# /********************************************************************
# Filename: mod_ahx_pics/routes.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/

from pdb import set_trace as BP

import os, sys, re, json
from datetime import datetime, date

import flask
from flask import request, render_template, flash, redirect, url_for, session
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps

from mod_ahx_pics import AppError, Q
from mod_ahx_pics import app, log, logged_in
from mod_ahx_pics import IMG_EXTENSIONS, VIDEO_EXTENSIONS, MEDIUM_FOLDER

from mod_ahx_pics.worker_funcs import gen_thumbnails 
import mod_ahx_pics.helpers as helpers
import mod_ahx_pics.persistence as pe
import mod_ahx_pics.gui as gui
import mod_ahx_pics.auth as auth

@app.route('/ttest')
#-----------------------
def ttest():
    """ Try things here """
    return render_template( 'ttest.html', msg='ttest')

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
#-------------------------------------------------
def add_user():
    error = None
    if request.method == 'POST': # form submitted
        email = request.form['email']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']
        admin_flag = request.form.get( 'admin_flag', False)

        user = auth.User(email)
        if user.valid:
            error = 'User exists' 
        elif len(password) < 8:
            error = 'Password must have 8 or more characters'
        if error:
            return render_template( 'add_user.html', error=error)
        # All is well, create user
        today = date.today()
        data = { 
            'email':email
            ,'fname':fname
            ,'lname':lname
            ,'admin_flag':admin_flag
            ,'create_date':today
            ,'change_date':today
        }   
        user.create_user(data, password)
        flash('User created.')
        return redirect( url_for('index'))
    else: # Initial hit
        return render_template( 'add_user.html', error=error)

@app.route('/carousel', methods=['GET', 'POST'])
#-------------------------------------------------
def carousel():
    """ Full screen swipeable image carousel """
    parms = get_parms()
    gallery_id = parms['gallery_id']
    active_pic_id = parms['picture_id']
    images = gui.gen_carousel_images( gallery_id, active_pic_id)
    return render_template( 'carousel.html', images=images, gallery_id=gallery_id, picture_id=active_pic_id )

@app.route('/gallery', methods=['GET', 'POST'])
#@show_error
#-------------------------------------------------
def gallery():
    """ View a gallery on a computer """
    parms = get_parms()
    gallery_id = parms['gallery_id']
    pics = pe.get_gallery_pics( gallery_id)
    gallery = pe.get_galleries( title='', owner='', gallery_id = gallery_id)[0]
    gallery_html = gui.gen_gallery( gallery, pics)
    return render_template( 'gallery.html', content=gallery_html)

@app.route('/gallery_mobile', methods=['GET', 'POST'])
#@show_error
#-------------------------------------------------
def gallery_mobile():
    """ View a gallery on a phone """
    parms = get_parms()
    gallery_id = parms['gallery_id']
    pics = pe.get_gallery_pics( gallery_id)
    gallery = pe.get_galleries( title='', owner='', gallery_id = gallery_id)[0]
    gallery_html = gui.gen_gallery_mobile( gallery, pics)
    return render_template( 'gallery_mobile.html', content=gallery_html)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
#@show_error
#-------------------------------------------------
def index():
    """ Main entry point. Show heading and list of galleries """
    session['is_mobile'] = False
    parms = get_parms()
    title = parms.get('title','')
    owner = parms.get('owner','')
    search_html = gui.gen_gallery_search( title, owner)
    galleries = pe.get_galleries( title, owner)
    gallery_html = gui.gen_gallery_list( galleries)
    res = render_template( 'index.html', search_html=search_html, gallery_list=gallery_html)
    return res

@app.route('/index_mobile', methods=['GET', 'POST'])
#@show_error
#-------------------------------------------------
def index_mobile():
    """ Main entry point for phones. """
    session['is_mobile'] = True
    parms = get_parms()
    title = parms.get('title','')
    owner = parms.get('owner','')
    search_html = gui.gen_gallery_search_mobile( title, owner)
    galleries = pe.get_galleries( title, owner)
    gallery_html = gui.gen_gallery_list_mobile( galleries)
    return render_template( 'index.html', search_html=search_html, gallery_list=gallery_html)

@app.route('/login', methods=['GET', 'POST'])
#----------------------------------------------
def login():
    error = None
    if request.method == 'POST':
        password = request.form['password']
        username = request.form['login'].upper()
        user = auth.User( username)
        if user.valid and user.password_matches( password):
            login_user(user, remember=False)
            next_page = request.args.get('next') # Magically populated to where we came from
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            error = 'Invalid credentials'
    return render_template('login.html', error=error, no_links=True)

@app.route("/logout")
@login_required
#--------------------
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/reset_request', methods=['GET', 'POST'])
#--------------------------------------------------------
def reset_request():
    if logged_in():
        return redirect( url_for('index'))
    if request.method == 'POST':
        user = auth.User( request.form['email'])
        if not user.valid:
            flash( 'User does not exist', 'danger')
            return redirect( url_for('reset_request'))
        send_reset_email( user)
        flash( tr('reset_email_sent'), 'info')
        return redirect(url_for('login')) 
    return render_template('reset_request.html', title='Reset Password')


# Utility funcs
##################

#------------------
def get_parms():
    if request.method == 'POST': # Form submit
        parms = dict(request.form)
    else:
        parms = dict(request.args)
    # strip all input parameters    
    parms = { k:v.strip() for k, v in parms.items()}
    print(f'>>>>>>>>>PARMS:{parms}')
    return parms

#-----------------------------
def show_error(f):
    """  Show errors in the browser """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            tb = exc_tb.tb_next.tb_next
            if not tb: tb = exc_tb.tb_next
            frame = str(tb.tb_frame)
            err = str(e)
            return flask.escape( f'''EXCEPTION: {err} {frame}''')
    return decorated

@app.before_request
#-----------------------
def before_request():
    if (not request.is_secure) and ('PRODUCTION_FLAG' in os.environ):
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url)

