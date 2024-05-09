import multiprocessing
import os

bind='localhost:5000'
#bind='localhost:80'

# these settings for logfile are not working
# set logfile in script_start_gunicorn.sh instead
logfile = '/tmp/server.log'
os.environ["GUNICORN_LOG_FILE"] = logfile

# restart after so many requests to prevent mem leaks
max_requests = 1000
max_requests_jitter = 50

pidfile = '/tmp/gunicorn.pid'

reload = True
workers = 4
