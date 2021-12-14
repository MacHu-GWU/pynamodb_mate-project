# -*- coding: utf-8 -*-

import boto3

db_client = boto3.session.Session().client("dynamodb")

# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.list_tables

res = db_client.list_tables()
for table_name in res.get("TableNames", []):
    if table_name.startswith("pynamodb-mate"):
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.delete_table
        db_client.delete_table(TableName=table_name)
