# /********************************************************************
# Filename: mod_ahx_pics/routes.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/

from pdb import set_trace as BP

import os, sys, re, json, random
from datetime import datetime, date
import shortuuid

import flask
from flask import request, render_template, flash, redirect, url_for, session, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from functools import wraps
from itsdangerous import TimestampSigner, SignatureExpired

from mod_ahx_pics import AppError, Q, pg
from mod_ahx_pics import app, log, logged_in
from mod_ahx_pics import IMG_EXTENSIONS, VIDEO_EXTENSIONS, MEDIUM_FOLDER, UPLOAD_FOLDER

from mod_ahx_pics.worker_funcs import gen_thumbnails 
import mod_ahx_pics.helpers as helpers
import mod_ahx_pics.persistence as pe
import mod_ahx_pics.gui as gui
import mod_ahx_pics.auth as auth
from  mod_ahx_pics.helpers import html_tag as H
from mod_ahx_pics import worker_funcs as wf


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
    data = {}
    if request.method == 'POST': # form submitted
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']
        admin_flag = request.form.get( 'admin_flag', False)

        today = date.today()
        iid = shortuuid.uuid() 
        data = { 
            'email':email
            ,'username':username
            ,'fname':fname
            ,'lname':lname
            ,'admin_flag':admin_flag
            ,'create_date':today
            ,'change_date':today
        }   
        user = auth.User(email)
        if user.valid:
            error = 'User exists' 
        elif len(password) < 8:
            error = 'Password must have 8 or more characters'
        if error:
            return render_template( 'add_user.html', error=error, **data)
        # All is well, create user
        try:
            user.create_user(data, password)
        except Exception as e:
            return render_template( 'add_user.html', error=str(e), **data)
            
        flash( f'''User {data['username']} created.''')
        return redirect( url_for('index'))
    else: # Initial hit
        return render_template( 'add_user.html', error=error, **data)

@app.route('/carousel', methods=['GET', 'POST'])
@login_required
#-------------------------------------------------
def carousel():
    """ Full screen swipeable image carousel """
    parms = get_parms()
    gallery_id = parms['gallery_id']
    active_pic_id = parms['picture_id']
    images = gui.gen_carousel_images( gallery_id, active_pic_id)
    return render_template( 'carousel.html', images=images, gallery_id=gallery_id, picture_id=active_pic_id )

@app.route('/delete_gallery', methods=['GET', 'POST'])
@login_required
#-------------------------------------------------------------
def delete_gallery():
    """ Delete a gallery (prompt for confirmation first) """
    home = 'index_mobile' if session['is_mobile'] else 'index'
    parms = get_parms()
    if request.method == 'POST': # form submitted
        if 'btn_no' in parms:
            flash('Gallery not deleted')
            return redirect( url_for(home))
        gallery_id = parms['question_parm']        
        pg.run( f''' update gallery set deleted_flag = true where id = '{gallery_id}' ''')
        flash('Gallery deleted')
        return redirect( url_for(home))
    else:
        gallery_id = parms['gallery_id']
        gallery = pe.get_galleries( title='', owner='', gallery_id = gallery_id)[0]
        if gallery['username'] != current_user.data['username']:
            error = 'You do not own this gallery.'
            return render_template('index.html', error=error)
        return render_template('question.html', 
                               msg=f'''Do you really want to delete gallery '{gallery['title']}'?
                                <div style='color:red;'>You cannot undo the delete!</div>''', 
                               question_parm=gallery_id, no_links=True)

@app.route('/download_img', methods=['GET'])
@login_required
#-------------------------------------------
def download_img():
    """
    Return original full resolution image as attachment.
    """
    parms = get_parms()
    slide_src = parms['slide_src']
    # 'https://ahx-pics.s3.amazonaws.com/pics/medium/423/med_6865_423_0.jpeg?...' -> 6865
    picture_id = slide_src.split('?')[0].split('_')[1]
    gallery_id = slide_src.split('?')[0].split('_')[2]
    gallery_id = os.path.splitext(gallery_id)[0]
    s3_path = helpers.s3_path_for_pic( gallery_id, picture_id, 'large') 
    local_fname = helpers.s3_download_file( s3_path)
    ext = os.path.splitext(local_fname)[1]
    fh = open( local_fname, 'br')
    resp = send_file( fh, as_attachment=True, download_name=f'{picture_id}_{gallery_id}{ext}')
    try:
        os.remove( local_fname)
    except:
        pass
    return resp

