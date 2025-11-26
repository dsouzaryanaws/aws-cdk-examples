# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import json
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb_client = boto3.client("dynamodb")


def handler(event, context):
    table = os.environ.get("TABLE_NAME")
    
    # Log request metadata
    request_context = event.get("requestContext", {})
    identity = request_context.get("identity", {})
    
    logger.info(json.dumps({
        "event": "request_received",
        "request_id": context.request_id,
        "source_ip": identity.get("sourceIp"),
        "user_agent": identity.get("userAgent"),
        "table_name": table,
    }))
    
    try:
        if event.get("body"):
            item = json.loads(event["body"])
            logger.info(json.dumps({
                "event": "payload_received",
                "request_id": context.request_id,
                "item_id": item.get("id"),
            }))
            
            year = str(item["year"])
            title = str(item["title"])
            id = str(item["id"])
            
            dynamodb_client.put_item(
                TableName=table,
                Item={"year": {"N": year}, "title": {"S": title}, "id": {"S": id}},
            )
            
            logger.info(json.dumps({
                "event": "dynamodb_write_success",
                "request_id": context.request_id,
                "table": table,
                "item_id": id,
            }))
            
            message = "Successfully inserted data!"
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": message}),
            }
        else:
            logger.info(json.dumps({
                "event": "request_without_payload",
                "request_id": context.request_id,
            }))
            
            default_id = str(uuid.uuid4())
            dynamodb_client.put_item(
                TableName=table,
                Item={
                    "year": {"N": "2012"},
                    "title": {"S": "The Amazing Spider-Man 2"},
                    "id": {"S": default_id},
                },
            )
            
            logger.info(json.dumps({
                "event": "dynamodb_write_success",
                "request_id": context.request_id,
                "table": table,
                "item_id": default_id,
            }))
            
            message = "Successfully inserted data!"
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": message}),
            }
    except KeyError as e:
        logger.error(json.dumps({
            "event": "validation_error",
            "error_type": "KeyError",
            "error_message": f"Missing required field: {str(e)}",
            "request_id": context.request_id,
        }))
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Missing required field: {str(e)}"}),
        }
    except json.JSONDecodeError as e:
        logger.error(json.dumps({
            "event": "json_parse_error",
            "error_type": "JSONDecodeError",
            "error_message": str(e),
            "request_id": context.request_id,
        }))
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON format"}),
        }
    except Exception as e:
        logger.error(json.dumps({
            "event": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "request_id": context.request_id,
        }))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"}),
        }
