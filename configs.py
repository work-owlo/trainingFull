import boto3
import openai 
import botocore
import os
# from env import *
from botocore.exceptions import ClientError

# OPEN AI
openai.api_key = os.environ.get('OPENAI_API_KEY')


# WASABI
wasabi = boto3.resource('s3',
    endpoint_url='https://s3.us-west-1.wasabisys.com',
    aws_access_key_id=os.environ.get('WASABI_AWS_KEY'),
    aws_secret_access_key=os.environ.get('WASABI_AWS_SECRET_KEY')
)

# LOCAL DB
db_host  =  "localhost" 
db_username = "postgres"
db_password = os.environ.get('LOCAL_DB_PASSWORD')
db_name = "postgres"
mail_password = os.environ.get('MAIL_PASSWORD')
