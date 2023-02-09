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
    picture_id = parms['picture_id']
    pics = pe.get_gallery_pics( gallery_id)
    img_prefix = MEDIUM_FOLDER + gallery_id + '/'
    images, s3_client =  helpers.s3_get_keys( img_prefix)
    keys = [ x['Key'] for x in images ]
    id2key = { k.split('_')[1]:k for k in keys }
    
    links = []
    s3_client = ''
    found_active = False
    for i,pic in enumerate(pics):
        key = id2key[pic['id']]
        furl,s3_client = helpers.s3_get_link( key, s3_client)
        ext = os.path.splitext(key)[1].lower()
        classes = " class='ahx-slide' "
        #if i == 0: classes = " class='ahx-slide ahx-active' "
        if pic['id'] == picture_id: 
            found_active = True
            classes = " class='ahx-slide ahx-active' "
        if ext in VIDEO_EXTENSIONS:
            link = f"<li> <video preload='none' controls {classes}>  <source src='{furl}#t=0.5'></video> </li>"
        elif ext in IMG_EXTENSIONS:
            link = f"<li> <img loading='lazy' src='{furl}' {classes}> </li>"
        else:
            log(f'ERROR: unknown media extension .{ext}. Ignoring {f}')
            continue
        links.append(link)
    if not found_active:
        links[0] = links[0].replace('ahx-slide', 'ahx-slide ahx-active')
    links = '\n'.join(links)
    return render_template( 'carousel.html', images=links, gallery_id=gallery_id, picture_id=picture_id )

def get_parms():
    if request.method == 'POST': # Form submit
        parms = dict(request.form)
    else:
        parms = dict(request.args)
    # strip all input parameters    
    parms = { k:v.strip() for k, v in parms.items()}
    print(f'>>>>>>>>>PARMS:{parms}')
    return parms
