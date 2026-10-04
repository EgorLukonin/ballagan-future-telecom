.PHONY: up tf-init tf-plan tf-apply tf-destroy ansible

up: tf-init tf-apply ansible

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan

tf-apply:
	cd terraform && terraform apply -auto-approve

ansible:
	cd ansible && ansible-playbook playbooks/site.yml

tf-destroy:
	cd terraform && terraform destroy -auto-approve