@app.route('/download_file', methods=['GET'])
@login_required
#-------------------------------------------
def download_file():
    """
    Download a file from s3. Used for non-image files
    """
    parms = get_parms()
    fname = parms['fname']
    orig_fname = parms['orig_fname']
    local_fname = helpers.s3_download_file(fname)
    ext = os.path.splitext(local_fname)[1]
    fh = open( local_fname, 'br')
    resp = send_file( fh, as_attachment=True, download_name=f'{os.path.split(orig_fname)[1]}')
    try:
        os.remove( local_fname)
    except:
        pass
    return resp

@app.route('/edit_info', methods=['GET', 'POST'])
@login_required
#---------------------------------------------------
def edit_info():
    error = None
    if request.method == 'POST': # form submitted
        email = request.form['email'].strip()
        fname = request.form['fname'].strip()
        lname = request.form['lname'].strip()

        user = auth.User(email)
        if not user.valid:
            error = 'User does not exist' 
        elif len(fname) < 1:
            error = 'First name is required' 
        elif len(lname) < 1:
            error = 'Last name is required' 
        if error:
            return render_template( 'edit_info.html', error=error, no_links=True)

        # All is well, update user
        user.data['fname'] = fname
        user.data['lname'] = lname
        user.update_db()
        flash('User info updated.')
        return redirect( url_for('index'))
    else: # Initial hit
        user = current_user
        if not user.valid:
            error = 'User does not exist' 
            return render_template( 'edit_info.html', error=error, no_links=True)
        return render_template( 'edit_info.html', error=error, no_links=True
                               ,lname=user.data['lname']
                               ,fname=user.data['fname']
                               ,username=user.data['username']
                               ,email=user.data['email']
                               )

@app.route('/gallery', methods=['GET', 'POST'])
@login_required
#@show_error
#-------------------------------------------------
def gallery():
    """ View a gallery on a computer """
    parms = get_parms()
    gallery_id = parms['gallery_id']
    pics = pe.get_gallery_pics( gallery_id)
    gallery = pe.get_galleries( title='', owner='', gallery_id = gallery_id)[0]
    session['gallery_id'] = gallery['id']
    session['gallery_title'] = gallery['title']
    gallery_html = gui.gen_gallery( gallery, pics)
    mylinks = ''
    # I can edit my own galleries only
    if current_user.data['username'] == gallery['username']:
        mylinks = f'''
        <div style='margin-left:50px;margin-bottom:10px;width:100%;'>
          <a href="{url_for('upload_pics')}">Upload Pics</a> &nbsp;   
          <a href="{url_for('index')}">Edit Title</a> &nbsp;   
          <a href="{url_for('index')}">Edit Pics</a> &nbsp;   
          <a href="{url_for('delete_gallery', gallery_id=gallery_id )}">Delete</a> &nbsp;   
        </div>
        '''
    return render_template( 'gallery.html', content=gallery_html, custom_links=mylinks, no_links=True)

@app.route('/gallery_mobile', methods=['GET', 'POST'])
@login_required
#@show_error
#-------------------------------------------------
def gallery_mobile():
    """ View a gallery on a phone """
    parms = get_parms()
    gallery_id = parms['gallery_id']
    pics = pe.get_gallery_pics( gallery_id)
    gallery = pe.get_galleries( title='', owner='', gallery_id = gallery_id)[0]
    session['gallery_id'] = gallery['id']
    session['gallery_title'] = gallery['title']
    gallery_html = gui.gen_gallery_mobile( gallery, pics)
    mylinks = ''
    return render_template( 'gallery_mobile.html', content=gallery_html, custom_links=mylinks, no_links=True)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@login_required
