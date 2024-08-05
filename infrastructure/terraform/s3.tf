module "column_extractor_results_bucket" {
  source = "git::https://github.com/terraform-aws-modules/terraform-aws-s3-bucket.git?ref=3a1c80b29fdf8fc682d2749456ec36ecbaf4ce14" # commit hash of version 4.1.0"

  bucket = "${var.prefix}-${local.aws_account_id}-column-extractor-results-${var.stage}"
  tags   = var.default_tags
}

module "column_extractor_utils_layer_bucket" {
  source = "git::https://github.com/terraform-aws-modules/terraform-aws-s3-bucket.git?ref=3a1c80b29fdf8fc682d2749456ec36ecbaf4ce14" # commit hash of version 4.1.0"

  bucket = "${var.prefix}-${local.aws_account_id}-column-extractor-utils-layer-artifacts-${var.stage}"
  tags   = var.default_tags
}
