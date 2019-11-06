import boto3
from src import config
from flask import render_template, redirect, url_for, request

from src import webapp


@webapp.route('/')
# Display an HTML list of all ec2 instances
def ec2_list():

    elb = boto3.client("elbv2")
    hostname = elb.describe_load_balancers(Names=["text-recognition-alb"])['LoadBalancers'][0]['DNSName']

    return render_template("main.html", title="EZ App Manager Deluxe", hostname=hostname,
                           upper_thresh=config.manager_config['upper_threshold'],
                           lower_thresh=config.manager_config['lower_threshold'],
                           expand_ratio=config.manager_config['expand_ratio'],
                           shrink_ratio=config.manager_config['shrink_ratio'])


@webapp.route('/instances')
def get_instances():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'tag-key', 'Values': ['a2']}]).all()
    return render_template("instance_list.html", instances=instances)


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
