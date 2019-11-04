from flask import render_template, redirect, url_for, request
from src import webapp

import boto3
from src import config
from datetime import datetime, timedelta
from operator import itemgetter
from threading import Thread

import boto3
from flask import render_template, redirect, url_for, flash

from src import webapp


@webapp.route('/')
# Display an HTML list of all ec2 instances
def ec2_list():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'tag-key', 'Values': ['a2']}]).all()

    elb = boto3.client("elbv2")
    hostname = elb.describe_load_balancers(Names=["text-recognition-alb"])['LoadBalancers'][0]['DNSName']

    return render_template(
        "list.html", title="EZ App Manager Deluxe", instances=instances,
        upper_thresh=config.manager_config['upper_threshold'],
        lower_thresh=config.manager_config['lower_threshold'],
        expand_ratio=config.manager_config['expand_ratio'],
        shrink_ratio=config.manager_config['shrink_ratio'])


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

    # S3 delete everything in `my-bucket`
    s3 = boto3.resource('s3')
    s3.Bucket('my-bucket').objects.delete()

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
    # TODO

    return redirect(url_for('ec2_list'))


@webapp.route('/remove-node', methods=['POST'])
# Terminate a EC2 instance
def remove_node():
    # TODO

    return redirect(url_for('ec2_list'))


@webapp.route('/change_threshold', methods=['POST'])
def change_threshold():
    config.manager_config['upper_threshold'] = request.form.get("upper threshold")
    config.manager_config['lower_threshold'] = request.form.get("lower threshold")
    return redirect(url_for('ec2_list'))


@webapp.route('/change_ratio', methods=['POST'])
def change_ratio():
    config.manager_config['shrink_ratio'] = request.form.get("shrink ratio")
    config.manager_config['expand_ratio'] = request.form.get("expand ratio")
    return redirect(url_for('ec2_list'))
