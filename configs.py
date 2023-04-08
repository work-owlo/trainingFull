import boto3
import openai 
import botocore
import os
from env import *
from botocore.exceptions import ClientError

# OPEN AI
openai.api_key = os.environ.get('OPENAI_API_KEY')


# WASABI
if os.environ.get('WASABI_AWS_KEY'):
    wasabi = boto3.resource('s3',
        endpoint_url='https://s3.us-west-1.wasabisys.com',
        aws_access_key_id=os.environ.get('WASABI_AWS_KEY'),
        aws_secret_access_key=os.environ.get('WASABI_AWS_SECRET_KEY')
    )
else:
    wasabi = boto3.resource('s3',
        endpoint_url='https://s3.us-west-1.wasabisys.com',
        aws_access_key_id='ENSP14OK2UNA3I68QPFX',
        aws_secret_access_key='xIYwur5X0QQ7yqtRVHlIT3BlbkFJ45NliM4urdSsLtsxo8uw'
    )

# LOCAL DB
db_host  =  "localhost" 
db_username = "postgres"
db_password = os.environ.get('LOCAL_DB_PASSWORD')
db_name = "postgres"
mail_password = os.environ.get('MAIL_PASSWORD')

d_id_api = "YW5zaHVscGF1bEBiZXJrZWxleS5lZHU:rvmRCOCQQ_I29fB-LU7s9"
