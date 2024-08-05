import json
import logging
import os
import re

import boto3

# Imports libs from column-extractor-utils layer
from utils import cleanup_s3_folder, write_result_to_s3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define the S3 bucket folder name
s3_bucket_folder_name = "datasets"


def lambda_handler(event, context):
    # Initialize QuickSight client and paginator
    quicksight = boto3.client("quicksight")
    paginator = quicksight.get_paginator("list_data_sets")

    # Get environment variables
    result_bucket = os.environ.get("QUICKSIGHT_RESULT_BUCKET")
    account_id = os.environ.get("QUICKSIGHT_ACCOUNT_ID")

    # Dictionary to store dataset summaries
    dataset_summary = {}

    # Paginate through datasets
    dataset_page_iterator = paginator.paginate(AwsAccountId=account_id)

    # Clean up the existing S3 folder
    if cleanup_s3_folder(result_bucket, s3_bucket_folder_name):
        # Retrieve dataset summaries
        dataset_summary = {
            dataset["DataSetId"]: {
                "Name": dataset["Name"],
                "RLSDataSetId": dataset.get("RowLevelPermissionDataSet", {})
                .get("Arn", "")
                .split("/")[-1]
                or None,
            }
            for page in dataset_page_iterator
            for dataset in page["DataSetSummaries"]
        }

        # Check if dataset_summary is empty
        if not dataset_summary:
            logger.info(
                f"No quicksight dataset found under {account_id}. Skipping futher column extraction."
            )
            return

        # Process each dataset
        for id in dataset_summary:
            try:
                # Describe the dataset
                dataset_describe = quicksight.describe_data_set(
                    AwsAccountId=account_id, DataSetId=id
                )
            except quicksight.exceptions.InvalidParameterValueException as e:
                # Skip unsupported dataset types
                print(f"Skipping unsupported dataset type for DataSetId: {id}. Error: {str(e)}")
                continue  # Skip to the next dataset

            # Extract column information from OutputColumns
            columns = dataset_describe["DataSet"].get("OutputColumns", [])

            # Create JSON lines for each column
            lines = []
            for col in columns:
                flat_json_item = json.dumps(
                    {
                        "DataSetId": id,
                        "DataSetName": dataset_summary[id]["Name"],
                        "RLSDataSetId": dataset_summary[id]["RLSDataSetId"],
                        "ColumnName": col["Name"],
                        "ColumnType": col["Type"],
                    }
                )
                lines.append(flat_json_item)
            flat_json_data = "\n".join(lines)

            # Write JSON data to S3
            if lines:
                dataset_name = re.sub(r"[^a-zA-Z0-9_\-.]", "_", dataset_summary[id]["Name"])
                write_result_to_s3(
                    dataset_name, result_bucket, s3_bucket_folder_name, flat_json_data
                )
    else:
        logger.error(f"Failed to cleanup the s3 folder({s3_bucket_folder_name}) for the result")
