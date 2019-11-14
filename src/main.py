import boto3
import mysql.connector
from src import config, autoscaler, database
from flask import render_template, redirect, url_for, request, g, flash
from threading import Thread

from src import webapp

boto_session = config.get_boto_session()


@webapp.before_first_request
def startup():
    database.initialize_config()

    # start auto scaler
    Thread(target=autoscaler.scale_workers).start()

    # resize the worker pool to 1
    ec2 = boto_session.resource('ec2')
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
            worker_count - 1, ec2, workers]).start()
    elif worker_count < 1:
        Thread(target=autoscaler.add_instances_to_pool, args=[1, ec2]).start()


@webapp.route('/')
# Display an HTML list of all ec2 instances
def ec2_list():
    elb = boto_session.client("elbv2")
    hostname = elb.describe_load_balancers(Names=[config.elb_name])['LoadBalancers'][0]['DNSName']

    scaler_config = database.get_manager_config()
    return render_template("main.html", title="EZ App Manager Deluxe", hostname=hostname,
                           upper_thresh=scaler_config['upper_threshold'],
                           lower_thresh=scaler_config['lower_threshold'],
                           expand_ratio=scaler_config['expand_ratio'],
                           shrink_ratio=scaler_config['shrink_ratio'])


@webapp.route('/instances')
def get_instances():
    ec2 = boto_session.resource('ec2')
    instances = ec2.instances.filter(Filters=[{'Name': 'image-id', 'Values': [config.ami_id]}]).all()
    return render_template("instance_list.html", instances=instances)


@webapp.route('/stop-all', methods=['POST'])
# remove all EC2 instance
def stop_all():
    # get list of workers
    ec2 = boto_session.resource('ec2')
    workers = ec2.instances.filter(
        Filters=[{
            'Name': 'instance-id',
            'Values': [config.ami_id]},
        ])

    for worker in workers:
        worker.terminate()

    # stop the manager as well
    manager = ec2.instances.filter(
            Filters=[{'Name': 'instance-id',
            'Values': [config.manager_instance_id]}])
    manager.stop()


@webapp.route('/delete-all', methods=['POST'])
# remove all EC2, S3, and RDS stuff
def delete_all():
    # remove all entries from worker database
    try:
        db = database.get_worker_db()
        cursor = db.cursor()
        cursor.execute('''truncate table images''')
        cursor.execute('''delete from users''')
        cursor.commit()
    except mysql.connector.Error as error:
        print('Failed to delete records from tables: {}'.format(error))
    finally:
        cursor.close()

    # delete all workers
    ec2 = boto_session.resource('ec2')
    workers = ec2.instances.filter(
        Filters=[{
            'Name': 'instance-id',
            'Values': [config.ami_id]},
        ])
    for worker in workers:
        worker.terminate()

    # S3 delete everything
    s3 = boto_session.resource('s3')
    s3.Bucket(config.s3_bucket_name).objects.delete()

    # stop the manager as well
    manager = ec2.instances.filter(
            Filters=[{'Name': 'instance-id',
            'Values': [config.manager_instance_id]}])
    manager.stop()


@webapp.route('/delete/<id>', methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):
    # create connection to ec2
    ec2 = boto_session.resource('ec2')

    ec2.Instance(id).terminate()

    return redirect(url_for('ec2_list'))


@webapp.route('/change_threshold', methods=['POST'])
def change_threshold():
    lower = request.form.get('lower_threshold')
    upper = request.form.get('upper_threshold')

    if not is_number(lower) or not is_number(upper):
        flash("Error: Ensure CPU thresholds are numbers only (e.g. '50.5')")
    else:
        database.update_manager_config(lower_threshold=float(lower), upper_threshold=float(upper))
    return redirect(url_for('ec2_list'))


@webapp.route('/change_ratio', methods=['POST'])
def change_ratio():
    shrink = request.form.get('shrink_ratio')
    expand = request.form.get('expand_ratio')

    if not is_number(shrink) or not is_number(expand):
        flash("Error: Ensure shrink and expand ratios are numbers only (e.g. '50.5')")
    else:
        database.update_manager_config(shrink_ratio=float(shrink), expand_ratio=float(expand))
    return redirect(url_for('ec2_list'))


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
