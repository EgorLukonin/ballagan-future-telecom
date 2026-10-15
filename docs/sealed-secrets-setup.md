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

## 4. Конфиг Alertmanager для Email (Gmail)

Алерты уходят на Email через Gmail SMTP. Конфиг Alertmanager хранится в git только запечатанным — секрет `alertmanager-email-secret` в namespace `monitoring`.

### Генерация и запечатывание скриптом:

```bash
python scripts/seal_alertmanager_email.py \
  --smtp-user "your-email@gmail.com" \
  --smtp-password "xxxx xxxx xxxx xxxx" \
  --from "your-email@gmail.com" \
  --to "alerts@example.com"
```

> **Важно:** Для Gmail нужен App Password (не обычный пароль):
> 1. Включите 2FA в Google Account
> 2. Security → App passwords → "Mail" → сгенерируйте 16-символьный пароль
> 3. Используйте его как `--smtp-password` (пробелы можно оставить или убрать)

Скрипт сам извлечёт сертификат из `master-key.yaml`, запечатает конфиг и запишет в `k3s/sealed-secrets/alertmanager-email-sealed-secret.yaml`.

### Ручной вариант (если kubeseal установлен локально):

```bash
# 1. Извлеките cert.pem из master-key.yaml (см. пункт 2)

# 2. Создайте plaintext конфиг:
cat > alertmanager-email-plaintext.yaml <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-email-secret
  namespace: monitoring
type: Opaque
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m
      smtp_smarthost: 'smtp.gmail.com:587'
      smtp_from: 'your-email@gmail.com'
      smtp_auth_username: 'your-email@gmail.com'
      smtp_auth_password: 'xxxx xxxx xxxx xxxx'
      smtp_require_tls: true
    route:
      receiver: email
      group_by: [alertname]
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
    receivers:
      - name: email
        email_configs:
          - to: 'alerts@example.com'
            send_resolved: true
    inhibit_rules:
      - source_matchers:
          - alertname =~ "KubeNodeUnreachable|KubeNodeNotReady|KubeletDown"
        target_matchers:
          - alertname =~ "UniversityMaterialsAPI.*"
EOF

# 3. Запечатать:
kubeseal --cert cert.pem --format yaml < alertmanager-email-plaintext.yaml > k3s/sealed-secrets/alertmanager-email-sealed-secret.yaml
rm -f alertmanager-email-plaintext.yaml cert.pem
```

Без файла `k3s/sealed-secrets/alertmanager-email-sealed-secret.yaml` роль `monitoring` остановится с подсказкой.

---

## 5. Проверка после развёртывания

```bash
# 1. Секрет расшифровался
kubectl --kubeconfig kubeconfig -n monitoring get secret alertmanager-email-secret

# 2. Алертменеджер получил конфиг
kubectl --kubeconfig kubeconfig -n monitoring port-forward svc/kube-prometheus-stack-alertmanager 9093:9093
# Откройте http://localhost:9093 → Alerts → проверьте receiver "email"

# 3. Тест алерта: остановите API на 2+ минуты
kubectl --kubeconfig kubeconfig -n default scale deployment materials-api-primary --replicas=0
# Через ~2 минуты алерт станет firing, уйдёт на Email
# Вернуть: kubectl --kubeconfig kubeconfig -n default scale deployment materials-api-primary --replicas=1
```

---

## Итоговый чек-лист файлов в `k3s/sealed-secrets/`

| Файл | Назначение |
|------|------------|
| `master-key.yaml` | Мастер-ключ контроллера Sealed Secrets (получен с кластера) |
| `monitoring-sealed-secret.yaml` | Пароль админа Grafana |
| `alertmanager-email-sealed-secret.yaml` | Конфиг Alertmanager для Email (Gmail SMTP) |
| `materials-api-sealed-secret.yaml` | Уже в репо — секрет приложения (Яндекс.Диск) |

Все `*plaintext*.yaml` и `cert.pem` — **только локально, в git не коммитить**.