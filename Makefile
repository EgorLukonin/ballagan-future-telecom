.PHONY: up down inventory tf-init tf-plan tf-apply tf-destroy ansible-infra ansible-apps build-image push-image

up: tf-init tf-apply ansible-infra push-image ansible-apps

down: tf-destroy
	rm -f kubeconfig
	rm -f ballagan-images.tar
	rm -f ansible/inventory.ini
	rm -f terraform/id_rsa terraform/id_rsa.pub
	rm -f terraform/hosts.ini

inventory:
	@sleep 15
	@VM_IP=$$(cd terraform && terraform output -raw server_ip); \
	printf "[webservers]\n$$VM_IP ansible_user=root ansible_ssh_private_key_file=../terraform/id_rsa\n" > ansible/inventory.ini

ansible-infra: inventory
	cd ansible && ansible-playbook -i inventory.ini playbooks/site.yml --tags infra

ansible-apps: inventory
	cd ansible && ansible-playbook -i inventory.ini playbooks/site.yml --tags apps

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan

tf-apply:
	cd terraform && terraform apply -auto-approve

tf-destroy:
	cd terraform && terraform destroy -auto-approve

build-image:
	docker build -t ballagan-telecom-api:latest .
	docker tag ballagan-telecom-api:latest ballagan-telecom-api:canary
	docker save ballagan-telecom-api:latest ballagan-telecom-api:canary -o ballagan-images.tar

push-image: build-image
	@VM_IP=$$(cd terraform && terraform output -raw server_ip); \
	scp -o StrictHostKeyChecking=no -i terraform/id_rsa ballagan-images.tar root@$$VM_IP:/tmp/; \
	ssh -o StrictHostKeyChecking=no -i terraform/id_rsa root@$$VM_IP "ctr -n k8s.io images import /tmp/ballagan-images.tar || true; rm -f /tmp/ballagan-images.tar"; \
	rm -f ballagan-images.tar
