# /********************************************************************
# Filename: mod_ahx_pics/routes.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/

from pdb import set_trace as BP

import os, sys, re, json

import flask
from flask import request, render_template, flash, redirect, url_for
from functools import wraps

from mod_ahx_pics import AppError, Q
from mod_ahx_pics import app, log
from mod_ahx_pics import IMG_EXTENSIONS, VIDEO_EXTENSIONS, MEDIUM_FOLDER

from mod_ahx_pics.worker_funcs import gen_thumbnails 
import mod_ahx_pics.helpers as helpers
import mod_ahx_pics.persistence as pe
import mod_ahx_pics.gui as gui

@app.before_request
def before_request():
    if (not request.is_secure) and ('PRODUCTION_FLAG' in os.environ):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url)

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

#-----------------------
@app.route('/ttest')
def ttest():
    """ Try things here """
    return render_template( 'ttest.html', msg='ttest')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@show_error
#-------------------------------------------------
def index():
    """ Main entry point. Show heading and list of galleries """
    parms = get_parms()
    title = parms.get('title','')
    owner = parms.get('owner','')
    search_html = gui.gen_gallery_search( title, owner)
    galleries = pe.get_galleries( title, owner)
    gallery_html = gui.gen_gallery_list( galleries)
    return render_template( 'index.html', search_html=search_html, gallery_list=gallery_html)

@app.route('/index_mobile', methods=['GET', 'POST'])
@show_error
#-------------------------------------------------
def index_mobile():
    """ Main entry point for phones. """
    parms = get_parms()
    title = parms.get('title','')
    owner = parms.get('owner','')
    search_html = gui.gen_gallery_search_mobile( title, owner)
    galleries = pe.get_galleries( title, owner)
    gallery_html = gui.gen_gallery_list_mobile( galleries)
    return render_template( 'index_mobile.html', search_html=search_html, gallery_list=gallery_html)

@app.route('/gallery', methods=['GET', 'POST'])
@show_error
#-------------------------------------------------
def gallery():
    """ View a gallery """
    parms = get_parms()
    gallery_id = parms['gallery_id']
    pics = pe.get_gallery_pics( gallery_id)
    gallery = pe.get_galleries( title='', owner='', gallery_id = gallery_id)[0]
    gallery_html = gui.gen_gallery_as_table( gallery, pics)
    return render_template( 'gallery.html', content=gallery_html)

@app.route('/carousel', methods=['GET', 'POST'])
#-------------------------------------------------
def carousel():
    """ Full screen swipeable image carousel """
    parms = get_parms()
    gallery_id = parms['gallery_id']
    active_pic_id = parms['picture_id']
    images = gui.gen_carousel_images( gallery_id, active_pic_id)
    return render_template( 'carousel.html', images=images, gallery_id=gallery_id, picture_id=active_pic_id )

def get_parms():
    if request.method == 'POST': # Form submit
        parms = dict(request.form)
    else:
        parms = dict(request.args)
    # strip all input parameters    
    parms = { k:v.strip() for k, v in parms.items()}
    print(f'>>>>>>>>>PARMS:{parms}')
    return parms
