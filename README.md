# Future Telecom — Materials Microservice & Cloud Infrastructure

## Описание проблемы

В современных распределенных телекоммуникационных платформах и учебных сервисах часто возникает задача динамической интеграции с внешними облачными хранилищами (публичными каталогами Яндекс Диска) для отдачи учебных материалов и документации. Ручное управление ссылками, отсутствие валидации входных данных, задержки при обновлении контента, а также отсутствие автоматизированной инфраструктуры, мониторинга и проверки безопасности приводят к невысокой надежности системы и сложностям при масштабировании.

## Цель работы

Создание отказоустойчивой, прозрачной и полностью автоматизированной платформы:

1. Разработка асинхронного REST API микросервиса на FastAPI для работы с публичными ресурсами Яндекс Диска, со строгой валидацией Pydantic и экспортом метрик.
2. Автоматическое развёртывание облачной инфраструктуры в OpenStack / Selectel через Terraform и конфигурация узла через Ansible.
3. Развёртывание и оркестрация Kubernetes-кластера (k3s) с Ingress-контроллером, Sealed Secrets, системой мониторинга Prometheus/Grafana и автоматизированным CI/CD пайплайном (GitHub Actions, Trivy).

## Состав команды

* **Валерий Михайлов (Backend Developer):**  
  - Роль: Разработка серверной логики и API сервиса.  
  - Навыки и задачи: Python 3.11+, FastAPI, Pydantic v2, httpx, pytest, uv. Разработка асинхронного REST API (materials-univ-api), написание юнит-тестов с моками, Pydantic-валидация, оптимизация работы с Яндекс Диск API и настройка линтинга.

* **Егор Луконин (Network engineer):**  
  - Роль: Специалист по сетевым технологиям.  
  - Навыки и задачи: Terraform, CI/CD, написание playbooks Ansible, разработка инфраструктуры проекта, настройка Ingress-контроллера, развертывание мониторинга (Grafana, Prometheus), настройка Sealed Secrets, работа с облаком (Selectel).

* **Алина Корниенко (Project manager):**  
  - Роль: Менеджер проекта.  
  - Навыки и задачи: Работа с таск-менеджерами, декомпозиция и трекинг задач, визуализация концептов и отчетность, создание презентаций для защиты и демонстрации результатов проекта, ведение учета выполнения задач и контроль сроков, продуктовая коммуникация.

* **Владислав Галеев (Data Scientist):**  
  - Роль: Аналитик данных.  
  - Навыки и задачи: Python 3.11+, pytest, numpy, jupyter, notebook, Git, matplotlib, qiskit, Ansible, CI/CD, Trivy, Linters (flake8, black), SLI/SLO/SLA. Настраивал Trivy, определял SLI/SLO/SLA метрики для мониторинга.

* **Георгий Винокуров (DevOps):**  
  - Роль: Специалист по разработке и эксплуатации.  
  - Навыки и задачи: Docker, k3s, Helm, Makefile, CI/CD. Создание Docker образа, Makefile, настройка k3s, написание Helm-chart.

## Архитектура / Схема

![Architecture](docs/architecture/architecture.svg)

*Поток запросов: Пользователь → Traefik Ingress Controller → FastAPI Microservice (materials-univ-api) → Yandex Disk Public API.  
Кластер k3s: содержит микросервис, Ingress, систему мониторинга (Prometheus / Grafana) и оператор Sealed Secrets.  
Автоматизация: инфраструктура поднимается через Terraform и настраивается с помощью Ansible Playbooks. CI/CD пайплайн на базе GitHub Actions запускает линтеры, тесты и сканирование безопасности.*

## Использованные инструменты

