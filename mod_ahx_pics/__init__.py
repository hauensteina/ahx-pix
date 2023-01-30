# /********************************************************************
# Filename: mod_ahx_pics/__init__.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/
#
# Imports and Globals
#

from pdb import set_trace as BP

import sys,os
from urllib.parse import urlparse
import redis
from rq import Queue
from flask import Flask

from mod_ahx_pics.postgres import Postgres

app = Flask( __name__)

S3_BUCKET = 'ahx-pics'

# Our own exception class
#----------------------------
class AppError(Exception):
    pass

# Logging
#---------------------------
def log( msg, level=''):
    """ Logging. Change as needed """
    print(msg, flush=True)

# REDIS background worker queue 
#-----------------------------------
redis_url = os.getenv('REDIS_URL')
log('>>>>>>>>> REDIS_URL:' + redis_url)

'''
To start redis and the worker locally:
$ redis-server &
$ python worker.py  
'''
REDIS_CONN = redis.from_url( os.getenv('REDIS_URL'))
url = urlparse(redis_url)
ssl=True
if url.hostname == 'localhost': ssl=False
REDIS_CONN = redis.Redis( host=url.hostname, port=url.port, 
                          username=url.username, password=url.password, 
                          ssl=ssl, ssl_cert_reqs=None)
Q = Queue( 'myq', connection=REDIS_CONN)
from mod_ahx_pics.worker_funcs import gen_thumbnails
Q.enqueue( gen_thumbnails, args=[1,3])

# Postgres
#-------------
if 'AHX_PICS_LOCAL_DB_URL' in os.environ:
    pg = Postgres( os.environ['AHX_PICS_LOCAL_DB_URL'])
else:
    pg = Postgres( os.environ['DATABASE_URL'])

# Create DB if it does not exist
#----------------------------------
from mod_ahx_pics.create_tables import create_tables
create_tables( pg) 

# Endpoints for GUI
#---------------------
from mod_ahx_pics import routes

