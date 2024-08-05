import json
import logging
import re

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def cleanup_s3_folder(bucket, folder_name):
    """
    Clean up data in S3 under a specific folder.

    Parameters:
        folder_name (str): S3 folder name.
        bucket (str): Name of the S3 bucket.

    Returns:
        bool: True if cleanup is successful or folder is missing, False for other errors.
    """
    s3 = boto3.client("s3")
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=folder_name)
        if "Contents" in response:
            for obj in response["Contents"]:
                s3.delete_object(Bucket=bucket, Key=obj["Key"])
            resp = s3.delete_object(Bucket=bucket, Key=folder_name)
            if resp["ResponseMetadata"]["HTTPStatusCode"] == 204:
                return True
            else:
                logger.error(f"Failed to delete folder {folder_name} in S3 bucket {bucket}")
                return False
        else:
            logger.warning(
                f"Folder {folder_name} not found in S3 bucket {bucket}, skipping cleanup."
            )
            return True
    except Exception as e:
        logger.error(f"Error cleaning up S3 bucket folder {folder_name}: {e}")
        return False


def write_result_to_s3(resource_name, bucket, folder_name, json_string):
    """
    Write analysis data to S3 under a specific folder.

    Parameters:
        folder_name (str): S3 folder name.
        bucket (str): Name of the S3 bucket to write the data to.
        resource_name (str): Name of the resource (dashboard, analysis, dataset etc).
        json_string (str): JSON data to write to S3.
    """
    s3 = boto3.client("s3")
    try:
        object_key = f"{folder_name}/{resource_name}.json"
        s3.put_object(Bucket=bucket, Key=object_key, Body=json_string.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error writing JSON data to S3 with error: {e}")


def get_dataset_summary(dataSetIdentifierDeclarations):
    """
    Extracts dataset summaries from a list of dataset identifier declarations.

    Args:
        dataSetIdentifierDeclarations (list of dict): List containing dictionaries with keys "Identifier" and "DataSetArn".

    Returns:
        dict: A dictionary where keys are dataset identifiers and values are dataset IDs extracted from DataSetArn.
    """
    dataset_summary = {}
    for dataset_declaration in dataSetIdentifierDeclarations:
        name = dataset_declaration.get("Identifier")
        dataset_arn = dataset_declaration.get("DataSetArn")
        if name and dataset_arn:
            dataset_id = dataset_arn.split("/")[-1]
            dataset_summary[name] = dataset_id

    return dataset_summary


def convert_to_flat_json_string(data, dataset_summary):
    """
    Convert nested JSON data containing column summaries into a newline-separated JSON string.

    Args:
        data (dict): Nested JSON data containing column summaries.
        dataset_summary (dict): Summary of datasets with dataset identifiers as keys and dataset IDs as values.

    Returns:
        str: Newline-separated JSON string representing the column summaries.
    """
    name = next(iter(data))
    flat_json_list = []

    for column_summary in data[name]:
        dataset_id = dataset_summary.get(column_summary.get("DataSetIdentifier"), "Unknown")
        flat_json = {
            "Name": name,
            "DataSetName": column_summary.get("DataSetIdentifier"),
            "DataSetId": dataset_id,
            "ColumnName": column_summary.get("ColumnName"),
            "CalculatedColumnName": column_summary.get("CalculatedColumnName"),
            "UsedColumns": column_summary.get("UsedColumns"),
        }
        # Remove keys with None values for a cleaner output
        clean_flat_json = {k: v for k, v in flat_json.items() if v is not None}
        flat_json_list.append(clean_flat_json)

    # Convert list of dictionaries to newline-separated JSON strings
    return "\n".join(json.dumps(obj) for obj in flat_json_list)


def extract_calculated_fields(data):
    """
    Extract calculated fields and the columns used in their expressions from QuickSight data.

    Args:
        data (dict): QuickSight data containing calculated fields.

    Returns:
        dict: A dictionary where keys are calculated field names and values are lists of used column names.
    """
    calculated_fields = {}

    # Define a regex pattern to identify potential column references
    function_pattern = r"\b(?:split|ifelse|left|right|substring|coalesce|dateDiff|dateAdd|extract|toDate|toTimestamp)\("
    column_pattern = re.compile(
        rf"(?:(?:{function_pattern})[^,)]+)|(?:\b(?<!\')[a-zA-Z_][\w]*\b(?!\'))"
    )

    for calculated_field in data.get("CalculatedFields", []):
        field_name = calculated_field.get("Name", "")
        expression = calculated_field.get("Expression", "")

        # Find all matches using the updated pattern
        matches = column_pattern.findall(expression)

        # Process matches to extract column names
        used_columns = set()
        for match in matches:
            clean_match = re.sub(r"(\b(?:{function_pattern})\b|\s+|\(|\))", "", match)
            potential_columns = re.split(r"[\s,=]+", clean_match)
            for col in potential_columns:
                if col:  # Ignore empty strings and non-column patterns
                    used_columns.add(col)

        calculated_fields[field_name] = list(used_columns)

    return calculated_fields


def find_columns_recursive(data, calculated_fields, unique_columns=None):
    """
    Recursively find columns in nested dictionaries or lists.

    Args:
        data (dict or list): The data to search for columns.
        calculated_fields (dict): A dictionary of calculated fields.
        unique_columns (set): A set to track unique column information.

    Returns:
        list: A list of column dictionaries found in the data.
    """
    if unique_columns is None:
        unique_columns = set()

    columns = []

    if isinstance(data, dict):
        if "DataSetIdentifier" in data and "ColumnName" in data:
            column_info = (data["ColumnName"], data["DataSetIdentifier"])
            if column_info not in unique_columns:
                unique_columns.add(column_info)
                if data["ColumnName"] in calculated_fields:
                    columns.append(
                        {
                            "CalculatedColumnName": data["ColumnName"],
                            "UsedColumns": calculated_fields[data["ColumnName"]],
                            "DataSetIdentifier": data["DataSetIdentifier"],
                        }
                    )
                else:
                    columns.append(
                        {
                            "ColumnName": data["ColumnName"],
                            "DataSetIdentifier": data["DataSetIdentifier"],
                        }
                    )

        for key, value in data.items():
            columns.extend(find_columns_recursive(value, calculated_fields, unique_columns))

    elif isinstance(data, list):
        for sub_data in data:
            columns.extend(find_columns_recursive(sub_data, calculated_fields, unique_columns))

    return columns