| Категория | Инструменты и версии |
|-----------|---------------------|
| **Backend & API** | Python 3.12, FastAPI, Pydantic v2, Uvicorn, httpx, uv |
| **Тестирование и качество** | pytest, pytest-asyncio, black, flake8, yamllint |
| **Infrastructure as Code (IaC)** | Terraform ≥ 1.6, OpenStack / Selectel Provider, Ansible (community.general) |
| **Оркестрация и контейнеризация** | Kubernetes (k3s v1.28+), Docker / Buildx, Helm, ingress-nginx |
| **CI/CD & Безопасность** | GitHub Actions, Trivy 0.75 (IaC + image scan), Sealed Secrets, kubeseal |
| **Мониторинг & Аналитика** | Prometheus, Grafana, Alertmanager (kube-prometheus-stack 92.3.0), kube-prometheus-stack |
| **Управление секретами** | Sealed Secrets (Bitnami), kubeseal |
| **Другое** | Make, ssh/scp, ctr (containerd) |

## Как запустить

### Быстрый старт

```bash
git clone https://github.com/EgorLukonin/ballagan-future-telecom
cd ballagan-future-telecom
make up
```

В конце вывода появятся URL API и Grafana.

---

### Предварительные требования (управляющая машина)

- Linux/macOS с `make`, `ssh`, `scp`
- Terraform ≥ 1.6, Ansible + коллекция `community.general` (`ansible-galaxy collection install community.general`)
- Docker (для `build-image`), Helm, kubectl (для ролей apps — выполняются на localhost)
- Переменные окружения для Terraform:
  - `TF_VAR_selectel_username`
  - `TF_VAR_selectel_password`
  - `TF_VAR_selectel_account`
  - `TF_VAR_project_id`
  - `TF_VAR_selectel_ip_address`

Проверка: `make prereqs`

---

### Подготовка Sealed Secrets (обязательно перед первым `make up`)

Подробная инструкция: **[docs/sealed-secrets-setup.md](docs/sealed-secrets-setup.md)**

Краткий чек-лист файлов, которые должны появиться в `k3s/sealed-secrets/`:

| Файл | Назначение |
|------|------------|
| `master-key.yaml` | Мастер-ключ контроллера Sealed Secrets (получить с кластера) |
| `monitoring-sealed-secret.yaml` | Пароль админа Grafana (запечатать через kubeseal) |
| `alertmanager-email-sealed-secret.yaml` | Конфиг Alertmanager для Email (Gmail SMTP, запечатать скриптом) |
| `materials-api-sealed-secret.yaml` | Уже в репо — секрет приложения (Яндекс.Диск) |

---

### Все команды make

Полный список: `make help` (цель по умолчанию).

| Цель | Что делает |
|---|---|
| `make help` | список всех команд с описаниями |
| `make up` | полное развёртывание: terraform → k3s → образы → приложения; в конце печатает URL API и Grafana |
| `make down` | terraform destroy + удаление локальных артефактов |
| `make prereqs` | проверка установленных инструментов (terraform, ansible, helm, kubectl, docker, ssh, scp) |
| `make inventory` | генерация `ansible/inventory.ini` из terraform output |
| `make ansible-infra` / `ansible-apps` | фазы ansible по отдельности (теги `infra` / `apps`) |
| `make tf-init` / `tf-plan` / `tf-apply` / `tf-destroy` | terraform по шагам |
| `make build-image` / `push-image` | сборка образа и доставка на ВМ (scp + `ctr images import`) |
| `make test` | unit-тесты pytest |
| `make lint` | black + flake8 + yamllint + ansible-lint (как в CI) |
| `make status` | terraform output + узлы и поды кластера |
| `make app-status` / `app-logs` | поды и логи приложения (primary/canary) |
| `make rollout` | перезапуск деплойментов приложения |
| `make verify` | сквозная проверка: `/health`, `/metrics` через ingress, узлы кластера |
| `make grafana` / `prometheus` / `alertmanager` | port-forward UI мониторинга на localhost |
| `make canary 50` | задать вес canary (%), по умолчанию 10 |
| `make clean` | удалить локальные артефакты без terraform destroy |

---

## Мониторинг и наблюдаемость

