import boto3
from src import config, autoscaler
from flask import render_template, redirect, url_for, request, flash
from threading import active_count, Thread

from src import webapp


@webapp.before_first_request
def start_autoscaler():
    Thread(target=autoscaler.scale_workers).start()


@webapp.route('/')
# Display an HTML list of all ec2 instances
def ec2_list():
    elb = boto3.client("elbv2")
    hostname = elb.describe_load_balancers(Names=[config.elb_name])['LoadBalancers'][0]['DNSName']

    return render_template("main.html", title="EZ App Manager Deluxe", hostname=hostname,
                           upper_thresh=config.manager_config['upper_threshold'],
                           lower_thresh=config.manager_config['lower_threshold'],
                           expand_ratio=config.manager_config['expand_ratio'],
                           shrink_ratio=config.manager_config['shrink_ratio'])


@webapp.route('/instances')
def get_instances():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [config.ami_id]}]).all()
    return render_template("instance_list.html", instances=instances)


@webapp.route('/stop-all', methods=['POST'])
# remove all EC2 instance
def stop_all():
    # TODO

    return redirect(url_for('ec2_list'))


@webapp.route('/delete-all', methods=['POST'])
# remove all EC2, S3, and RDS stuff
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
    lower = request.form.get('lower_threshold')
    upper = request.form.get('upper_threshold')

    if not is_number(lower) or not is_number(upper):
        flash("Error: Ensure CPU thresholds are numbers only (e.g. '50.5')")
    else:
        config.manager_config['upper_threshold'] = float(upper)
        config.manager_config['lower_threshold'] = float(lower)
    return redirect(url_for('ec2_list'))


@webapp.route('/change_ratio', methods=['POST'])
def change_ratio():
    shrink = request.form.get('shrink_ratio')
    expand = request.form.get('expand_ratio')

    if not is_number(shrink) or not is_number(expand):
        flash("Error: Ensure shrink and expand ratios are numbers only (e.g. '50.5')")
    else:
        config.manager_config['shrink_ratio'] = float(expand)
        config.manager_config['expand_ratio'] = float(shrink)
    return redirect(url_for('ec2_list'))


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
