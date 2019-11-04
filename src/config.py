ami_id = 'ami-0bb5866ae41938eff'

db_config = {'user': 'root',
             'password': 'INSERT PASSWORD HERE',
             'host': '127.0.0.1',
             'database': 'a2'}

app_config = {'secret_key': 'INSERT SECRET KEY HERE',
              'max_file_size_MB': 5,
              'uploads_directory': 'uploads'}

manager_config = {'upper_threshold': 80.0,
                  'lower_threshold': 60.0,
                  'expand_ratio': 2.0,
                  'shrink_ratio': 0.5}