- В микросервис встроен Prometheus-экспортер метрик (`/metrics`).
- В кластере k3s развернут стек **kube-prometheus-stack** (Prometheus + Alertmanager + Grafana) версии `92.3.0`, ставится ролью `monitoring` на фазе `apps` (`make up`).
- Конфигурация в `k3s/monitoring/`:
  - `values.yaml` — урезано под ВМ 4 GB: Prometheus 1 реплика / retention 15d, отключены kubeEtcd/kubeControllerManager/kubeScheduler/kubeProxy
  - `servicemonitor.yaml` — сбор `/metrics` с primary/canary нашего API
  - `prometheusrule.yaml` — алерты: `UniversityMaterialsAPIDown` (critical), `UniversityMaterialsAPIHighErrorRate` (warning), burn-rate алерты для error budget
  - `grafana-dashboard-configmap.yaml` — дашборд «University Materials API» (RPS, 5xx, p95, up, error budget remaining)
  - `sli-rules.yaml` — recording-правила `sli:*` для SLI/SLO

### SLI / SLO (окно 15 дней)

| Показатель | SLO |
|---|---|
| Доступность (доля не-5xx) | ≥ 99.5% |
| Латентность | p95 ≤ 500 мс, p99 ≤ 1 с |
| Ошибки 5xx | < 1% |
| Аптайм | ≥ 99.9% |
| Успешные выдачи списка материалов | ≥ 99.9% |

Полный документ: [`docs/sli-sla.md`](docs/sli-sla.md).

### Доступ после развёртывания

| Что | Как открыть |
|---|---|
| Grafana | `http://<IP-сервера>/grafana`, логин `admin`, пароль из секрета |
| Prometheus UI | `kubectl --kubeconfig kubeconfig -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090` → http://localhost:9090 |
| Alertmanager UI | `kubectl --kubeconfig kubeconfig -n monitoring port-forward svc/kube-prometheus-stack-alertmanager 9093:9093` → http://localhost:9093 |
| Дашборд API | Grafana → Dashboards → «University Materials API» |

Проверка метрик: в Prometheus UI выполните `up{job=~"default/materials-api/.*"}` — должно вернуть экземпляры primary и canary.

### Алертинг на Email (Gmail)

Алерты из Prometheus маршрутизируются в Alertmanager и уходят на Email через Gmail SMTP. Конфиг хранится в запечатанном секрете `alertmanager-email-secret`.

Алерты:
- `UniversityMaterialsAPIDown` (critical) — экземпляр не отвечает более 2 минут
- `UniversityMaterialsAPIHighErrorRate` (warning) — доля 5xx выше 5% в течение 5 минут
- Burn-rate алерты: `UniversityMaterialsAPIErrorBudgetBurnFast` (critical), `UniversityMaterialsAPIErrorBudgetBurnSlow` (warning)

Логика: группировка по `alertname`, `group_interval 5m`, повтор `repeat_interval 4h`; ингибирование алертов приложения пока нода недоступна.

Настройка Gmail App Password:
1. Включите 2FA в Google Account
2. Security → App passwords → "Mail" → сгенерируйте пароль
3. Используйте скрипт: `python scripts/seal_alertmanager_email.py --smtp-user <EMAIL> --smtp-password <APP_PASSWORD> --from <EMAIL> --to <EMAIL>`

---

## Безопасность

- **Trivy IaC scan** — сканирование конфигураций (terraform, ansible, helm, Dockerfile) на misconfig и секреты; падение на HIGH/CRITICAL; результаты в **GitHub → Security → Code scanning**.
- **Trivy image scan** — сканирование Docker-образа после сборки; падение на HIGH/CRITICAL; результаты в **Security → Code scanning**.
- **Sealed Secrets** — все конфиденциальные данные (пароль Grafana, Gmail App Password для Alertmanager, секреты приложения) хранятся в git только в запечатанном виде. Мастер-ключ контроллера не в git.
- **Нет внешнего реестра** — образ доставляется на ВМ через scp и импортируется в containerd (`ctr images import`).
- **UFW на VM** — роль `base` настраивает firewall.
- **`.trivyignore`** — исключения для ложных срабатываний Trivy.
- **GitHub Actions secrets** — `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` для пуша образа.

---

## Troubleshooting

