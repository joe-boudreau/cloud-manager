ami_id = 'ami-0bb5866ae41938eff'  # TODO change this to actual AMI once done
inst_template_name = 'text-rec-v1'
elb_target_name = 'text-recognition-workers'
elb_name = 'text-recognition'
s3_bucket_name = 'my-bucket'

secret_key = "INSERT SECRET KEY HERE"

# will get database ip and port from rds
worker_db_config = {
    'user': 'admin',
    'password': 'admin123',
    'database': 'a1'}

manager_db_config = {
    'user': 'admin',
    'password': 'admin123',
    'database': 'a2'}
