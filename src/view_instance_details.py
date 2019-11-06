from datetime import datetime, timedelta
from operator import itemgetter

import boto3
from flask import render_template

from src import webapp


@webapp.route('/node/<id>', methods=['GET'])
# Display details about a specific instance.
def ec2_view(id):
    ec2 = boto3.resource('ec2')

    instance = ec2.Instance(id)

    return render_template("view.html", title="Worker Information",
                           instance=instance)


@webapp.route('/node/cpu/<id>', methods=['GET'])
def get_http_data(id):
    client = boto3.client('cloudwatch')
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
    return {'data': http_stats_fmt}


@webapp.route('/node/cpu/<id>', methods=['GET'])
def get_cpu_data(id):
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
    return {'data': cpu_stats_fmt}
