import logging
import os
import re

import boto3

# Imports libs from column-extractor-utils layer
from utils import (
    cleanup_s3_folder,
    convert_to_flat_json_string,
    extract_calculated_fields,
    find_columns_recursive,
    get_dataset_summary,
    write_result_to_s3,
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define the S3 bucket folder name
s3_bucket_folder_name = "dashboards"


def lambda_handler(event, context):
    # Initialize QuickSight client and paginator
    quicksight = boto3.client("quicksight")
    paginator = quicksight.get_paginator("list_dashboards")

    # Get environment variables
    dashboard_prefix = os.environ.get("QUICKSIGHT_DASHBOARD_PREFIX", "")
    result_bucket = os.environ.get("QUICKSIGHT_RESULT_BUCKET")
    account_id = os.environ.get("QUICKSIGHT_ACCOUNT_ID")

    # Check for required environment variables
    if not result_bucket or not account_id:
        logger.error(
            "Error: QUICKSIGHT_ACCOUNT_ID or QUICKSIGHT_RESULT_BUCKET environment variable is missing"
        )
        return

    # Dictionary to store dashboard summaries
    dashboard_summary = {}

    # Paginate through dashboards
    dashboard_page_iterator = paginator.paginate(AwsAccountId=account_id)

    # Clean up the existing S3 folder
    if cleanup_s3_folder(result_bucket, s3_bucket_folder_name):
        # Retrieve dashboard summaries

        dashboard_summary = {
            dashboard["DashboardId"]: dashboard["Name"]
            for page in dashboard_page_iterator
            for dashboard in page["DashboardSummaryList"]
            if dashboard.get("Status") != "DELETED"
        }

        # Check if dashboard_summary is empty
        if not dashboard_summary:
            logger.info(
                f"No quicksight dashboards found under {account_id}. Skipping futher column extraction."
            )
            return

        for id in dashboard_summary:
            # Check if dashboard prefix is specified or dashboard name starts with the prefix
            if not dashboard_prefix or dashboard_summary[id].startswith(dashboard_prefix):
                # Describe the dashboard
                definition = quicksight.describe_dashboard_definition(
                    AwsAccountId=account_id, DashboardId=id
                )["Definition"]
                calculated_fields = extract_calculated_fields(definition)
                extracted_columns = find_columns_recursive(
                    data=definition, calculated_fields=calculated_fields
                )
                formatted_json_data = {dashboard_summary[id]: extracted_columns}
                flat_json_string = convert_to_flat_json_string(
                    formatted_json_data,
                    dataset_summary=get_dataset_summary(
                        definition["DataSetIdentifierDeclarations"]
                    ),
                )
                dashboard_name = re.sub(r"[^a-zA-Z0-9_\-.]", "_", dashboard_summary[id])

                # Write JSON data to S3
                if flat_json_string:
                    write_result_to_s3(
                        dashboard_name, result_bucket, s3_bucket_folder_name, flat_json_string
                    )

    else:
        logger.error(f"Failed to cleanup the s3 folder ({s3_bucket_folder_name}) for the result")
