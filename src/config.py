import boto3
from botocore.credentials import InstanceMetadataProvider
from botocore.utils import InstanceMetadataFetcher

ami_id = 'ami-0bb5866ae41938eff'  # TODO change this to actual AMI once done
inst_template_name = 'text_recog_launch_template'
elb_target_name = 'app-target-group'
elb_name = 'text-recognition-alb'
s3_bucket_name = 'a2-photos'
manager_instance_id = 'i-0c74329b0cbbaf7ed'

using_IAM_role = False
secret_key = "INSERT SECRET KEY HERE"

# will get database ip and port from rds
worker_db_config = {
    'user': 'admin',
    'password': '7tRMVvwVFM9T4Ekzors8',
    'database': 'a1'}

manager_db_config = {
    'user': 'admin',
    'password': '7tRMVvwVFM9T4Ekzors8',
    'database': 'a2'}


def get_boto_session():
    if using_IAM_role:
        provider = InstanceMetadataProvider(iam_role_fetcher=InstanceMetadataFetcher(timeout=1000, num_attempts=2))
        print("Loading IAM Role credentials... (if this is taking a while you are probably not running inside EC2)")
        creds = provider.load()
        print("IAM credentials loaded")
        return boto3.Session(aws_access_key_id=creds.access_key, aws_secret_access_key=creds.secret_key,
                             aws_session_token=creds.token, region_name='us-east-1')
    else:
        return boto3.Session(region_name='us-east-1')
