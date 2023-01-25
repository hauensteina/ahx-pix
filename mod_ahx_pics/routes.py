# /********************************************************************
# Filename: mod_carousel/routes.py
# Author: AHN
# Creation Date:Feb, 2023
# **********************************************************************/
#

from pdb import set_trace as BP

import os, sys, re, json

from flask import request, render_template, flash, redirect, url_for

from mod_ahx_pics import AppError
from mod_ahx_pics import app

@app.before_request
def before_request():
    if (not request.is_secure) and ('PRODUCTION_FLAG' in os.environ):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url)

@app.route('/ttest')
def ttest():
    """ Try things here """
    return render_template( 'ttest.html', msg='ttest')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def index():
    """ Main entry point """
    parms = get_parms()
    return render_template( 'index.html')

@app.route('/carousel', methods=['GET', 'POST'])
def carousel():
    """ Full screen swipeable image carousel """
    images = ['defense.jpg','eiffel.jpg','elphi.jpg','robot.mov']
    images = [ f'static/images/{x}' for x in images ] # @@@ cont here
        
    parms = get_parms()
    return render_template( 'carousel.html',images=images )



def get_parms():
    if request.method == 'POST': # Active screen submitted a form
        parms = dict(request.form)
    else:
        parms = dict(request.args)
    # strip all input parameters    
    parms = { k:v.strip() for k, v in parms.items()}
    print(f'>>>>>>>>>PARMS:{parms}')
    return parms
