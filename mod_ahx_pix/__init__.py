# /********************************************************************
# Filename: mod_ahx_pix/__init__.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/
#
# Imports and Globals
#

from pdb import set_trace as BP

import os
from urllib.parse import urlparse
import redis
import random
from rq import Queue
from flask import Flask, session, json
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask.json import JSONEncoder

from flask_mail import Mail

from mod_ahx_pix.postgres import Postgres

app = Flask( __name__)

S3_BUCKET = 'ahx-pics'
# S3 folders
#ORIG_FOLDER = 'pics/orig/'
#ORIG_FOLDER = 'pics_complete/'
LARGE_FOLDER = 'pics/large/'
MEDIUM_FOLDER = 'pics/medium/'
SMALL_FOLDER = 'pics/small/'

LINK_EXPIRE_HOURS = 24

# Thumbnail sizes
SMALL_THUMB_SIZE = 200
MEDIUM_THUMB_SIZE = 1000

# Local download folder (stuff from S3, during thumb generation)
DOWNLOAD_FOLDER='downloads'
# Local upload folder (user uploads)
UPLOAD_FOLDER='uploads'

# Limit background job time
JOB_TIMEOUT=3600

IMG_EXTENSIONS = ['.png', '.jpg', '.jpeg','.heic','.svg', '.webp']
VIDEO_EXTENSIONS = ['.mov', '.mp4']
MEDIA_EXTENSIONS = IMG_EXTENSIONS + VIDEO_EXTENSIONS

FFMPEG_COMPRESSOR = 'ffmpeg -i @IN  -c:v libx264 -crf 28 @OUT'
FFMPEG_VIDEO_THUMB = 'ffmpeg -i @IN  -ss 00:00:01.000 -vframes 1 @OUT'

FFMPEG_RESIZE_IMG = 'ffmpeg -i @IN -q:v 2 -vf "scale=@MAXW:-1@ROT" @OUT'

# Our own exception class
#----------------------------
class AppError(Exception):
    pass

# Logging
#---------------------------
def log( msg, level=''):
    """ Logging. Change as needed """
    print(msg, flush=True)

# Make sure dates are serialized as yyyy-mm-dd by flask.jsonify (for our API endpoints)
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime.date):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return json.JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder

app.config.update(
    DEBUG = True,
    SECRET_KEY = os.environ['AHX_FLASK_SECRET'] # For encrypted session cookie
)

app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024 

# Make some functions available in the jinja templates.
# Black Magic.
@app.context_processor
def inject_template_funcs():
    return {
        'firstname':firstname
        ,'f_username':f_username
        ,'getenv':getenv
        ,'is_admin':is_admin
        ,'is_mobile':is_mobile
        ,'logged_in':logged_in
        ,'rrand':rrand
    }   

def firstname():
    res = ''
    try:
        res = current_user.data['fname']
    except:
        pass
    return res

def f_username():
    res = ''
    try:
        res = current_user.data['username']
    except:
        pass
    return res

def getenv(varname):
    return os.environ[varname]

def is_admin():
    try:
        return current_user.data['admin_flag']
    except:
        return False

def is_mobile():
    return session.get('is_mobile', False)

def logged_in():
    return current_user.is_authenticated

def rrand():
    return str(random.uniform(0,1))

bcrypt = Bcrypt( app) # Our password hasher
login_manager = LoginManager( app)
login_manager.login_view = 'login' # The route if you should be logged in but aren't
login_manager.login_message = ''

app.config['MAIL_SERVER'] = 'mail.hover.com'
app.config['MAIL_PORT'] = 587 
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)

# REDIS background worker queue 
#-----------------------------------
#redis_url = os.getenv('REDIS_URL')
if os.getenv('PRODUCTION_FLAG'):
    #redis_url = os.getenv('REDIS_TLS_URL')
    redis_url = os.getenv('REDIS_URL')
else:
    #redis_url = os.getenv('PIX_REDIS_URL')  # remote
    redis_url = os.getenv('REDIS_URL')  # local

log('>>>>>>>>> REDIS_URL:' + redis_url)

'''
To start redis and the worker locally:
$ redis-server &
$ python worker.py  
'''

url = urlparse(redis_url)
ssl=True
if url.hostname == 'localhost': ssl=False
REDIS_CONN = redis.Redis( host=url.hostname, port=url.port, 
                          username=url.username, password=url.password, 
                          ssl=ssl, ssl_cert_reqs=None)

Q = Queue( 'high',connection=REDIS_CONN, default_timeout=JOB_TIMEOUT)

# Postgres
#-------------
if 'AHX_PIX_LOCAL_DB_URL' in os.environ:
    pg = Postgres( os.environ['AHX_PIX_LOCAL_DB_URL']) # local
    #pg = Postgres( os.environ['PIX_DB_URL']) # remote
else:
    pg = Postgres( os.environ['DATABASE_URL'])

# Create DB if it does not exist
#----------------------------------
from mod_ahx_pix.create_tables import create_tables
create_tables( pg) 

# Endpoints for GUI
#---------------------
from mod_ahx_pix import routes

from mod_ahx_pix.worker_funcs import gen_thumbnails
#Q.enqueue( gen_thumbnails)
Q.empty()
