from threading import Thread

import boto3
from flask import flash, redirect, url_for

from src import webapp, config

boto_session = config.get_boto_session()

@webapp.route('/add-node', methods=['POST'])
# Terminate a EC2 instance
def add_node():
    ec2 = boto_session.resource('ec2')
    new_instance = ec2.create_instances(LaunchTemplate={'LaunchTemplateName': config.inst_template_name}, MaxCount=1, MinCount=1)[0]
    new_id = new_instance.instance_id

    Thread(target=register_once_running, args=[new_id]).start()

    flash("New worker successfully provisioned. It will be registered with the load balancer once start-up completes")
    return redirect(url_for('ec2_list'))


def register_once_running(new_id):

    ec2 = boto_session.resource('ec2')
    ec2.Instance(new_id).wait_until_running()  # this method blocks until the instance is running

    elb = boto_session.client('elbv2')

    target_group = elb.describe_target_groups(Names=[config.elb_target_name, ])
    if not target_group:
        print("ERROR: Target group does not exist!")

    arn = target_group['TargetGroups'][0]['TargetGroupArn']
    elb.register_targets(TargetGroupArn=arn, Targets=[{'Id': new_id, 'Port': 5000}, ])
    print("Successfully added new worker node with id: " + new_id + " to the application load balancer")


@webapp.route('/remove-node', methods=['POST'])
# Terminate a EC2 instance
def remove_node():
    ec2 = boto_session.resource('ec2')

    nodes = ec2.instances.filter(
            Filters=[{
                'Name': 'image-id',
                'Values': [config.ami_id]},
                {
                'Name': 'instance-state-name',
                'Values': ['running']},
                    ]).all()
    list(nodes)[0].terminate()  # just kill a random one

    flash("One worker successfully terminated")
    return redirect(url_for('ec2_list'))
