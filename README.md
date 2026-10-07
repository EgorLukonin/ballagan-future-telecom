# ballagan-future-telecom

DevOps-кейс «Облачный DevOps-конвейер: от репозитория до production-Kubernetes за 3 команды».

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
2. **Tests** — установка проекта (`pip install .`) и `pytest -v`
3. **Build, scan and push** (только после успеха 1–2) — сборка образа через buildx, пуш в Docker Hub только из `main`, затем сканирование уязвимостей **Trivy** (пайплайн падает при находках HIGH/CRITICAL)

## Что осталось по кейсу (вне этого шага)

- Живой прогон `make up` на арендованной ВМ (terraform + ansible + k3s «с нуля»)
- Helm-чарты стабильной и canary-версий, Sealed Secrets
- Мониторинг: Prometheus + Grafana + Alertmanager, алерты в Telegram
- Заполнить README по шаблону ForAgent.md (архитектура, SLI/SLA, команда)
- Видео-демо до 5 минут
