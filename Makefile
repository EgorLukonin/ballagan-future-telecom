.PHONY: up tf-init tf-plan tf-apply tf-destroy

up: tf-init tf-apply

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan

tf-apply:
	cd terraform && terraform apply -auto-approve

tf-destroy:
	cd terraform && terraform destroy -auto-approve