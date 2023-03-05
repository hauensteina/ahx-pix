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
from flask import Flask, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, user_logged_out, user_logged_in, current_user
from flask.json import JSONEncoder
from flask_mail import Mail

from mod_ahx_pics.postgres import Postgres

app = Flask( __name__)

S3_BUCKET = 'ahx-pics'
# S3 folders
#ORIG_FOLDER = 'pics/orig/'
ORIG_FOLDER = 'pics_complete/'
LARGE_FOLDER = 'pics/large/'
MEDIUM_FOLDER = 'pics/medium/'
SMALL_FOLDER = 'pics/small/'

LINK_EXPIRE_HOURS = 24

# Thumbnail sizes
SMALL_THUMB_SIZE = 200
MEDIUM_THUMB_SIZE = 1000

# Local download folder
DOWNLOAD_FOLDER='downloads'

# Limit background job time
JOB_TIMEOUT=3600

IMG_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf']
VIDEO_EXTENSIONS = ['.mov', '.mp4']

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
        return JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder

app.config.update(
    DEBUG = True,
    SECRET_KEY = os.environ['AHX_FLASK_SECRET'] # For encrypted session cookie
)

app.config['MAX_CONTENT_LENGTH'] = int(1E6)

# Make some functions available in the jinja templates.
# Black Magic.
@app.context_processor
def inject_template_funcs():
    return {
        'firstname':firstname
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
Q = Queue( 'myq', connection=REDIS_CONN, default_timeout=JOB_TIMEOUT)
from mod_ahx_pics.worker_funcs import gen_thumbnails
Q.enqueue( gen_thumbnails)

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

