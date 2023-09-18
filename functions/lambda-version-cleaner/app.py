import os
from typing import Dict, List
import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

NUM_VERSIONS_TO_KEEP = int(os.environ["NUM_VERSIONS_TO_KEEP"])
REGIONS = os.environ["REGIONS"].split(",")


BOTO_SESSION = boto3.Session()
LAMBDA_CLIENTS = dict()
for region in REGIONS:
    LAMBDA_CLIENTS[region] = BOTO_SESSION.client("lambda", region_name=region)

LOGGER = Logger()


def get_functions(region: str) -> List[Dict[str, str]]:
    # Get a list of all Lambda function names
    try:
        list_functions_paginator = LAMBDA_CLIENTS[region].get_paginator(
            "list_functions"
        )

        pages = [page["Functions"] for page in list_functions_paginator.paginate()]
        return [
            {"function_name": function["FunctionName"], "version": function["Version"]}
            for page in pages
            for function in page
        ]
    except ClientError as e:
        LOGGER.error(f"Failed to list all Lambda function in region {region}: {e}")
        raise


def get_function_versions(function: Dict[str, str], region: str) -> List[str]:
    # Get a list of all versions of the Lambda function
    try:
        list_versions_paginator = LAMBDA_CLIENTS[region].get_paginator(
            "list_versions_by_function"
        )

        pages = [
            page["Versions"]
            for page in list_versions_paginator.paginate(
                FunctionName=function["function_name"]
            )
        ]
        return sorted(
            [
                version["Version"]
                for page in pages
                for version in page
                if version["Version"] != function["version"]
            ],
            reverse=True,
        )
    except ClientError as e:
        LOGGER.error(
            f"Failed to list Lambda versions for function {function['function_name']} in region {region}: {e}"
        )
        raise


def get_function_alias_versions(function_name: str, region: str) -> List[str]:
    # Get a list of all versions used by function aliases
    try:
        response = LAMBDA_CLIENTS[region].list_aliases(FunctionName=function_name)
        return [alias["FunctionVersion"] for alias in response["Aliases"]]
    except ClientError as e:
        LOGGER.error(
            f"Failed to list Lambda version for function {function_name} in region {region}: {e}"
        )
        raise


def delete_function_version(version: str, function_name: str, region: str) -> None:
    # Delete inputted Lambda function
    try:
        LAMBDA_CLIENTS[region].delete_function(
            FunctionName=function_name, Qualifier=version
        )
    except ClientError as e:
        LOGGER.error(
            f"Failed to delete Lambda version {version} for function {function_name} in region {region}: {e}"
        )
        raise


@LOGGER.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    num_deleted_versions = 0
    for region in REGIONS:
        LOGGER.info(f"Scanning Lambda functions in region {region}...")
        functions = get_functions(region)

        # Loop through all functions and remove old versions
        for function in functions:
            versions = get_function_versions(function, region)
            alias_versions = get_function_alias_versions(
                function["function_name"], region
            )

            # Keep only NUM_VERSIONS_TO_KEEP number of most recent versions
            versions_to_delete = versions[NUM_VERSIONS_TO_KEEP:]

            # Delete all versions in versions_to_delete
            for version in versions_to_delete:
                if version not in alias_versions:
                    delete_function_version(version, function["function_name"], region)
                    LOGGER.info(
                        f"Deleted version {version} from function {function['function_name']}"
                    )

        LOGGER.info(f"Deleted {len(versions_to_delete)} versions in region {region}")
        num_deleted_versions += len(versions_to_delete)

    return {"statusCode": 200, "body": f"Deleted {num_deleted_versions} old versions."}