### Инфраструктура (Terraform / OpenStack / Selectel)

| Проблема | Причина | Решение |
|---|---|---|
| `terraform apply` падает с `Error creating server` | Квоты исчерпаны, нехватка ресурсов в проекте Selectel | Проверить квоты в панели Selectel → Project → Quotas. Увеличить лимиты на vCPU, RAM, Volumes, Floating IPs. |
| `Error: Error applying plan: 1 error occurred: * Provider produced inconsistent result` | Кеш Terraform устарел | `make tf-init` (переинициализация провайдеров), затем `make tf-plan` и `make tf-apply`. |
| VM не получает Floating IP | Порт не привязан к сети `ext-net` или нет свободных IP | Проверить в Terraform: `network { name = "ext-net" }` у instance. Освободить/выделить Floating IP в панели Selectel. |
| `ssh: connect to host ... port 22: Connection refused` | VM ещё не загрузилась, cloud-init не завершился, UFW блокирует | Подождать 2–3 минуты после создания VM. Проверить `make status` — узел должен быть `Ready`. UFW настраивается ролью `base` Ansible. |

### Ansible / Конфигурация узла

| Проблема | Причина | Решение |
|---|---|---|
| `make inventory` не создаёт `ansible/inventory.ini` | Terraform output пустой (ресурсы не созданы) | Выполнить `make tf-apply` до конца. Проверить `terraform output -json`. |
| Ansible: `Failed to connect to the host via ssh` | Неправильный `ansible_user` или ключ SSH | Убедиться, что в `ansible.cfg` или inventory указан верный пользователь (обычно `ubuntu` для Ubuntu Cloud Images). Ключ должен быть в `~/.ssh/id_rsa` или задан `ansible_ssh_private_key_file`. |
| Роль `k3s` падает на `k3s service failed to start` | Недостаточно памяти/CPU на VM (минимум 4 GB RAM, 2 vCPU) | Использовать флейвор с ≥4 GB RAM. Проверить `journalctl -u k3s -f` на узле. |
| `ansible-apps` падает на `Helm release failed` | kubeconfig неверный, кластер не Ready | Проверить `make status` — все узлы `Ready`. `export KUBECONFIG=$(pwd)/kubeconfig`. Перезапустить `make ansible-apps`. |

### Kubernetes (k3s) / Приложение

| Проблема | Причина | Решение |
|---|---|---|
| Поды `materials-api-*` в `ImagePullBackOff` / `ErrImagePull` | Образ не доставлен на VM или не импортирован в containerd | Выполнить `make build-image && make push-image`. Проверить на VM: `ctr -n k8s.io images ls | grep materials-api`. |
| Поды в `CrashLoopBackOff` | Ошибка запуска приложения (конфиг, секреты, зависимости) | `make app-logs` — посмотреть логи. Частые причины: неверные Sealed Secrets, недоступен Yandex Disk API, ошибка миграций. |
| `Service materials-api` не имеет Endpoints | Селектор Service не совпадает с labels подов | Проверить `kubectl -n default get svc materials-api -o yaml` и `kubectl -n default get pods -l app=materials-api --show-labels`. |
| Ingress возвращает 502 / 404 | Traefik/ingress-nginx не видит Service, неверный `host` в Ingress | Проверить `kubectl -n default get ingress`. Host в Ingress должен совпадать с DNS/IP. `make verify` проверяет `/health` через ingress. |

### Sealed Secrets

| Проблема | Причина | Решение |
|---|---|---|
| `kubeseal: error: secrets "xxx" not found` | Секрет не создан в кластере перед sealing | Создать обычный Secret в целевом namespace, затем запечатать: `kubectl create secret generic ... --dry-run=client -o yaml | kubeseal ...` |
| Поды не стартуют: `InvalidSecret: secret data must be base64 encoded` | Неправильный формат при создании SealedSecret | Значения в `stringData` (не `data`) при создании исходного Secret. `kubeseal` сам заэнкодит. |
| После переустановки кластера Sealed Secrets не расшифровываются | Мастер-ключ контроллера изменился (не сохранён) | Всегда сохранять `master-key.yaml` из предыдущего кластера (`kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > master-key.yaml`). При переустановке кластера восстанавливать его до установки приложений. |

