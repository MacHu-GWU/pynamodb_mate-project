# -*- coding: utf-8 -*-

import os
from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, KeysOnlyProjection

# from pynamodb_mate import all


AWS_PROFILE = "eq_sanhe"
AWS_REGION = "us-east-1"
os.environ["AWS_DEFAULT_PROFILE"] = AWS_PROFILE
os.environ["AWS_DEFAULT_REGION"] = AWS_REGION



class MajorEmailIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "data-modeling-users-major_email"
        read_capacity_units = 10
        write_capacity_units = 5

        projection = KeysOnlyProjection()

    major_email =UnicodeAttribute(null=False, hash_key=True)


class UserModel(Model):
    class Meta:
        table_name = "data-modeling-users"
        region = AWS_REGION

    user_id = UnicodeAttribute(hash_key=True)

    major_email_index= MajorEmailIndex()
    major_email = UnicodeAttribute(null=False)


UserModel.create_table(billing_mode="PAY_PER_REQUEST")

# user = UserModel(user_id="uid-001", major_email="alice@example.com")
# user.save()
