from src import config
from time import sleep
from threading import Thread, enumerate
from datetime import datetime, timedelta
import boto3 as boto


# reads average cpu usage across worker pool and
# grow/shrink worker pool accordingly
def scale_workers():
    print('started scaler thread')
    # infinite loop running once every minute
    while 1:
        sleep(10)
        # get list of instances that are running
        ec2 = boto.resource('ec2')
        workers = ec2.instances.filter(
                Filters=[{
                    'Name': 'image-id',
                    'Values': [config.ami_id]},
                    {
                    'Name': 'instance-state-name',
                    'Values': ['running']},
                        ])
        worker_count = len(list(workers))
        print('DEBUG: {}- worker count={}'.format(datetime.now(),
              worker_count))

        # CPU usage across all workers
        cpu_usage = get_workers_cpu()

        if cpu_usage is None:
            continue  # Cloudwatch query returned no data

        # handle conditions for thresholds
        instance_delta = get_worker_delta(cpu_usage, worker_count)

        # start adding instances
        if instance_delta > 0:
            print('cpu_usage: {}%, expanding worker pool'.format(cpu_usage))
            # run on separate thread since there are blocking calls
            Thread(target=add_instances_to_pool, args=[instance_delta, ec2])\
                .start()

        # deregister instances and terminate, need to leave at least one
        elif worker_count > 1 and instance_delta < 0:
            print('cpu_usage: {}%, shrinking worker pool'.format(cpu_usage))
            Thread(target=remove_instances_from_pool, args=[-1*instance_delta,
                   ec2, workers]).start()


# sends a query to cloudwatch for worker CPU usage
def get_workers_cpu():
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

    result_values = resp['MetricDataResults'][0]['Values']
    if len(result_values) > 0:
        print('DEBUG: cpu_usage={}%'.format(result_values[0]))
        return result_values[0]
    else:
        print("DEBUG: Metric data returned no results")
        return None


# get number of workers to add/remove
def get_worker_delta(cpu_usage, worker_count):
    instance_delta = 0
    if cpu_usage < config.manager_config['lower_threshold']:
        instance_delta = int(config.manager_config['shrink_ratio'] *
                             worker_count) - worker_count
        if instance_delta == 0:
            print('Warning: lower threashold reached but no instances ' +
                  'will be removed - check shrink ratio')
        elif instance_delta * -1 > worker_count:
            instance_delta = -1 * (worker_count - 1)
            print('Warning: lower threashold reached but removing more ' +
                  'instances than available - check shrink ratio')

    elif cpu_usage > config.manager_config['upper_threshold']:
        instance_delta = int(config.manager_config['expand_ratio'] *
                             worker_count) - worker_count
        if instance_delta == 0:
            print('Warning: upper threashold reached but no instances ' +
                  'will be added - check expand ratio')

    return instance_delta


# threaded call to avoid blocking
def add_instances_to_pool(num, ec2):

    # launch the instances
    instances = ec2.create_instances(LaunchTemplate={
        'LaunchTemplateName': config.inst_template_name},
        MaxCount=num, MinCount=num)

    # register in load balancer
    elb = boto.client('elbv2')

    target_group = elb.describe_target_groups(Names=[config.elb_target_name, ])
    if not target_group:
        print("ERROR: Target group does not exist!")

    arn = target_group['TargetGroups'][0]['TargetGroupArn']

    for inst in instances:
        # wait until fully booted
        inst.wait_until_running()
        elb.register_targets(TargetGroupArn=arn, Targets=[{
            'Id': inst.instance_id, 'Port': 5000}, ])
    print('{} workers added to pool'.format(num))


# threaded call to avoid blocking
def remove_instances_from_pool(num, ec2, workers):

    elb = boto.client('elbv2')

    target_group = elb.describe_target_groups(Names=[config.elb_target_name, ])
    if not target_group:
        print("ERROR: Target group does not exist!")

    arn = target_group['TargetGroups'][0]['TargetGroupArn']

    to_deregister = list()
    to_terminate = list()
    for i in range(num):
        tempworker = list(workers)[i]
        to_terminate.append(tempworker)
        to_deregister.append({'Id': tempworker.instance_id})

    elb.deregister_targets(TargetGroupArn=arn,
                           Targets=to_deregister)
    print('{} workers removed from pool'.format(num))

    # wait for workers to finish requests before terminating
    sleep(30)

    for worker in to_terminate:
        worker.terminate()

