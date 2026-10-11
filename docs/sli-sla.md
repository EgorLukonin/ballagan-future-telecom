# SLI/SLA — целевые показатели сервиса

Документ определяет метрики качества сервиса «University Materials API»,
целевые показатели (SLO) и соглашение об уровне обслуживания (SLA).

## 1. Термины

| Термин | Определение |
|---|---|
| **SLI** (Service Level Indicator) | Измеримый показатель качества сервиса, вычисляется по метрикам Prometheus |
| **SLO** (Service Level Objective) | Целевое значение SLI, которое сервис обязуется поддерживать (окно оценки — 30 дней) |
| **SLA** (Service Level Agreement) | Соглашение с потребителем: уровни, время реакции, действия при нарушении |
| **Error budget** | Допустимая «неудача» = 1 − SLO. Пока бюджет не исчерпан — можно рисковать (релизы); исчерпан — релизы замораживаются |

## 2. Источники метрик

- Сервис экспонирует метрики на `/metrics` через `prometheus-fastapi-instrumentator`
- Сбор: ServiceMonitor `materials-api` (namespace `default`), job `default/materials-api/http`
- Основные метрики: `http_requests_total` (лейблы `status`, `method`, `handler`),
  `http_request_duration_seconds_bucket` (гистограмма), `up`

## 3. SLI — индикаторы и формулы (окно 30 дней)

| SLI | Формула (PromQL) |
|---|---|
| **Доступность** — доля успешных (не-5xx) запросов | `1 - (sum(rate(http_requests_total{job=~"default/materials-api/.*",status=~"5.."}[30d])) / clamp_min(sum(rate(http_requests_total{job=~"default/materials-api/.*"}[30d])), 1))` |
| **Латентность p95 / p99** | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job=~"default/materials-api/.*"}[30d])) by (le))` (аналогично 0.99) |
| **Ошибки** — доля 5xx | `sum(rate(http_requests_total{job=~"default/materials-api/.*",status=~"5.."}[30d])) / clamp_min(sum(rate(http_requests_total{job=~"default/materials-api/.*"}[30d])), 1)` |
| **Аптайм** — доля времени с живыми экземплярами | `avg_over_time(up{job=~"default/materials-api/.*"}[30d])` |
| **Бизнес: успешные выдачи списка материалов** — доля 2xx от 2xx+5xx на `/api/v1/materials/list` | `sum(rate(http_requests_total{job=~"default/materials-api/.*",handler=~".*materials/list",status=~"2.."}[30d])) / clamp_min(sum(rate(http_requests_total{job=~"default/materials-api/.*",handler=~".*materials/list",status=~"2..|5.."}[30d])), 1)` |

Примечание: клиентские ошибки 4xx (некорректная ссылка, ошибки валидации)
исключаются из расчёта бизнес-SLI — это не дефект сервиса.

## 4. SLO — утверждённые целевые показатели

| Показатель | Целевое значение (SLO) | Окно оценки |
|---|---|---|
| Доступность | **≥ 99.5%** | 30 дней |
| Латентность | **p95 ≤ 500 мс**, p99 ≤ 1 с | 30 дней |
| Ошибки (5xx) | **< 1%** | 30 дней |
| Аптайм | **≥ 99.9%** | 30 дней |
| Успешные выдачи списка материалов | **≥ 99.9%** | 30 дней |

## 5. Error budget

Доступность 99.5% ⇒ error budget = 0.5% времени/запросов (≈ 3.6 часа простоя в месяц).

Пороги burn-rate (SRE multi-window):

| Режим | Окно | Порог | Смысл |
|---|---|---|---|
| Fast burn | 1 час | 14.4 × бюджет = **7.2% ошибок за час** | критично, бюджет сгорит за ~2 дня |
| Slow burn | 6 часов | 6 × бюджет = **3% ошибок за 6 часов** | бюджет сгорит за ~5 дней |

Реализовано алертами: `UniversityMaterialsAPIErrorBudgetBurnFast` (critical),
`UniversityMaterialsAPIErrorBudgetBurnSlow` (warning) — см. `k3s/monitoring/sli-rules.yaml`.

## 6. SLA — соглашение об уровне обслуживания

### 6.1 Уровни инцидентов

| Уровень | Определение | Время реакции | Время восстановления |
|---|---|---|---|
| **P1** | Полная недоступность API или исчерпание fast burn | 15 минут | 1 час |
| **P2** | Деградация: p95 > 500 мс, slow burn, доля 5xx > 1% | 30 минут | 4 часа |
| **P3** | Незначительные отклонения, предупреждающие алерты | в течение рабочего дня | 24 часа |

### 6.2 Обязательства сторон

- **Команда сервиса:** устраняет инциденты в сроки таблицы выше, публикует
  post-mortem по P1/P2, поддерживает мониторинг и алертинг (Prometheus + Alertmanager + Telegram).
- **Потребитель:** использует актуальную публичную ссылку папки Яндекс.Диска,
  повторяет запросы при 5xx (ретраи с backoff).

### 6.3 Действия при исчерпании error budget

1. Заморозка релизов/изменений канареечного веса до восстановления показателей
2. Приоритетная работа над надёжностью вместо фич
3. Разбор инцидента и корректировка SLO/процессов по итогам

## 7. Где смотреть

- **Grafana** → дашборд «University Materials API»: RPS, 5xx, p95, панель «Error budget remaining»
- **Prometheus UI**: recording-правила `sli:*` (группа `materials-api-sli`)
- **Alertmanager / Telegram**: burn-rate и health-алерты

## 8. Процесс пересмотра

SLO пересматриваются ежемесячно (или после каждого P1): если достижение целей
слишком лёгкое/трудное — значения корректируются командой и фиксируются в этом документе.
