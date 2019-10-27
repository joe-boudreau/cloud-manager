from src import webapp


@webapp.route('/')
def hello_world():
    return 'Hello World!'
