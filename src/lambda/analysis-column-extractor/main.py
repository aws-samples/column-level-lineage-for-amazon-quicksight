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
s3_bucket_folder_name = "analyses"


def lambda_handler(event, context):
    # Initialize QuickSight client and paginator
    quicksight = boto3.client("quicksight")
    paginator = quicksight.get_paginator("list_analyses")

    # Get environment variables
    analysis_prefix = os.environ.get("QUICKSIGHT_ANALYSIS_PREFIX", "")
    result_bucket = os.environ.get("QUICKSIGHT_RESULT_BUCKET")
    account_id = os.environ.get("QUICKSIGHT_ACCOUNT_ID")

    # Check for required environment variables
    if not result_bucket or not account_id:
        logger.error(
            "Error: QUICKSIGHT_ACCOUNT_ID or QUICKSIGHT_RESULT_BUCKET environment variable is missing"
        )
        return

    # Dictionary to store analysis summaries
    analysis_summary = {}

    # Paginate through analyses
    analysis_page_iterator = paginator.paginate(AwsAccountId=account_id)

    # Clean up the existing S3 folder
    if cleanup_s3_folder(result_bucket, s3_bucket_folder_name):
        # Retrieve analysis summaries
        analysis_summary = {
            analysis["AnalysisId"]: analysis["Name"]
            for page in analysis_page_iterator
            for analysis in page["AnalysisSummaryList"]
            if analysis.get("Status") != "DELETED"
        }

        # Check if analysis_summary is empty
        if not analysis_summary:
            logger.info(
                f"No quicksight analyses found under {account_id}. Skipping futher column extraction."
            )
            return

        for id in analysis_summary:
            # Check if analysis prefix is specified or analysis name starts with the prefix
            if not analysis_prefix or analysis_summary[id].startswith(analysis_prefix):
                # Describe the analysis
                definition = quicksight.describe_analysis_definition(
                    AwsAccountId=account_id, AnalysisId=id
                )["Definition"]
                calculated_fields = extract_calculated_fields(definition)
                extracted_columns = find_columns_recursive(
                    data=definition, calculated_fields=calculated_fields
                )
                formatted_json_data = {analysis_summary[id]: extracted_columns}
                flat_json_string = convert_to_flat_json_string(
                    data=formatted_json_data,
                    dataset_summary=get_dataset_summary(
                        definition["DataSetIdentifierDeclarations"]
                    ),
                )
                analysis_name = re.sub(r"[^a-zA-Z0-9_\-.]", "_", analysis_summary[id])

                # Write JSON data to S3
                if flat_json_string:
                    write_result_to_s3(
                        analysis_name, result_bucket, s3_bucket_folder_name, flat_json_string
                    )