#-------------------------------------------------
def index():
    """ Main entry point. Show heading and list of galleries """
    if session.get('is_mobile',''): return redirect( url_for('index_mobile'))
    parms = get_parms()
    title = parms.get('title','')
    owner = parms.get('owner','')
    all_pics_flag = parms.get('all_pics_flag', session.get('all_pics_flag',False)) in ('True', True)
    session['all_pics_flag'] = all_pics_flag

    if 'btn_sort' in parms: 
        sort_col = parms['btn_sort']
        sort_order = parms['sort_order'] # asc or desc
        next_order = 'asc' if sort_order == 'desc' else 'desc'
    else: # Initial index hit
        sort_col = 'Date'
        sort_order = 'desc'
        next_order = 'asc'

    search_html = gui.gen_gallery_search( title, owner)
    columns = { 'Title':'title', 'Date':'create_date', 'Owner':'username'} 
    if all_pics_flag:
        galleries = pe.get_galleries( title, owner, order_by=f''' lower({columns[sort_col]}::text) {sort_order} ''' )
    else:
        galleries = pe.get_my_galleries( title, order_by=f''' lower({columns[sort_col]}::text) {sort_order} ''' )
        
    gallery_html = gui.gen_gallery_list( galleries, sort_col, next_order)
    res = render_template( 'index.html', search_html=search_html, 
                           gallery_list=gallery_html, all_pics_flag=all_pics_flag)
    return res

@app.route('/index_mobile', methods=['GET', 'POST'])
@login_required
#@show_error
#-------------------------------------------------
def index_mobile():
    """ Main entry point for phones. """
    #session['is_mobile'] = True
    #log('>>>>>>>>>>>>>>>>seesion is_mobile true')
    if not session.get('is_mobile',''): return redirect( url_for('index'))
    parms = get_parms()
    title = parms.get('title','')
    owner = parms.get('owner','')
    all_pics_flag = parms.get('all_pics_flag', session.get('all_pics_flag',False)) in ('True', True)
    session['all_pics_flag'] = all_pics_flag

    if 'btn_sort' in parms: 
        sort_col = parms['btn_sort']
        sort_order = parms['sort_order'] # asc or desc
        next_order = 'asc' if sort_order == 'desc' else 'desc'
    else: # Initial index hit
        sort_col = 'Date'
        sort_order = 'desc'
        next_order = 'asc'

    search_html = gui.gen_gallery_search_mobile( title, owner)
    columns = { 'Title':'title', 'Date':'create_date', 'Owner':'username'} 
    if all_pics_flag:
        galleries = pe.get_galleries( title, owner, order_by=f''' lower({columns[sort_col]}::text) {sort_order} ''' )
    else:
        galleries = pe.get_my_galleries( title, order_by=f''' lower({columns[sort_col]}::text) {sort_order} ''' )
    gallery_html = gui.gen_gallery_list_mobile( galleries, sort_col, next_order)
    res = render_template( 'index.html', search_html=search_html, 
                           gallery_list=gallery_html, all_pics_flag=all_pics_flag)
    return res

@app.route('/login', methods=['GET', 'POST'])
#----------------------------------------------
def login():
    error = None
    username = ''
    if request.method == 'POST':
        password = request.form['password']
        username = request.form['login']
        user = auth.User( username)
        if user.valid and user.password_matches( password):
            login_user(user, remember=False)
            next_page = request.args.get('next') # Magically populated to where we came from
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            error = 'Invalid credentials'
    return render_template('login.html', username=username, error=error, no_links=True)

@app.route("/logout")
@login_required
#--------------------
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/new_gallery", methods=['GET', 'POST'])
@login_required
#-----------------------------------------------------
def new_gallery():
    error = None
    data = {}
    if request.method == 'POST': # form submitted
        title = request.form['title']
        private_flag = request.form.get( 'private_flag', False)

        today = date.today()
        iid = shortuuid.uuid()
        data = { 
            'id':iid
            ,'username':current_user.data['username']
            ,'title':title
            ,'private_flag':private_flag
            ,'create_date':today
            ,'change_date':today
        }           
        try:
            pg.insert( 'gallery',[data])
        except Exception as e:
            return render_template( 'new_gallery.html', error=str(e), **data)
            
        flash( f'''Gallery created.''')
        return redirect( url_for('index'))
    else: # Initial hit
        return render_template( 'new_gallery.html', error=error, **data)

