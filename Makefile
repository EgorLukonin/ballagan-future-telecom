.DEFAULT_GOAL := help

.PHONY: help up down clean prereqs inventory ansible-infra ansible-apps \
        tf-init tf-plan tf-apply tf-destroy build-image push-image \
        test lint status app-status app-logs rollout verify \
        grafana prometheus alertmanager canary

help: ## Список доступных команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: tf-init tf-apply ansible-infra push-image ansible-apps ## Полное развёртывание: terraform -> k3s -> образы -> приложения
	@echo ""
	@echo "Готово! API:      http://$$(cd terraform && terraform output -raw server_ip)/"
	@echo "       Grafana:   http://$$(cd terraform && terraform output -raw server_ip)/grafana"

down: tf-destroy clean ## Удалить инфраструктуру (terraform destroy) и локальные артефакты

clean: ## Удалить локальные артефакты (без terraform destroy)
	rm -f kubeconfig ballagan-images.tar ansible/inventory.ini
	rm -f terraform/hosts.ini

prereqs: ## Проверить, что все нужные инструменты установлены
	@fail=0; \
	for c in terraform ansible-playbook helm kubectl docker ssh scp; do \
		if command -v $$c >/dev/null 2>&1; then \
			echo "  ok   $$c"; \
		else \
			echo "  MISS $$c"; fail=1; \
		fi; \
	done; \
	if [ $$fail -ne 0 ]; then echo "Установите недостающие инструменты (см. README)"; exit 1; fi

inventory: ## Сгенерировать ansible/inventory.ini из terraform output
	@if [ ! -f ansible/inventory.ini ]; then sleep 20; fi
	@VM_IP=$$(cd terraform && terraform output -raw server_ip); \
	printf "[webservers]\n$$VM_IP ansible_user=root ansible_ssh_private_key_file=../terraform/id_rsa\n" > ansible/inventory.ini

ansible-infra: inventory ## Настройка ОС и установка k3s (роли base, k3s)
	cd ansible && ansible-playbook -i inventory.ini playbooks/site.yml --tags infra

ansible-apps: inventory ## Установка приложений (sealed-secrets, ingress, мониторинг)
	cd ansible && ansible-playbook -i inventory.ini playbooks/site.yml --tags apps

tf-init: ## terraform init
	@if [ ! -f ~/.terraformrc ]; then \
		printf 'provider_installation {\n  network_mirror {\n    url = "https://terraform-mirror.yandexcloud.net/"\n    include = ["registry.terraform.io/*/*"]\n  }\n  direct {\n    exclude = ["registry.terraform.io/*/*"]\n  }\n}\n' > ~/.terraformrc; \
	fi
	cd terraform && terraform init

tf-plan: ## terraform plan (без применения)
	cd terraform && terraform plan

tf-apply: ## terraform apply -auto-approve
	cd terraform && terraform apply -auto-approve

tf-destroy: ## terraform destroy -auto-approve
	cd terraform && terraform destroy -auto-approve

build-image: ## Собрать Docker-образ (latest + canary) и упаковать в tar
	docker build -t docker.io/guber45/ballagan-telecom-api:latest .
	docker tag docker.io/guber45/ballagan-telecom-api:latest docker.io/guber45/ballagan-telecom-api:canary
	docker save docker.io/guber45/ballagan-telecom-api:latest docker.io/guber45/ballagan-telecom-api:canary -o ballagan-images.tar

push-image: build-image ## Доставить образ на сервер и импортировать в containerd
	@VM_IP=$$(cd terraform && terraform output -raw server_ip); \
	scp -o StrictHostKeyChecking=no -i terraform/id_rsa ballagan-images.tar root@$$VM_IP:/tmp/; \
	ssh -o StrictHostKeyChecking=no -i terraform/id_rsa root@$$VM_IP "ctr -n k8s.io images import /tmp/ballagan-images.tar || true; rm -f /tmp/ballagan-images.tar"; \
	rm -f ballagan-images.tar

test: ## Запустить unit-тесты (pytest)
	python -m pytest -q

lint: ## Проверить код: black, flake8, yamllint, ansible-lint (как в CI)
	black --check src tests
	flake8 src tests
	yamllint ansible k3s .github
	cd ansible && ANSIBLE_CONFIG=ansible.cfg ansible-lint playbooks roles

status: ## Состояние инфраструктуры и кластера
	@cd terraform && terraform output
	@KUBECONFIG=kubeconfig kubectl get nodes
	@KUBECONFIG=kubeconfig kubectl get pods -A

app-status: ## Поды приложения (primary/canary)
	KUBECONFIG=kubeconfig kubectl get pods -n default -l app=production-api

app-logs: ## Последние логи подов приложения
	KUBECONFIG=kubeconfig kubectl logs -n default -l app=production-api --prefix --tail=50

rollout: ## Перезапустить деплойменты приложения
	KUBECONFIG=kubeconfig kubectl rollout restart -n default deployment -l app=production-api

verify: ## Сквозная проверка: /health, /metrics через ingress и узлы кластера
	@set -e; \
	VM_IP=$$(cd terraform && terraform output -raw server_ip); \
	echo "== /health =="; \
	curl -fsS "http://$$VM_IP/health" && echo; \
	echo "== /metrics (первые строки) =="; \
	curl -fsS "http://$$VM_IP/metrics" | head -5; \
	echo "== узлы кластера =="; \
	KUBECONFIG=kubeconfig kubectl get nodes

grafana: ## Port-forward Grafana (остановка: Ctrl+C)
	@echo "Grafana: http://localhost:3000/grafana/"
	KUBECONFIG=kubeconfig kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80

prometheus: ## Port-forward Prometheus (остановка: Ctrl+C)
	@echo "Prometheus: http://localhost:9090"
	KUBECONFIG=kubeconfig kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090

alertmanager: ## Port-forward Alertmanager (остановка: Ctrl+C)
	@echo "Alertmanager: http://localhost:9093"
	KUBECONFIG=kubeconfig kubectl -n monitoring port-forward svc/kube-prometheus-stack-alertmanager 9093:9093

canary: ## Задать вес canary, например: make canary 50 (по умолчанию 10)
	@WEIGHT=$(filter-out $@,$(MAKECMDGOALS)); \
	[ -n "$$WEIGHT" ] || WEIGHT=10; \
	KUBECONFIG=kubeconfig helm upgrade materials-api k3s/helm-charts/materials-univ-api \
		--namespace default --reuse-values --set canary.weight=$$WEIGHT; \
	echo "Вес canary: $$WEIGHT%"

%:
	@:
