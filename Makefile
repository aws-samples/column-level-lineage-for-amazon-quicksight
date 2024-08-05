.PHONY: init plan apply checkov

TF_DIR := infrastructure/terraform
SRC_DIR := src

init:
	@cd $(TF_DIR) && terraform init

plan:
	@cd $(TF_DIR) && terraform plan -out=tfplan

apply: plan
	@cd $(TF_DIR) && terraform apply tfplan

destroy:
	@cd $(TF_DIR) && terraform destroy

lint:
	@git diff-index --cached --name-only HEAD -- $(SRC_DIR) $(TF_DIR) | xargs pre-commit run lint --files

security:
	@git diff-index --cached --name-only HEAD -- $(SRC_DIR) $(TF_DIR) | xargs pre-commit run security --files
