# -*- coding: utf-8 -*-

from boto_session_manager import BotoSesManager
from pynamodb_mate.tests.constants import AWS_PROFILE

bsm = BotoSesManager(profile_name=AWS_PROFILE)
res = bsm.dynamodb_client.list_tables(Limit=100)
for table_name in res.get("TableNames", []):
    if table_name.startswith("pynamodb-mate-test"):
        print(f"delete DynamoDB table {table_name!r}")
        bsm.dynamodb_client.delete_table(TableName=table_name)
