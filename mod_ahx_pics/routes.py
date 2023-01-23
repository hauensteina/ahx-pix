# /********************************************************************
# Filename: mod_carousel/routes.py
# Author: AHN
# Creation Date:Feb, 2023
# **********************************************************************/
#

from pdb import set_trace as BP

import os, sys, re, json

from flask import request, render_template, flash, redirect, url_for

from mod_carousel import AppError
from mod_carousel import app

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
    if request.method == 'POST': # Active screen submitted a form
        parms = dict(request.form)
    else:
        parms = dict(request.args)
    # strip all input parameters    
    parms = { k:v.strip() for k, v in parms.items()}
    print(f'>>>>>>>>>PARMS:{parms}')

    '''
    active_tab = parms.get('_active_tab','')
    active_screen = parms.get('_active_screen','')
    try:
        tab_html, rredirect = tabgen.gen_html( active_tab, active_screen, parms)
    except AppError as e:
        if 'bad_or_expired_token' in str(e):
            return redirect( url_for('logout'))
        else:
            raise
    if rredirect: return rredirect
    '''

    return render_template( 'index.html')

