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
from mod_ahx_pics import app, log

IMAGE_EXTS = ['.jpg','.jpeg','.png','.JPG','.JPEG','.PNG']
VIDEO_EXTS = ['.mov','.mp4','.MOV','.MP4']

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
    parms = get_parms()
    img_files = ['defense.jpg','eiffel.jpg','elphi.jpg','robot.mov']
    img_files = [ f'static/images/{x}' for x in img_files ]
    links = []
    for i,f in enumerate(img_files):
        ext = os.path.splitext(f)[1]
        classes = " class='ahx-slide' "
        if i == 0: classes = " class='ahx-slide ahx-active' "
        if ext in VIDEO_EXTS:
            link = f"<li> <video controls {classes}>  <source src='{f}'></video> </li>"
        elif ext in IMAGE_EXTS:
            link = f"<li> <img src='{f}' {classes}> </li>"
        else:
            log(f'ERROR: unknown media extension .{ext}. Ignoring {f}')
            continue
        links.append(link)
    links = '\n'.join(links)
    return render_template( 'carousel.html',images=links )

def get_parms():
    if request.method == 'POST': # Active screen submitted a form
        parms = dict(request.form)
    else:
        parms = dict(request.args)
    # strip all input parameters    
    parms = { k:v.strip() for k, v in parms.items()}
    print(f'>>>>>>>>>PARMS:{parms}')
    return parms
