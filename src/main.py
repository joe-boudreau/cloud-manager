from threading import Thread
from time import sleep

from flask import render_template, redirect, url_for, Response, make_response, request, flash
from src import webapp

import boto3
from src import config
from datetime import datetime, timedelta
from operator import itemgetter


@webapp.route('/')
# Display an HTML list of all ec2 instances
def ec2_list():
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    instances = ec2.instances.filter(Filters=[{'Name': 'tag-key', 'Values': ['a2']}]).all()

    return render_template("list.html", title="EZ App Manager Deluxe", instances=instances)


@webapp.route('/node/<id>', methods=['GET'])
# Display details about a specific instance.
def ec2_view(id):
    ec2 = boto3.resource('ec2')

    instance = ec2.Instance(id)

    client = boto3.client('cloudwatch')

    # CPU Utilization
    cpu = client.get_metric_statistics(
        Period=1 * 60,
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Statistics=['Average'],  # could be Sum,Maximum,Minimum,SampleCount,Average
        Dimensions=[{'Name': 'InstanceId', 'Value': id}]
    )

    cpu_stats = [[point['Timestamp'], point['Average']] for point in cpu['Datapoints']]
    cpu_stats = sorted(cpu_stats, key=itemgetter(0))
    cpu_stats_fmt = [[int(stat[0].timestamp()) * 1000, stat[1]] for stat in cpu_stats]

    # HTTP Requests per minute
    http = client.get_metric_statistics(
        Period=1 * 60,
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName='http_request',
        Namespace='custom',
        Statistics=['SampleCount'],
        Dimensions=[{'Name': 'InstanceId', 'Value': id}]
    )

    http_stats = [[point['Timestamp'], point['SampleCount']] for point in http['Datapoints']]
    http_stats = sorted(http_stats, key=itemgetter(0))
    http_stats_fmt = [[int(stat[0].timestamp()) * 1000, stat[1]] for stat in http_stats]

    return render_template("view.html", title="Instance Info",
                           instance=instance,
                           cpu_stats=cpu_stats_fmt,
                           http_stats=http_stats_fmt)


@webapp.route('/stop-all', methods=['POST'])
# Start a new EC2 instance
def stop_all():
    # TODO

    return redirect(url_for('ec2_list'))


@webapp.route('/delete-all', methods=['POST'])
# Terminate a EC2 instance
def delete_all():
    # TODO

    return redirect(url_for('ec2_list'))


@webapp.route('/delete/<id>', methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    ec2.Instance(id).terminate()

    return redirect(url_for('ec2_list'))


@webapp.route('/add-node', methods=['POST'])
# Terminate a EC2 instance
def add_node():
    ec2 = boto3.resource('ec2')
    new_instance = ec2.create_instances(LaunchTemplate={'LaunchTemplateName': 'text_recog_launch_template'}, MaxCount=1, MinCount=1)[0]
    new_id = new_instance.instance_id

    Thread(target=register_once_running, args=[new_id]).start()

    flash("New instance successfully provisioned. It will be added to the load balancer once start-up completes")
    return redirect(url_for('ec2_list'))


def register_once_running(new_id):
    session = boto3.session.Session()

    ec2 = session.resource('ec2')

    count = 0
    node = ec2.Instance(new_id)
    status = node.state['Name']
    while status != 'running' and count < 100:
        sleep(5)
        node.reload()
        status = node.state['Name']
        count = count + 1

    if count >= 100:
        print("ERROR: New instance with id: " + new_id + "unable to be added to load balancer before timeout. Current "
                                                         "node status: " + status)

    elb = session.client('elbv2')

    target_group = elb.describe_target_groups(Names=['app-target-group', ])
    if not target_group:
        print("ERROR: Target group does not exist!")

    arn = target_group['TargetGroups'][0]['TargetGroupArn']
    elb.register_targets(TargetGroupArn=arn, Targets=[{'Id': new_id, 'Port': 5000}, ])
    print("Successfully added new worker node with id: " + new_id + " to the application load balancer")


@webapp.route('/remove-node', methods=['POST'])
# Terminate a EC2 instance
def remove_node():
    # TODO

    return redirect(url_for('ec2_list'))
