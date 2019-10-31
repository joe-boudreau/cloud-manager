from flask import render_template, redirect, url_for, request
from src import webapp

import boto3
from src import config
from datetime import datetime, timedelta
from operator import itemgetter


@webapp.route('/ec2_examples', methods=['GET'])
# Display an HTML list of all ec2 instances
def ec2_list():
    # create connection to ec2
    ec2 = boto3.resource('ec2')

#    instances = ec2.instances.filter(
#        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    instances = ec2.instances.filter().all()

    return render_template("ec2_examples/list.html", title="EC2 Instances", instances=instances)


@webapp.route('/ec2_examples/<id>', methods=['GET'])
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
    cpu_stats_fmt = [[int(stat[0].timestamp())*1000, stat[1]] for stat in cpu_stats]

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
    http_stats_fmt = [[int(stat[0].timestamp())*1000, stat[1]] for stat in http_stats]

    return render_template("ec2_examples/view.html", title="Instance Info",
                           instance=instance,
                           cpu_stats=cpu_stats_fmt,
                           http_stats=http_stats_fmt)


@webapp.route('/ec2_examples/create', methods=['POST'])
# Start a new EC2 instance
def ec2_create():
    ec2 = boto3.resource('ec2')

    ec2.create_instances(ImageId=config.ami_id, MinCount=1, MaxCount=1)

    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_examples/delete/<id>', methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    ec2.instances.filter(InstanceIds=[id]).terminate()

    return redirect(url_for('ec2_list'))
