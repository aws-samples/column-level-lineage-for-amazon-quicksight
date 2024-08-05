variable "prefix" {
  description = "Prefix to be used for naming resources"
  default     = "qs-blog"
}

variable "stage" {
  description = "Stage of the environment"
  default     = "dev"
}

variable "aws_region" {
  description = "The AWS region where infrastructure resources will be provisioned."
  default     = "eu-central-1"
}

variable "lambda_python_runtime" {
  description = "Python runtime version for Lambda functions"
  default     = "python3.12"
}

variable "default_tags" {
  description = "Default tags to be applied to all AWS resources"
  type        = map(string)
  default = {
    "project" : "qs-blog"
    "stage" : "dev"
  }
}

variable "layer_pip_requirements" {
  description = "Path to the pip requirements file for Lambda layer"
  default     = false
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  default     = "600"
}

variable "lambda_concurrent_executions" {
  description = "Maximum number of concurrent executions for Lambda function"
  default     = "10"
}
