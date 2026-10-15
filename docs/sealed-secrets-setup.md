# Подготовка Sealed Secrets перед первым запуском

Для работы кластера необходимы заранее запечатанные секреты. Они **не хранятся в git в открытом виде** (пути в `.gitignore`). Перед первым `make up` выполните шаги ниже один раз.

---

## 1. Мастер-ключ Sealed Secrets контроллера

Роль `sealed_secrets` требует мастер-ключ контроллера — это секрет, он **не хранится в git**.

### Получите ключ с существующего кластера (если есть):

```bash
kubectl get secret -n kube-system sealed-secrets-key -o yaml > k3s/sealed-secrets/master-key.yaml
```

Файл должен лежать по пути `k3s/sealed-secrets/master-key.yaml` (или укажите свой: `-e sealed_secrets_master_key=/path/to/master-key.yaml`).

> **Важно:** Без этого файла роль упадёт с понятной ошибкой до установки контроллера. Если ключа нет вообще — контроллер сгенерирует новый, но тогда `materials-api-sealed-secret.yaml` придётся перезапечатывать.

---

## 2. Извлечение сертификата для kubeseal

Для запечатывания секретов нужен публичный сертификат из мастер-ключа:

```bash
# Linux/macOS
python3 - <<'EOF'
import base64, yaml
d = yaml.safe_load(open("k3s/sealed-secrets/master-key.yaml"))
print(base64.b64decode(d["items"][0]["data"]["tls.crt"]).decode())
EOF
# > cert.pem
```

Сохраните вывод в `cert.pem` (временный файл, не коммитить).

---

## 3. Секрет для мониторинга (Grafana admin password)

Секрет хранится в git только запечатанным.

### Plaintext (не класть в git!):

```bash
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
```

### Запечатать:

```bash
kubeseal --cert cert.pem --format yaml < monitoring-secret-plaintext.yaml > k3s/sealed-secrets/monitoring-sealed-secret.yaml
rm -f monitoring-secret-plaintext.yaml cert.pem
```

Без файла `k3s/sealed-secrets/monitoring-sealed-secret.yaml` роль `monitoring` остановится с подсказкой.

---

## 4. Конфиг Alertmanager для Telegram-бота

Алерты уходят в Telegram. Конфиг Alertmanager (с токеном бота) хранится в git только запечатанным — секрет `alertmanager-telegram-secret` в namespace `monitoring`.

### Plaintext (не класть в git!):

```bash
cat > alertmanager-telegram-plaintext.yaml <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-telegram-secret
  namespace: monitoring
type: Opaque
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m
    route:
      receiver: telegram
      group_by: [alertname]
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
    receivers:
      - name: telegram
        telegram_configs:
          - bot_token: "ВАШ_ТОКЕН_БОТА"
            chat_id: ВАШ_CHAT_ID
            parse_mode: HTML
    inhibit_rules:
      - source_matchers:
          - alertname =~ "KubeNodeUnreachable|KubeNodeNotReady|KubeletDown"
        target_matchers:
          - alertname =~ "UniversityMaterialsAPI.*"
EOF
```

### Запечатать:

```bash
# Снова извлеките cert.pem из мастер-ключа (см. пункт 2)
kubeseal --cert cert.pem --format yaml < alertmanager-telegram-plaintext.yaml > k3s/sealed-secrets/alertmanager-telegram-sealed-secret.yaml
rm -f alertmanager-telegram-plaintext.yaml cert.pem
```

Без файла `k3s/sealed-secrets/alertmanager-telegram-sealed-secret.yaml` роль `monitoring` остановится с подсказкой.

---

## 5. Проверка после развёртывания

```bash
# 1. Секрет расшифровался
kubectl --kubeconfig kubeconfig -n monitoring get secret alertmanager-telegram-secret

# 2. Алертменеджер получил конфиг
kubectl --kubeconfig kubeconfig -n monitoring port-forward svc/kube-prometheus-stack-alertmanager 9093:9093
# Откройте http://localhost:9093 → Alerts

# 3. Тест алерта: остановите API на 2+ минуты
kubectl --kubeconfig kubeconfig -n default scale deployment materials-api-primary --replicas=0
# Через ~2 минуты алерт станет firing, уйдёт в Telegram
# Вернуть: kubectl --kubeconfig kubeconfig -n default scale deployment materials-api-primary --replicas=1
```

---

## Итоговый чек-лист файлов в `k3s/sealed-secrets/`

| Файл | Назначение |
|------|------------|
| `master-key.yaml` | Мастер-ключ контроллера Sealed Secrets (получен с кластера) |
| `monitoring-sealed-secret.yaml` | Пароль админа Grafana |
| `alertmanager-telegram-sealed-secret.yaml` | Конфиг Alertmanager с токеном Telegram-бота |
| `materials-api-sealed-secret.yaml` | Уже в репо — секрет приложения (Яндекс.Диск) |

Все `*plaintext*.yaml` и `cert.pem` — **только локально, в git не коммитить**.