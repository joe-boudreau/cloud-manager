from src import config
from time import sleep
import threading
from datetime import datetime, timedelta
import boto3 as boto


# reads average cpu usage across worker pool and
# grow/shrink worker pool accordingly
def scale_workers():
    # infinite loop running once every minute
    while 1:
        # get list of instances
        ec2 = boto.resource('ec2')
        workers = ec2.instances.filter(
                Filters=[{
                    'Name': 'image-id',
                    'Values': [config.ami_id]}])
        worker_count = len(list(workers))

        # cloudwatch client
        cw = boto.client('cloudwatch')

        # create the query form
        cquery = [
            {
                'Id': 'getcpu',
                'MetricStat': {
                    'Period': 60,
                    'Stat': 'Average',
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'CPUUtilization',
                        # query for all images running the ami for our webapp
                        'Dimensions': [{
                            'Name': 'ImageId', 'Value': config.ami_id
                        }, ]
                    }
                }
            }
        ]

        resp = cw.get_metric_data(
                MetricDataQueries=cquery,
                StartTime=datetime.utcnow() - timedelta(seconds=100),
                EndTime=datetime.utcnow(),
                MaxDatapoints=1)

        # CPU usage across all workers
        cpu_usage = resp['MetricDataResults'][0]['Values']

        print('DEBUG: cpu_usage={}%'.format(cpu_usage))

        # handle conditions for thresholds
        instance_delta = 0
        if cpu_usage < config.manager_config['lower_threshold']:
            instance_delta = int(config.manager_config['shrink_ratio'] * worker_count) - worker_count
            if instance_delta == 0:
                print('Warning: lower threashold reached but no instances ' +
                      'will be removed - check shrink ratio')

        elif cpu_usage > config.manager_config['upper_threshold']:
            instance_delta = int(config.manager_config['expand_ratio'] * worker_count) - worker_count
            if instance_delta == 0:
                print('Warning: upper threashold reached but no instances ' +
                      'will be added - check expand ratio')

        # start adding instances
        if instance_delta > 0:
            # TODO
            print('cpu_usage: {}%, expanding worker pool'.format(cpu_usage))

        # deregister instances and terminate
        elif instance_delta < 0:
            # TODO
            print('cpu_usage: {}%, shrinking worker pool'.format(cpu_usage))

        sleep(60)


scaler_thread = threading.Thread(target=scale_workers)
