ami_id = 'ami-0bb5866ae41938eff'
load_balancer_name = "text-recognition-alb"
load_balancer_target_group_name = "app-target-group"
ec2_worker_tag_key = "a2"
ec2_worker_launch_template = "text_recog_launch_template"


db_config = {'user': 'root',
             'password': 'INSERT PASSWORD HERE',
             'host': '127.0.0.1',
             'database': 'a2'}

manager_config = {'upper_threshold': 80.0,
                  'lower_threshold': 60.0,
                  'expand_ratio': 2.0,
                  'shrink_ratio': 0.5}
