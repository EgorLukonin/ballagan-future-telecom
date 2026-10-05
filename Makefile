.PHONY: up tf-init tf-plan tf-apply tf-destroy ansible

up: tf-init tf-apply ansible

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

tf-destroy:
	cd terraform && terraform destroy -auto-approve