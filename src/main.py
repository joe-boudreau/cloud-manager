import boto3
import mysql.connector
from src import config, autoscaler, database
from flask import render_template, redirect, url_for, request, g
from threading import Thread

from src import webapp


@webapp.before_first_request
def startup():
    # start auto scaler
    Thread(target=autoscaler.scale_workers).start()

    # connect to databases
    database.connect_to_db()

    # resize the worker pool to 1
    ec2 = boto3.resource('ec2')
    workers = ec2.instances.filter(
            Filters=[{
                'Name': 'image-id',
                'Values': [config.ami_id]},
                {
                'Name': 'instance-state-name',
                'Values': ['running']},
                    ])
    worker_count = len(list(workers))

    if worker_count > 1:
        Thread(target=autoscaler.remove_instances_from_pool, args=[
               worker_count-1, ec2, workers]).start()
    elif worker_count < 1:
        Thread(target=autoscaler.add_instances_to_pool, args=[1, ec2]).start()


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
    # get list of workers
    workers = autoscaler.get_workers()

    for worker in workers:
        worker.terminate()
    return redirect(url_for('ec2_list'))


@webapp.route('/delete-all', methods=['POST'])
# remove all EC2, S3, and RDS stuff
def delete_all():
    # remove all entries from worker database
    try:
        cursor = g._worker_db
        cursor.execute('''truncate table users''')
        cursor.execute('''truncate table images''')
        g._worker_db.commit()
    except mysql.connector.Error as error:
        print('Failed to delete records from tables: {}'.format(error))
    finally:
        cursor.close()

    # delete all workers
    workers = autoscaler.get_workers()
    for worker in workers:
        worker.terminate()

    # S3 delete everything
    s3 = boto3.resource('s3')
    s3.Bucket(config.s3_bucket_name).objects.delete()

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
    config.manager_config['upper_threshold'] = request.form.get('upper_threshold')
    config.manager_config['lower_threshold'] = request.form.get('lower_threshold')
    return redirect(url_for('ec2_list'))


@webapp.route('/change_ratio', methods=['POST'])
def change_ratio():
    config.manager_config['shrink_ratio'] = request.form.get("shrink_ratio")
    config.manager_config['expand_ratio'] = request.form.get("expand_ratio")
    return redirect(url_for('ec2_list'))
