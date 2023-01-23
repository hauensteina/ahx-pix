# /********************************************************************
# Filename: mod_carousel/__init__.py
# Author: AHN
# Creation Date: Feb, 2023
# **********************************************************************/
#
# Imports and Globals
#

from pdb import set_trace as BP

import sys,os

from flask import Flask

# Our own exception class
class AppError(Exception):
    pass

app = Flask( __name__)

#---------------------------
def log( msg, level=''):
    """ Logging. Change as needed """
    print(msg, flush=True)
 
# Endpoints for GUI
from mod_carousel import routes

