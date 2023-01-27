# /********************************************************************
# Filename: mod_ahx_pics/__init__.py
# Author: AHN
# Creation Date: Feb, 2023
# **********************************************************************/
#
# Imports and Globals
#

from pdb import set_trace as BP

import sys,os
from flask import Flask

from mod_ahx_pics.postgres import Postgres

S3_BUCKET = 'ahx-pics'

# Our own exception class
class AppError(Exception):
    pass

app = Flask( __name__)

#---------------------------
def log( msg, level=''):
    """ Logging. Change as needed """
    print(msg, flush=True)

if 'AHX_PICS_LOCAL_DB_URL' in os.environ:
    pg = Postgres( os.environ['AHX_PICS_LOCAL_DB_URL'])
else:
    pg = Postgres( os.environ['DATABASE_URL'])

# Create DB if it does not exist
from mod_ahx_pics.create_tables import create_tables
create_tables( pg) 
 
# Endpoints for GUI
from mod_ahx_pics import routes

