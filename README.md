# ballagan-future-telecom

DevOps-кейс «Облачный DevOps-конвейер: от репозитория до production-Kubernetes за 3 команды».

## Запуск (make up / make down)

Полное развёртывание одной командой:

```bash
git clone ...
cd ballagan-future-telecom
make up
```

Что делает `make up` (последовательно):

1. **Terraform** — `terraform init` + `apply`: заказ ВМ в Selectel, сеть, плавающий IP, генерация ssh-ключа и inventory
2. **ansible-infra** — роли `base` (пакеты, ufw, swap off) и `k3s` (кластер k3s без Traefik, kubeconfig выгружается в `./kubeconfig`)
3. **push-image** — локальная сборка одного образа (`ballagan-telecom-api:latest` + тег `:canary`), доставка на ВМ через scp и импорт в containerd (`ctr images import`) — внешний реестр не нужен
4. **ansible-apps** — роли `sealed_secrets` (контроллер + секрет Яндекс.Диска), `ingress` (ingress-nginx + helm-чарт приложения primary/canary 90/10) и `monitoring` (kube-prometheus-stack: Prometheus, Grafana, Alertmanager + ServiceMonitor, алерт-правило, дашборд)

Остановить и удалить всё: `make down` (terraform destroy + очистка артефактов).

### Prerequisites (управляющая машина)

- Linux/macOS с `make`, `ssh`, `scp`
- Terraform ≥ 1.6, Ansible + коллекция `community.general` (`ansible-galaxy collection install community.general`)
- Docker (для `build-image`), Helm, kubectl (для ролей apps — выполняются на localhost)
- Переменные окружения для Terraform: `TF_VAR_selectel_username`, `TF_VAR_selectel_password`, `TF_VAR_selectel_account`, `TF_VAR_project_id`

### Мастер-ключ Sealed Secrets

Роль `sealed_secrets` требует мастер-ключ контроллера — это секрет, он **не хранится в git** (путь в `.gitignore`). Перед первым `make up`:

1. Получите ключ с кластера, где он уже живёт:
   ```bash
   kubectl get secret -n kube-system sealed-secrets-key -o yaml > k3s/sealed-secrets/master-key.yaml
   ```
2. Файл должен лежать по пути `k3s/sealed-secrets/master-key.yaml` (или укажите свой: `-e sealed_secrets_master_key=/path/to/master-key.yaml`)

Без этого файла роль упадёт с понятной ошибкой до установки контроллера. Если ключа нет вообще — контроллер сгенерирует новый, но тогда `materials-api-sealed-secret.yaml` придётся перезапечатывать.

## Что сделать вручную (чек-лист для запуска CI)

### 1. Настроить секреты в GitHub

Откройте репозиторий на GitHub → **Settings → Secrets and variables → Actions → New repository secret**. Добавьте два секрета:

| Имя секрета | Что вставить |
|---|---|
| `DOCKERHUB_USERNAME` | Логин аккаунта Docker Hub (организации или личный), от которого будет пуш образа |
| `DOCKERHUB_TOKEN` | Access Token. Создаётся на Docker Hub: **Account Settings → Security → New Access Token** (права Read & Write). Пароль от аккаунта вставлять нельзя — только токен |

Без этих секретов джоба `docker` будет падать на шаге `Login to Docker Hub`.

### 2. Заменить имя образа

В файле `.github/workflows/ci.yml`, строка 14, стоит заглушка:

```yaml
IMAGE_NAME: ORGANIZATION/ballagan-telecom-api
```

Замените `ORGANIZATION` на реальное имя организации/аккаунта Docker Hub, например:

```yaml
IMAGE_NAME: ballagan-team/ballagan-telecom-api
```

Имя должно совпадать с тем аккаунтом, чей токен вы положили в секреты. Если организация на Docker Hub не создана — создайте её: **Docker Hub → Organizations → Create organization** (или используйте личный логин).

### 3. Локальная проверка перед пушем (опционально)

Те же проверки, что гоняет CI, можно запустить у себя:

```bash
python -m venv .venv
.venv\Scripts\pip install .
.venv\Scripts\pip install black flake8 yamllint
.venv\Scripts\python -m pytest -v          # тесты
.venv\Scripts\black --check src tests      # форматирование
.venv\Scripts\flake8 src tests             # линт Python
.venv\Scripts\yamllint ansible k3s .github # линт YAML
```

