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

    return render_template("list.html", title="EZ App Manager Deluxe", instances=instances, hostname=hostname)


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