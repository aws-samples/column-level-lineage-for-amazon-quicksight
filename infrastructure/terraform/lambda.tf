locals {
  column_extractor_functions = {
    "analysis"  = "Lambda function to extract columns from Quicksight Analysis"
    "dashboard" = "Lambda function to extract columns from Quicksight Dashboard"
    "dataset"   = "Lambda function to extract columns from Quicksight Dataset"
  }
}

module "column_extractor_utils_layer" {
  source = "git::https://github.com/terraform-aws-modules/terraform-aws-lambda.git?ref=9e3798ed4c2db0216369d27c1c02891ec9fcec7d" # commit hash of version 7.2.0"

  create_layer        = true
  layer_name          = "${var.prefix}-column-extractor-utils-layer-${var.stage}"
  description         = "Lambda layer for Shared clients and utils"
  compatible_runtimes = [var.lambda_python_runtime]
  runtime             = var.lambda_python_runtime

  source_path = [
    {
      path             = "${path.module}/../../src/lambda/column-extractor-utils-layer"
      pip_requirements = var.layer_pip_requirements
      prefix_in_zip    = "python"
    }
  ]

  store_on_s3 = true
  s3_bucket   = module.column_extractor_utils_layer_bucket.s3_bucket_id
  tags        = var.default_tags
}

module "lambda_function_column_extractor" {
  for_each = local.column_extractor_functions
  source   = "git::https://github.com/terraform-aws-modules/terraform-aws-lambda.git?ref=9e3798ed4c2db0216369d27c1c02891ec9fcec7d" # commit hash of version 7.2.0"

  create_function                   = true
  function_name                     = "${var.prefix}-${each.key}-column-extractor-lambda-${var.stage}"
  description                       = each.value
  handler                           = "main.lambda_handler"
  runtime                           = var.lambda_python_runtime
  publish                           = true
  timeout                           = var.lambda_timeout
  reserved_concurrent_executions    = var.lambda_concurrent_executions
  maximum_retry_attempts            = 1
  cloudwatch_logs_retention_in_days = 30
  source_path                       = "${path.module}/../../src/lambda/${each.key}-column-extractor"
  layers                            = [module.column_extractor_utils_layer.lambda_layer_arn]

  attach_policy_statements = true
  policy_statements = {

    quicksight = {
      effect = "Allow"
      actions = [
        "quicksight:ListAnalyses",
        "quicksight:ListDashboards",
        "quicksight:ListDatasets",
        "quicksight:Describe*"
      ]
      resources = ["*"]
    }

    s3 = {
      effect = "Allow"
      actions = [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObjectTagging",
        "s3:PutObjectTagging"
      ]
      resources = [
        "${module.column_extractor_results_bucket.s3_bucket_arn}",
        "${module.column_extractor_results_bucket.s3_bucket_arn}/*",
      ]
    }
  }

  environment_variables = {
    QUICKSIGHT_ACCOUNT_ID    = local.aws_account_id
    QUICKSIGHT_RESULT_BUCKET = module.column_extractor_results_bucket.s3_bucket_id
  }
  tags = var.default_tags
}