## Что делает CI

Пайплайн (`.github/workflows/ci.yml`) срабатывает на push в `main` и на каждый pull request:

1. **Lint** — `black --check`, `flake8`, `yamllint` (ansible, k3s, workflow), `ansible-lint`
2. **Trivy IaC scan** — сканирование конфигураций (terraform, ansible, helm, Dockerfile) на misconfig и секреты; падение на HIGH/CRITICAL; результаты в **GitHub → Security → Code scanning**
3. **Tests** — установка проекта (`pip install .`) и `pytest -v`
4. **Build, scan and push** (только после успеха 1 и 3) — сборка образа через buildx, экспорт в tar-архив и пуш в Docker Hub (только из `main`), затем сканирование образа **Trivy** по tar-архиву (пайплайн падает при HIGH/CRITICAL); результаты в **Security → Code scanning**

Если config-скан Trivy падает на неактуальной находке — заведите исключение в файле `.trivyignore` в корне репо (формат: id находки построчно).

## Мониторинг

Стек: **kube-prometheus-stack** (Prometheus + Alertmanager + Grafana) ставится ролью `monitoring` на фазе `apps` (`make up`), пин версии `92.3.0`. Конфигурация — `k3s/monitoring/`:

- `values.yaml` — урезано под ВМ 4 GB: Prometheus 1 реплика / retention 15d, отключены kubeEtcd/kubeControllerManager/kubeScheduler/kubeProxy
- `servicemonitor.yaml` — сбор `/metrics` с primary/canary нашего API
- `prometheusrule.yaml` — алерт `UniversityMaterialsAPIDown` (падение экземпляра)
- `grafana-dashboard-configmap.yaml` — дашборд «University Materials API» (RPS, 5xx, p95, up)

### Перед первым `make up` — запечатать пароль Grafana (вручную, один раз)

Секрет хранится в git только запечатанным (Sealed Secrets):

```bash
# 1. Установите kubeseal
#    Linux:   wget https://github.com/bitnami-labs/sealed-secrets/releases/latest/download/kubeseal-$(uname -s | tr 'A-Z' 'a-z')-amd64.tar.gz ...
#    macOS:   brew install kubeseal

# 2. Извлеките сертификат из вашего мастер-ключа
python3 - <<'EOF'
import base64, yaml
d = yaml.safe_load(open("k3s/sealed-secrets/master-key.yaml"))
print(base64.b64decode(d["items"][0]["data"]["tls.crt"]).decode())
EOF
#    > cert.pem

# 3. Создайте plaintext-секрет (в git не класть!)
cat > monitoring-secret-plaintext.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: monitoring-secrets
  namespace: monitoring
type: Opaque
stringData:
  admin-user: admin
  admin-password: ВАШ_ПАРОЛЬ
EOF

# 4. Запечатайте и уберите plaintext
kubeseal --cert cert.pem --format yaml < monitoring-secret-plaintext.yaml > k3s/sealed-secrets/monitoring-sealed-secret.yaml
rm -f monitoring-secret-plaintext.yaml cert.pem
```

Без файла `k3s/sealed-secrets/monitoring-sealed-secret.yaml` роль `monitoring` остановится с подсказкой.

### Доступ после развёртывания

| Что | Как открыть |
|---|---|
| Grafana | `http://<IP-сервера>/grafana`, логин `admin`, пароль из секрета |
| Prometheus UI | `kubectl --kubeconfig kubeconfig -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090` → http://localhost:9090 |
| Alertmanager UI | `kubectl --kubeconfig kubeconfig -n monitoring port-forward svc/kube-prometheus-stack-alertmanager 9093:9093` → http://localhost:9093 |
| Дашборд API | Grafana → Dashboards → «University Materials API» |

Проверка метрик: в Prometheus UI выполните `up{job=~"default/materials-api/.*"}` — должно вернуть экземпляры primary и canary.

## Что осталось по кейсу (вне этого шага)

- Живой прогон `make up` на арендованной ВМ (terraform + ansible + k3s «с нуля»)
- Алертинг: приёмник Telegram в Alertmanager (следующий шаг)
- Заполнить README по шаблону ForAgent.md (архитектура, SLI/SLA, команда)
- Видео-демо до 5 минут