### Мониторинг (Prometheus / Grafana / Alertmanager)

| Проблема | Причина | Решение |
|---|---|---|
| Grafana: "Invalid username or password" | Пароль админа не совпадает с запечатанным секретом | Проверить `monitoring-sealed-secret.yaml` — пароль должен быть запечатан для namespace `monitoring`, key `admin-password`. Пересоздать секрет и перезапустить `grafana` под. |
| Prometheus не видит targets `materials-api` | ServiceMonitor не создан / неверный namespace / label mismatch | Проверить `kubectl -n monitoring get servicemonitor`. `matchLabels` в ServiceMonitor должен совпадать с labels Service (`app: materials-api`). |
| Алерты не уходят на Email | Неверные SMTP настройки в `alertmanager-email-sealed-secret.yaml` | Проверить секрет: `kubectl -n monitoring get secret alertmanager-email-secret -o yaml`. SMTP user/password в base64. Логи Alertmanager: `kubectl -n monitoring logs -l app=alertmanager`. |
| Дашборд "University Materials API" пустой | Метрики не собираются / неверные recording rules | Проверить в Prometheus UI: `up{job=~"default/materials-api/.*"}`. Должно вернуть 1 для primary и canary. Проверить `sli-rules.yaml` — recording rules должны создавать `sli:*` метрики. |

### CI/CD (GitHub Actions)

| Проблема | Причина | Решение |
|---|---|---|
| Job `trivy-iac` / `trivy-image` падает на HIGH/CRITICAL | Найдены уязвимости или misconfig в коде/образе | Открыть GitHub → Security → Code scanning → просмотреть детали. Исправить Dockerfile, Terraform, Helm values. Ложные срабатывания добавить в `.trivyignore`. |
| `docker/build-push-action` падает: `denied: requested access to the resource is denied` | Неверные `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` в GitHub Secrets | Проверить Secrets в репозитории. Токен должен иметь права на push. |
| Пайплайн не запускается при push в main | Workflow файл не в `.github/workflows/` или неверный `on:` trigger | Проверить `.github/workflows/ci.yml` — `on: push: branches: [main]`. Файл должен быть в корне репозитория. |

### Сеть / DNS / Внешний доступ

| Проблема | Причина | Решение |
|---|---|---|
| API недоступен по `http://<IP>/api/...` | Ingress не настроен, неверный host, Traefik не слушает 80/443 | Проверить `kubectl -n kube-system get svc traefik` (или ingress-nginx). Порты 80/443 должны быть открыты в Security Groups Selectel + UFW на VM. |
| `curl` к API возвращает 504 Gateway Timeout | Апстрим (FastAPI) не отвечает за 60с (timeout Traefik) | Увеличить `timeout` в Ingress/Traefik Middleware. Проверить производительность API — возможно, Yandex Disk API тормозит. |

### Полезные команды диагностики

```bash
# Общее состояние
make status              # terraform output + kubectl get nodes,pods -A
make verify              # сквозная проверка /health, /metrics через ingress

# Логи приложения
make app-logs            # логи primary/canary подов
kubectl -n default logs -l app=materials-api -f --tail=100

# Логи инфраструктуры
kubectl -n kube-system logs -l app=traefik -f
kubectl -n monitoring logs -l app=prometheus -f
kubectl -n monitoring logs -l app=alertmanager -f

# Sealed Secrets
kubectl get sealedsecrets -A
kubectl -n default get secret materials-api-secret -o yaml

# Метрики в Prometheus (через port-forward)
make prometheus          # затем http://localhost:9090
# Запросы:
# up{job=~"default/materials-api/.*"}
# rate(http_requests_total{job="materials-api"}[5m])
# histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="materials-api"}[5m]))

# Перезапуск приложения
make rollout             # rolling restart deployments
```

---

## Лицензия

[MIT License](LICENSE)