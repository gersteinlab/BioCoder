import json
import boto3
import base64
import hashlib
import os
import time
client = boto3.client('dynamodb')
sqs = boto3.client('sqs')
s3 = boto3.client('s3')

# check if TESTING is set
prod = not ("TESTING" in os.environ)
if prod:
    queue_url = "https://sqs.us-east-1.amazonaws.com/AWS_ACCOUNT_ID/gerstein_queue_standard"
    queue_url_inprogress = "https://sqs.us-east-1.amazonaws.com/AWS_ACCOUNT_ID/gerstein_queue_standard_inprogress"
    dynamodb_table = "gerstein_data"
else:
    # use test queues
    queue_url = "https://sqs.us-east-1.amazonaws.com/AWS_ACCOUNT_ID/gerstein_queue_test.fifo"
    queue_url_inprogress = "https://sqs.us-east-1.amazonaws.com/AWS_ACCOUNT_ID/gerstein_queue_inprogress_test.fifo"
    dynamodb_table = "gerstein_data_test"

def generate_random_string():
    return base64.b64encode(hashlib.sha256(os.urandom(256)).digest()).decode('utf-8')
def lambda_handler(event, context):
    path = event["requestContext"]["http"]["path"]
    if path == '/get':

        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'notinprogress'
            ],
        )
        if "Messages" not in response:
            add_unfinished_to_queue()
            response = sqs.receive_message(
                QueueUrl=queue_url,
                AttributeNames=[],
                MaxNumberOfMessages=1,
                MessageAttributeNames=[
                    'notinprogress'
                ],
            )
        if "Messages" not in response:
            return {
                "statusCode": 200,
                "body": ""
            }

        # get item
        message = response['Messages'][0]
        json_str = message['Body']
        receipt_handle = message["ReceiptHandle"]
        item = json.loads(json_str)
        item["random_stringadasd"] = generate_random_string()
        json_str = json.dumps(item)
        # Update item in dynamodb
        client.update_item(
            TableName=dynamodb_table,
            Key={
                "test_case_id": {
                    "S": item["test_case_id"]
                }
            },
            UpdateExpression="SET inprogress = :true",
            ExpressionAttributeValues={
                ":true": {
                    "BOOL": True
                }
            }
        )
        # Delete message from SQS
        response = sqs.change_message_visibility(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=1
        )
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )

        # Send message to SQS with an inprogress attribute
        sqs.send_message(
            QueueUrl=queue_url_inprogress,
            MessageBody=json_str,
            # MessageGroupId="gerstein_queue_inprogess",
            MessageAttributes={
                "inprogress": {
                    "DataType": "String",
                    "StringValue": "true"
                },
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
        if "error" in param:
            reason = param["error"]
        else:
            reason = "successful"

        # check if test_case_id exists
        response = client.get_item(
            TableName=dynamodb_table,
            Key={
                "test_case_id": {
                    "S": id_int
                }
            }
        )
        if "Item" not in response:
            return {
                "statusCode": 404,
                "body": "test case id not found"
            }

        # Update item in dynamodb
        client.update_item(
            TableName=dynamodb_table,
            Key={
                "test_case_id": {
                    "S": id_int
                }
            },
            UpdateExpression="SET finished = :true, res = :resu, reason = :reason",
            ExpressionAttributeValues={
                ":true": {
                    "BOOL": True
                },
                ":resu": {
                    "BOOL": res_bool
                },
                ":reason": {
                    "S": reason
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
            s = s
        json_obj = json.loads(s)
        json_obj["random_stringadasd"] = generate_random_string()
        s = json.dumps(json_obj)
        # look for the test case id first
        response = client.get_item(
            TableName=dynamodb_table,
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

        # Add item to SQS without the inprogress attribute
        response = sqs.send_message(
            QueueUrl=queue_url,
            # MessageGroupId="gerstein_queue",
            MessageAttributes={
                "notinprogress": {
                    "DataType": "String",
                    "StringValue": "true"
                }
            },
            MessageBody=(s)
        )

        # Add item to dynamodb
        response2 = client.put_item(
            TableName=dynamodb_table,
            Item={
                "test_case_id": {
                    "S": json_obj["test_case_id"]
                },
                "res": {
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
        param = event["queryStringParameters"]
        if "password" not in param:
            return {
                "statusCode": 404,
                "body": "password not provided"
            }
        if param["password"] != "gerstein!@#$%":
            return {
                "statusCode": 404,
                "body": "incorrect password"
            }
        if "suffix" not in param:
            suffix = "default"
        else:
            suffix = param["suffix"]
        # Get all items from dynamodb that are finished
        response = client.scan(
            TableName=dynamodb_table,
            AttributesToGet=[
                "test_case_id",
                "res",
                "finished",
                "body"
            ],
        )
        items = response["Items"]
        while "LastEvaluatedKey" in response:
            response = client.scan(
                TableName=dynamodb_table,
                AttributesToGet=[
                    "test_case_id",
                    "res",
                    "finished",
                    "body"
                ],
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response["Items"])
        # remove dynamoDB labels and return
        for i in range(len(items)):
            items[i]["test_case_id"] = items[i]["test_case_id"]["S"]
            items[i]["res"] = items[i]["res"]["BOOL"]
            items[i]["finished"] = items[i]["finished"]["BOOL"]
            items[i]["body"] = json.loads(items[i]["body"]["S"])

        # filter out items that are not finished	
        items = [x for x in items if x["finished"] == True]	
        str1 = generate_random_string()	
        key1 = "results-"+suffix + ".json"	
        s3.put_object(Bucket="gersteincodegenprod", Key=key1, Body=json.dumps(items).encode('utf-8'))	
        	
        return {	
            "statusCode": 200,	
            "body": json.dumps({	
                "key": key1	
            })	
        }
        
    elif path == "/reset_data":
        param = event["queryStringParameters"]
        if "password" not in param:
            return {
                "statusCode": 404,
                "body": "password not provided"
            }
        if param["password"] != "gerstein!@#$%":
            return {
                "statusCode": 404,
                "body": "incorrect password"
            }

        # delete all items in dynamodb
        truncateTable()
        # delete all items in SQS
        response = sqs.purge_queue(
            QueueUrl=queue_url
        )
        response = sqs.purge_queue(
            QueueUrl=queue_url_inprogress
        )
        return {
            "statusCode": 200,
            "body": "successful"
        }
        # # get number of items in SQS
        # response = sqs.get_queue_attributes(
        #     QueueUrl=queue_url,
        #     AttributeNames=[
        #         'ApproximateNumberOfMessages'
        #     ]
        # )
    elif path== "/upload":
        # take data from log in the body and upload to s3
        if "body" not in event:
            print("empty body")
            return {
                "statusCode": 404,
                "body": "empty body"
            }
        data = json.loads(event["body"])
        if "log" not in data:
            print("log not provided")
            return {
                "statusCode": 404,
                "body": "log not provided"
            }
        # get first line of log
        first_line = data["log"].splitlines()[0]
        if "No data" in first_line:
            print("No data")
            return {
                "statusCode": 404,
                "body": "No data"
            }
        # get test case id
        splits = first_line.split("TEST_CASE_ID: ")
        if len(splits) < 2:
            print("TEST_CASE_ID not found")
            return {
                "statusCode": 404,
                "body": "TEST_CASE_ID not found"
            }
        test_case_id = first_line.split("TEST_CASE_ID: ")[1] # TODO: check if it is the first one or second one
        if test_case_id == "":
            print("TEST_CASE_ID is empty")
            return {
                "statusCode": 404,
                "body": "TEST_CASE_ID is empty"
            }
        # create s3 filename by splitting the first 3 characters of the test case id into their own subfolders
        s3_filename = f"output_logs/{test_case_id[0]}/{test_case_id[1]}/{test_case_id[2]}/{test_case_id}.txt"

        # upload to s3
        s3.put_object(
            Bucket="gersteincodegenprod",
            Key=s3_filename,
            Body=data["log"]
        )
        return {
            "statusCode": 200,
            "body": "successful"
        }

    elif path== "/reset_results_only":
        param = event["queryStringParameters"]
        if "password" not in param:
            return {
                "statusCode": 404,
                "body": "password not provided"
            }
        if param["password"] != "gerstein!@#$%":
            return {
                "statusCode": 404,
                "body": "incorrect password"
            }

        # set all items in dynamodb to not finished
        last_evaluated_key = None
        while True:
            response = client.scan(
                TableName=dynamodb_table,
                ExclusiveStartKey=last_evaluated_key
            )
            for item in response["Items"]:
                # only append if it's finished
                client.update_item(
                    TableName=dynamodb_table,
                    Key={
                        "test_case_id": {
                            "S": item["test_case_id"]["S"]
                        }
                    },
                    UpdateExpression="SET finished = :false, res = :false, reason = :reason",
                    ExpressionAttributeValues={
                        ":false": {
                            "BOOL": False
                        },
                        ":reason": {
                            "S": ""
                        }
                    }
                )
            if "LastEvaluatedKey" not in response:
                break
            last_evaluated_key = response["LastEvaluatedKey"]

    return {
        'statusCode': 200,
        'body': json.dumps(path + str(sqs.list_queues()))
    }


def isBase64(s):
    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception:
        return False

def add_unfinished_to_queue():
    response = sqs.receive_message(
        QueueUrl=queue_url_inprogress,
        AttributeNames=[],
        MaxNumberOfMessages=10,
        MessageAttributeNames=[
            'All'
            # 'inprogress'
        ],

    )
    if "Messages" not in response:
        return
    for message in response["Messages"]:
        if "inprogress" not in message["MessageAttributes"]:
            sqs.delete_message(
                QueueUrl=queue_url_inprogress,
                ReceiptHandle=message["ReceiptHandle"]
            )
            continue
        # check if it already is finished in dynamodb
        response = client.get_item(
            TableName=dynamodb_table,
            Key={
                "test_case_id": {
                    "S": json.loads(message["Body"])["test_case_id"]
                }
            }
        )
        if "Item" not in response:
            sqs.delete_message(
                QueueUrl=queue_url_inprogress,
                ReceiptHandle=message["ReceiptHandle"]
            )
            continue
        if response["Item"]["finished"]["BOOL"]:
            sqs.delete_message(
                QueueUrl=queue_url_inprogress,
                ReceiptHandle=message["ReceiptHandle"]
            )
            continue
        # add to queue
        sqs.send_message(
            QueueUrl=queue_url,
            # MessageGroupId="gerstein_queue",
            MessageAttributes={
                "notinprogress": {
                    "DataType": "String",
                    "StringValue": "true"
                }
            },
            MessageBody=(message["Body"])
        )
        sqs.delete_message(
            QueueUrl=queue_url_inprogress,
            ReceiptHandle=message["ReceiptHandle"]
        )
    return

dynamo = boto3.resource('dynamodb')
def truncateTable():
    table = dynamo.Table(dynamodb_table)
    tableKeyNames = [key.get("AttributeName") for key in table.key_schema]
    projectionExpression = ", ".join('#' + key for key in tableKeyNames)
    expressionAttrNames = {'#' + key: key for key in tableKeyNames}

    counter = 0
    page = table.scan(
        ProjectionExpression=projectionExpression,
        ExpressionAttributeNames=expressionAttrNames
    )
    with table.batch_writer() as batch:
        while page["Count"] > 0:
            counter += page["Count"]
            for itemKeys in page["Items"]:
                batch.delete_item(
                    Key=itemKeys
                )
            if 'LastEvaluatedKey' in page:
                page = table.scan(
                    ProjectionExpression=projectionExpression,
                    ExpressionAttributeNames=expressionAttrNames,
                    ExclusiveStartKey=page['LastEvaluatedKey']
                )
            else:
                break
