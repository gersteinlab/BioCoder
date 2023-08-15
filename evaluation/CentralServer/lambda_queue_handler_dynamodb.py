import json
import boto3
import base64
import hashlib

client = boto3.client('dynamodb')


def lambda_handler(event, context):
    path = event["requestContext"]["http"]["path"]
    if path == '/get':
        # not finished and not in progress
        response = client.scan(
            TableName="gerstein_data",
            FilterExpression="finished = :false AND inprogress = :false",
            ExpressionAttributeValues={
                ":false": {
                    "BOOL": False
                },
            },
            Limit=1
        )

        items = response["Items"]
        if len(items) == 0:
            # reset all inprogress to false, only if they are not also finished
            response = client.scan(
                TableName="gerstein_data",
                FilterExpression="inprogress = :true AND finished = :false",
                ExpressionAttributeValues={
                    ":false": {
                        "BOOL": False
                    },
                    ":true": {
                        "BOOL": True
                    }
                }
            )
            for item in response["Items"]:
                client.update_item(
                    TableName="gerstein_data",
                    Key={
                        "test_case_id": {
                            "S": item["test_case_id"]["S"]
                        }
                    },
                    UpdateExpression="SET inprogress = :false",
                    ExpressionAttributeValues={
                        ":false": {
                            "BOOL": False
                        }
                    }
                )

            response = client.scan(
                TableName="gerstein_data",
                FilterExpression="finished = :false AND inprogress = :false",
                ExpressionAttributeValues={
                    ":false": {
                        "BOOL": False
                    },
                },
                Limit=1
            )
            items = response["Items"]

        if len(items) == 0:
            return {
                "statusCode": 200,
                "body": ""
            }

        item = items[0]
        print(item)
        json_str = item['body']["S"]

        client.update_item(
            TableName="gerstein_data",
            Key={
                "test_case_id": {
                    "S": item["test_case_id"]["S"]
                }
            },
            UpdateExpression="SET inprogress = :true",
            ExpressionAttributeValues={
                ":true": {
                    "BOOL": True
                }
            }
        )
        return {
            "statusCode": 200,
            "body": json_str
        }
    elif path == "/submit":
        param = event["queryStringParameters"]
        if (param["result"] in ["pass", "True", "true", "correct"]):
            res_bool = True
        else:
            res_bool = False
        id_int = str(param["test_case_id"])
        print(id_int)
        # update the item to be finished
        response = client.update_item(
            TableName="gerstein_data",
            Key={
                "test_case_id": {
                    "S": id_int
                }
            },
            UpdateExpression="SET finished = :true, res = :resu",
            ExpressionAttributeValues={
                ":true": {
                    "BOOL": True
                },
                ":resu": {
                    "BOOL": res_bool
                }
            }
        )

        return {
            "statusCode": 200,
            "body": "successful"
        }
    elif path == "/add":
        s = event["body"]
        if "body" not in event:
            return {
                "statusCode": 404,
                "body": "empty body"
            }
        if isBase64(s): s = base64.b64decode(s).decode("utf-8")
        try:
            s = base64.b64decode(s).decode("utf-8")
        except:
            return s
        json_obj = json.loads(s)

        # look for the test case id first
        response = client.get_item(
            TableName="gerstein_data",
            Key={
                "test_case_id": {
                    "S": json_obj["test_case_id"]
                }
            }
        )
        if "Item" in response:
            return {
                "statusCode": 200,
                "body": "already exists"
            }

        response2 = client.put_item(
            TableName="gerstein_data",
            Item={
                "test_case_id": {
                    "S": json_obj["test_case_id"]
                },
                "result": {
                    "BOOL": False
                },
                "finished": {
                    "BOOL": False
                },
                "inprogress": {
                    "BOOL": False
                },
                "body": {
                    "S": s
                }
            }
        )
        return {
            'statusCode': 200,
            'body': "successful"
        }
    elif path == "/getallresults":
        responses = {}
        last_evaluated_key = None
        while True:
            response = client.scan(
                TableName="gerstein_data",
                ExclusiveStartKey=last_evaluated_key
            )
            for item in response["Items"]:
                # only append if it's finished
                responses[item["test_case_id"]["S"]] = item["result"]["BOOL"]
            if "LastEvaluatedKey" not in response:
                break
            last_evaluated_key = response["LastEvaluatedKey"]
        json_obj = {
            "responses": responses
        }
        return {
            'statusCode': 200,
            'body': json.dumps(json_obj)
        }
    # elif path=="/reset":
    #     truncateTable("gerstein_data")
    #     return {
    #         'statusCode': 200,
    #         'body': "successful"
    #     }
    #
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps(path)
    # }


def isBase64(s):
    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception:
        return False


def truncateTable(tableName):
    table = client.Table(tableName)

    # get the table keys
    tableKeyNames = [key.get("AttributeName") for key in table.key_schema]

    # Only retrieve the keys for each item in the table (minimize data transfer)
    projectionExpression = ", ".join('#' + key for key in tableKeyNames)
    expressionAttrNames = {'#' + key: key for key in tableKeyNames}

    counter = 0
    page = table.scan(ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames)
    with table.batch_writer() as batch:
        while page["Count"] > 0:
            counter += page["Count"]
            # Delete items in batches
            for itemKeys in page["Items"]:
                batch.delete_item(Key=itemKeys)
            # Fetch the next page
            if 'LastEvaluatedKey' in page:
                page = table.scan(
                    ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames,
                    ExclusiveStartKey=page['LastEvaluatedKey'])
            else:
                break
    print(f"Deleted {counter}")