@app.route('/reset_request', methods=['GET', 'POST'])
#--------------------------------------------------------
def reset_request():
    if logged_in():
        return redirect( url_for('index'))
    if request.method == 'POST':
        user = auth.User( request.form['email'])
        if not user.valid:
            flash( 'User does not exist', 'error')
            return redirect( url_for('reset_request'))
        helpers.send_reset_email( user)
        flash( 'Reset email sent')
        return redirect(url_for('login')) 
    return render_template('reset_request.html', title='Reset Password', no_links=True)

@app.route('/reset_token', methods=['GET', 'POST'])
#----------------------------------------------------------------
def reset_token():
    if logged_in():
        return redirect( url_for('index'))
    parms = get_parms()

    if 'password' in parms or 'error' in parms: # User entered password
        
        user_id = parms['user_id']
        password = parms['password']
        confpwd = parms['confpwd']
        error=''

        user = auth.User( user_id)
        if not user.valid:
            flash( 'User does not exist', 'error')
            return redirect( url_for('login'))
            
        if len(password) < 8:
            error = 'Password must have 8 or more characters'
        elif password != confpwd:
            error = 'Passwords must match'
        if error:
            return render_template( 'reset_token.html', error=error, password=password, confpwd=confpwd, user_id=user_id )

        user.set_password( password)
        flash( 'Password updated')
        return redirect(url_for('login'))

    else: # Prompt user to enter password
        token = parms['token']
        s = TimestampSigner( app.config['SECRET_KEY'])
        try:
            user_id = s.unsign(token, max_age = 3600 * 24 )
        except SignatureExpired as e:
            flash( 'Reset token too old', 'error')
            return redirect( url_for('index'))

        user_id = user_id.decode('utf8')
        user = auth.User( user_id)
        if not user.valid:
            flash( f'Invalid user {user_id}', 'error')
            return redirect( url_for('reset_request'))
        return render_template('reset_token.html', user_id=user_id)

@app.route("/set_mobile", methods=['GET','POST'])
#---------------------------------------------------
def set_mobile():
    parms = get_parms()
    url = parms['url']
    mobile_flag = True if parms['mobile_flag'].lower() == 'true' else False
    session['is_mobile'] = mobile_flag
    return redirect(url)

@app.route("/upload_pics", methods=['GET', 'POST'])
@login_required
#-----------------------------------------------------
def upload_pics():
    error = None
    data = {}
    data['gallery_title'] = session['gallery_title']
    gallery_id = session['gallery_id']
    data['gallery_id'] = gallery_id
    if request.method == 'POST': # Upload button clicked
        gallery_page = 'gallery_mobile' if session.get('is_mobile','') else 'gallery'
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('Please select a file', 'error')
            return redirect(request.url)
        if file: # and allowed_file(file.filename):
            #BP()
            tempfolder = f'''{UPLOAD_FOLDER}/{shortuuid.uuid()}'''
            os.mkdir( tempfolder)            
            fname = secure_filename(file.filename)
            fname = f'''{tempfolder}/{fname}'''
            # This will work with one dyno. To scale, the file would have to move to S3.
            file.save(fname)
            Q.enqueue( wf.add_new_images, fname, gallery_id)
            #flash( f'''File {file.filename} was uploaded and is processing.''') 
            #return redirect( url_for( gallery_page, gallery_id=session['gallery_id']))
            return 'ok'
    else: # Initial hit
        return render_template( 'upload_pics.html', error=error, **data, no_links=True )

# Utility funcs
##################

#------------------
def get_parms():
    if request.method == 'POST': # Form submit
        parms = dict(request.form)
    else:
        parms = dict(request.args)
    # strip all parameters    
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

