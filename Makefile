.PHONY: up tf-init tf-plan tf-apply tf-destroy ansible build-image push-image

up: tf-init tf-apply ansible push-image

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan

tf-apply:
	cd terraform && terraform apply -auto-approve

ansible:
	@sleep 15
	@VM_IP=$$(cd terraform && terraform output -raw server_ip); \
	printf "[webservers]\n$$VM_IP ansible_user=root ansible_ssh_private_key_file=../terraform/id_rsa\n" > ansible/inventory.ini; \
	cd ansible && ansible-playbook -i inventory.ini playbooks/site.yml

build-image:
	docker build -t ballagan-telecom-api:latest .
	docker build -t ballagan-telecom-api:canary .
	docker save ballagan-telecom-api:latest ballagan-telecom-api:canary -o ballagan-images.tar

push-image: build-image
	@VM_IP=$$(cd terraform && terraform output -raw server_ip); \
	scp -o StrictHostKeyChecking=no -i terraform/id_rsa ballagan-images.tar root@$$VM_IP:/tmp/; \
	ssh -o StrictHostKeyChecking=no -i terraform/id_rsa root@$$VM_IP "ctr -n k8s.io images import /tmp/ballagan-images.tar && rm /tmp/ballagan-images.tar"; \
	rm ballagan-images.tar

tf-destroy:
	cd terraform && terraform destroy -auto-approve