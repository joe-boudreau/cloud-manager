ami_id = 'ami-0bb5866ae41938eff'  # TODO change this to actual AMI once done
inst_tag_key_value = 'a2'
inst_template_name = 'text-rec-v1'
elb_target_name = 'text-recognition-workers'
elb_name = 'text-recognition'
s3_bucket_name = 'my-bucket'

# will get database ip and port from rds
worker_db_config = {
    'user': 'admin',
    'password': 'admin123',
    'database': 'a1'}

manager_db_config = {
    'user': 'admin',
    'password': 'admin123',
    'database': 'a2'}

manager_config = {'upper_threshold': 80.0,
                  'lower_threshold': 40.0,
                  'expand_ratio': 2.0,
                  'shrink_ratio': 0.5}
