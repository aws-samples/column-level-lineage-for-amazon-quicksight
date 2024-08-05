# Amazon Quicksight Column Lineage

This is the code repository for code sample used in AWS blog [Amazon Quicksight Column Lineage](https://aws.amazon.com/blogs/aws/)

## Prerequisites

Before proceeding with this walkthrough, ensure you have the following:

- **AWS Account**: An active AWS account is required. If you don't have one yet, you can sign up [here](https://signin.aws.amazon.com/signin?redirect_uri=https%3A%2F%2Fportal.aws.amazon.com%2Fbilling%2Fsignup%2Fresume&client_id=signup).

- **QuickSight Enterprise Edition Subscription**: Obtain a subscription to QuickSight Enterprise Edition.

- **AWS CLI Installation**: Install the AWS Command Line Interface (CLI) using the instructions found [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

- **Terraform Installation**: Ensure Terraform is installed on your local machine. Refer to the installation guide [here](https://learn.hashicorp.com/tutorials/terraform/install-cli).

- **AWS IAM Permissions**: Make sure you have the necessary IAM permissions required to create AWS resources using Terraform

- **pre-commit Installation**: Install pre-commit, a framework for managing and maintaining multi-language pre-commit hooks. This tool is used to automate code quality checks and security scans. Follow the installation instructions [here](https://pre-commit.com/#install).

Optionally, you may also want to consider:

- **Makefile**: While not mandatory, having the `make` command available is recommended. The target commands within the provided [Makefile](./Makefile) can be executed independently.

## Deployment

As mentioned earlier in the Solution Overview, as part of this deployment, we will be deploying the following AWS resources using Terraform:

1. AWS Lambda Functions:
	- [analysis-column-extractor](src/lambda/analysis-column-extractor)
	- [dashboard-column-extractor](src/lambda/dashboard-column-extractor)
	- [dataset-column-extractor](src/lambda/dataset-column-extractor)
2. AWS Lambda Layer for utils
3. Glue Database
4. Glue Catalog Tables:
	- Dashboard details
	- Analysis details
	- Dataset details
5. S3 Bucket for storing lambda results.
6. Necessary Lambda Execution IAM Roles

### Clone the GitHub repository

Clone the [GitHub repository](https://github.com/aws-samples/column-level-lineage-for-amazon-quicksight) to your local machine. This repository contains all the code needed for the walkthrough. Use the following command to clone the repository:

```bash
$ git clone git@github.com:aws-samples/column-level-lineage-for-amazon-quicksight.git
```

### Terraform Deployment

Navigate to the infrastructure directory to initialize and deploy the AWS resources using Terraform:

- Terraform Initialization

	```bash
	$ make init
	```
	or

	```bash
	$ cd infrastructure
	$ terraform init
	```
- Terraform Plan

	```bash
	$ make plan
	```
	or

	```bash
	$ cd infrastructure
	$ terraform plan
	```

- Terraform Apply

	```bash
	$ make apply
	```
	or

	```bash
	$ cd infrastructure
	$ terraform apply
	```

### Linting and Security Checks

To ensure code quality and security, run the following commands:

- **Linting**: Run `make lint` to perform linting on the source and infrastructure directories. This checks for common code quality issues.

	```bash
	$ make lint
	```

- **Security**: Run `make security` to perform security checks on the source and infrastructure directories using pre-commit. The following hooks are used for security:

	- bandit
	- checkov

	```bash
	$ make security
	```

## Cleanup

It's important to clean up the resources to avoid incurring unnecessary costs. Follow these steps to clean up:

1. Manually delete the data stored in the S3 bucket.
2. Delete other AWS resources using Terraform:

	```bash
	$ make destroy
	```
	or

	```bash
	$ cd infrastructure
	$ terraform destroy
	```
These steps will ensure that all resources created during this walkthrough are properly cleaned up.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

