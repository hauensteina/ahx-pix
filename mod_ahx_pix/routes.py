# /********************************************************************
# Filename: mod_ahx_pix/routes.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/

from pdb import set_trace as BP

import os, sys, json
from datetime import date
import uuid
import shutil

import flask
from flask import request, render_template, flash, redirect, url_for, session, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from functools import wraps
from itsdangerous import TimestampSigner, SignatureExpired

from mod_ahx_pix import Q, pg
from mod_ahx_pix import app, log, logged_in
from mod_ahx_pix import UPLOAD_FOLDER

import mod_ahx_pix.helpers as helpers
import mod_ahx_pix.persistence as pe
import mod_ahx_pix.gui as gui
import mod_ahx_pix.auth as auth
from  mod_ahx_pix.helpers import html_tag as H
from mod_ahx_pix import worker_funcs as wf

@app.route('/ttest')
#-----------------------
def ttest():
    """ Try things here """
    return render_template( 'ttest.html', msg='ttest')

@app.route('/ws_dd')
#-----------------------
def ws_dd():
    """ Drag and Drop from Web Dev Simplified """
    return render_template( 'ws_dd.html')

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
#--------------------------------------------------
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
        iid = str(uuid.uuid4()) 
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
            return render_template( 'add_user.html', error=error, no_links=True, **data)
        # All is well, create user
        try:
            user.create_user(data, password)
        except Exception as e:
            return render_template( 'add_user.html', error=str(e), no_links=True, **data)
            
        flash( f'''User {data['username']} created.''')
        return redirect( url_for('index'))
    else: # Initial hit
        return render_template( 'add_user.html', error=error, no_links=True, **data)

@app.route('/carousel', methods=['GET', 'POST'])
#@login_required
#-------------------------------------------------
def carousel():
    """ Full screen swipeable image carousel """
    parms = get_parms()
    gallery_id = parms.get('gallery_id', session['gallery_id'])
    try:
        gallery = pe.get_galleries( title='', owner='', gallery_id = gallery_id)[0]    
    except:
        flash('Gallery not found', 'error')
        return redirect( url_for('index'))
    edit_icon = ''
    delete_icon = ''
    if logged_in() and gallery['username'] == current_user.data['username']:
        edit_icon = f''' <div class='ahx-edit' style='user-select:none;'>&#x270e;</div> '''
        delete_icon = f''' <div class='ahx-delete' style='user-select:none;'>&#x26d4;</div> '''

    if request.method == 'POST':  # form submitted
        gallery_id = session['gallery_id']
        active_pic_id = parms['pic_id']  # hidden form parm
        caption = parms['ta_caption']
        caption = helpers.sanitize_caption( caption)
        sql = f''' update picture set blurb = %s where id = %s '''
        pg.run(sql, (caption.strip(), active_pic_id))
        images = gui.gen_carousel_images(gallery, active_pic_id)
        return render_template('carousel.html',
                               images=images, gallery_id=gallery_id, picture_id=active_pic_id,
                               edit_icon=edit_icon, delete_icon=delete_icon)
    else:  # Initial hit
        gallery_id = parms['gallery_id']
        active_pic_id = parms['picture_id']
        images = gui.gen_carousel_images(gallery, active_pic_id)
        return render_template('carousel.html',
                               images=images, gallery_id=gallery_id, picture_id=active_pic_id,
                               edit_icon=edit_icon, delete_icon=delete_icon)

@app.route('/delete_gallery', methods=['GET', 'POST'])
@login_required
#---------------------------------------------------------------
def delete_gallery():
    """ Delete a gallery (prompt for confirmation first) """
    gallery_id = session['gallery_id']
    home = 'index_mobile' if session.get('is_mobile','') else 'index'
    gallery = 'gallery_mobile' if session.get('is_mobile','') else 'gallery'
    parms = get_parms()
    if request.method == 'POST': # form submitted
        if 'btn_one' in parms:
            flash('Gallery not deleted')
            return redirect( url_for(gallery, gallery_id=gallery_id))
        pg.run( f''' update gallery set deleted_flag = true where id = '{gallery_id}' ''')
        flash('Gallery deleted')
        pe.gallery_changed( gallery_id)
        return redirect( url_for(home))
    else:
        gallery = pe.get_galleries( title='', owner='', gallery_id = gallery_id)[0]
        if gallery['username'] != current_user.data['username']:
            error = 'You do not own this gallery.'
            return render_template('index.html', error=error)
        return render_template('question.html', 
                               msg=f'''Do you really want to delete gallery '{gallery['title']}'?
                                <div style='color:red;'>You cannot undo the delete!</div>''', 
                               value1='Back to safety', value2='DELETE',
                               no_links=True)

@app.route('/delete_pic', methods=['GET', 'POST'])
@login_required
#---------------------------------------------------------------
def delete_pic():
    """ Delete a pic (prompt for confirmation first) """
    gallery_id = session['gallery_id']
    parms = get_parms()
    pic_id = parms.get('pic_id', '') or session['pic_id']

    home = 'index_mobile' if session.get('is_mobile','') else 'index'
    gallery = 'gallery_mobile' if session.get('is_mobile','') else 'gallery'
    if request.method == 'POST': # form submitted
        if 'btn_one' in parms:
            flash('Pic not deleted')
            return redirect( url_for(gallery, gallery_id=gallery_id))
        pg.run( f''' update picture set deleted_flag = true where id = '{pic_id}' ''')
        flash('Pic deleted')
        pe.gallery_changed( gallery_id)
        return redirect( url_for(gallery, gallery_id=gallery_id))
    else:
        session['pic_id'] = pic_id
        return render_template('question.html', 
                               msg=f'''Do you really want to delete the pic?
                                <div style='color:red;'>You cannot undo the delete!</div>''', 
                               value1='Back to safety', value2='DELETE',
                               no_links=True)

@app.route('/download_img', methods=['GET'])
@login_required
#----------------------------------------------
def download_img():
    """ Return original full resolution image as attachment. """
    parms = get_parms()

    slide_src = parms['slide_src']
    # 'https://ahx-pics.s3.amazonaws.com/pics/medium/423/med_6865_423_0.jpeg?...' -> 6865
    picture_id = slide_src.split('?')[0].split('_')[1]
    gallery_id = slide_src.split('?')[0].split('_')[2]
    gallery_id = os.path.splitext(gallery_id)[0]

    if 'other_type' in parms:
        # 'pics_complete/2254_234_1.mp3' -> 2254
        picture_id = slide_src.split('/')[1].split('_')[0]
        gallery_id = slide_src.split('/')[1].split('_')[1]
        gallery_id = os.path.splitext(gallery_id)[0]
        s3_path = slide_src
    else:
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
#----------------------------------------------
def download_file():
    """
    Download a file from s3. Used for non-image files
    """
    parms = get_parms()
    fname = parms['fname']
    #orig_fname = parms['orig_fname']
    local_fname = helpers.s3_download_file(fname)
    ext = os.path.splitext(local_fname)[1]
    fh = open( local_fname, 'br')
    resp = send_file( fh, as_attachment=True, download_name=f'{os.path.split(fname)[1]}')
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

@app.route('/edit_pics', methods=['GET', 'POST'])
@login_required
#--------------------------------------------------
def edit_pics():
    """ Move pics around and edit the captions. """

    def autosort(gallery_id):
        """ Sort the pictures in a gallery by filename length and then alphabetically. """
        sql = f''' select id,orig_fname from picture where gallery_id = %s and deleted_flag = false  '''
        pics = pg.select( sql, (gallery_id,) )
        # Short names first; alphabetical within same length
        pics = sorted( pics, key = lambda x:  f'{len(x["orig_fname"]):04d}|{x["orig_fname"]}' )
        pic_ids = [ x['id'] for x in pics ]
        update_order( gallery_id, pic_ids)

    def delete_pics( pic_ids):
        idlist = [ f''' '{x}' ''' for x in pic_ids ]
        idlist = ','.join(idlist)
        sql = f''' update picture set deleted_flag = true where id in ({idlist}) and title_flag = false '''
        ndeleted = pg.run( sql)
        if ndeleted: pe.gallery_changed( gallery_id)

        sql = f''' select 1 from picture where id in ({idlist}) and title_flag = true '''
        nrows = pg.run( sql)
        if nrows > 0:
            flash('Title pic not deleted.')
        return ndeleted    

    def update_captions( caption_dict):
        pe.gallery_changed( gallery_id)
        for pic_id in caption_dict:
            caption = caption_dict[pic_id].strip()
            caption = helpers.sanitize_caption( caption)
            sql = f''' update picture set blurb = %s where id = %s '''
            pg.run( sql, (caption, pic_id))

    def update_order( gallery_id, pic_ids):
        pe.gallery_changed( gallery_id)
        piclist = json.dumps( [ x for x in pic_ids ] )
        sql = f''' update gallery set piclist = %s where id = %s '''
        pg.run( sql, (piclist, gallery_id))

    def initial_page( gallery_id):
        session['gallery_id'] = gallery_id
        gallery = pe.get_galleries( title='', owner='', gallery_id=gallery_id)[0]
        picdivs = gui.gen_edit_pics(gallery)
        return render_template( 'edit_pics.html', picdivs=picdivs, gallery_id=gallery_id, 
                                no_links=True, no_header=True, no_flash=True)

    parms = get_parms()
    gallery_id = parms.get( 'gallery_id', session['gallery_id'])
    gallery_page = 'gallery_mobile' if session.get('is_mobile','') else 'gallery'

    if request.method == 'POST': # form submitted
        # Cancel
        if 'btn_cancel' in parms:
            #flash( f'''Editing cancelled.''')
            return redirect( url_for( gallery_page, gallery_id=gallery_id))
        # Delete pics after confirmation
        elif 'btn_del' in parms: # Delete clicked; ask for confirmation
            delete_pic_ids = json.loads( parms['marked_pic_ids'])
            session['delete_pic_ids'] = delete_pic_ids
            n = len(delete_pic_ids)
            return render_template('question.html', 
                                   msg=f'''Do you really want to delete {len(delete_pic_ids)} pic{'s' if n > 1 else ''}?
                                   <div style='color:red;'>You cannot undo the delete!</div>''', 
                                   value1='Back to safety', value2='DELETE',
                                   no_links=True)
        elif 'btn_one' in parms:
            flash( 'Delete cancelled.')
            return redirect( url_for( gallery_page, gallery_id=gallery_id))
        elif 'btn_two' in parms:
            delete_pic_ids = session['delete_pic_ids']
            n = delete_pics( delete_pic_ids)
            if n: flash( f'''Deleted {n} pic{'s' if n > 1 else ''}.''')
            return redirect( url_for( gallery_page, gallery_id=gallery_id))
        elif 'btn_sort' in parms:
            autosort( gallery_id)
            flash( f'''Auto sort done.''')
            return redirect( url_for( gallery_page, gallery_id=gallery_id))
        elif 'btn_save' in parms:
            caption_dict = { p.split('_')[1]:parms[p].strip() for p in parms if p.startswith('ta_') }
            update_captions( caption_dict)
            update_order( gallery_id, caption_dict.keys())
            flash( f'''Changes saved.''')
            return redirect( url_for( gallery_page, gallery_id=gallery_id))
        else: # just show the edit page
            return initial_page( gallery_id)
    else: # initial hit
        return initial_page( gallery_id)

@app.route("/edit_title", methods=['GET', 'POST'])
@login_required
#-----------------------------------------------------
def edit_title():

    def save_changes(parms, gallery_id):
        title = parms.get('title','').strip() or ''
        caption = parms.get('caption','').strip() or ''
        blurb = parms.get('blurb','').strip() or ''
        show_title_pic_flag =  True if 'cb_show_tpic' in parms else False

        sql = f'''update gallery set title=%s where id=%s'''
        pg.run( sql, (title.strip(),gallery_id))

        sql = f'''update gallery set blurb=%s where id=%s'''
        pg.run( sql, (blurb.strip(),gallery_id))

        sql = f'''update gallery set show_title_pic_flag=%s where id=%s'''
        pg.run( sql, (show_title_pic_flag, gallery_id))

        sql = f'''update gallery set title_pic_caption=%s where id=%s'''
        pg.run( sql, (caption.strip(),gallery_id))

        if parms['access'] == 'public':
                sql = f'''update gallery set private_flag = false, public_flag = true where id=%s'''
        elif parms['access'] == 'private':
                sql = f'''update gallery set private_flag = true, public_flag = false where id=%s'''
        else:
                sql = f'''update gallery set private_flag = false, public_flag = false where id=%s'''
        pg.run( sql, (gallery_id,))

        sql = f'''update gallery set layout = 'multi_column' where id=%s'''
        if parms['layout'] == 'single_column':
            sql = f'''update gallery set layout = 'single_column' where id=%s'''
        elif parms['layout'] == 'double_column':
            sql = f'''update gallery set layout = 'double_column' where id=%s'''
        pg.run( sql, (gallery_id,))

        pe.gallery_changed( gallery_id)
            
    error = None
    data = {}
    data['gallery_title'] = session['gallery_title']
    gallery_id = session['gallery_id']
    gallery = pe.get_galleries( title='', owner='', gallery_id=gallery_id)[0]
    gallery_page = 'gallery_mobile' if session.get('is_mobile','') else 'gallery'

    data['access'] = 'members' 
    if gallery['public_flag']: data['access'] = 'public' 
    if gallery['private_flag']: data['access'] = 'private'

    data['blurb'] = gallery.get('blurb','') or ''
    data['layout'] = gallery.get('layout','multi_column') or 'multi_column'
    data['private_flag'] = gallery.get('private_flag',True)
    data['show_tpic'] = gallery.get('show_title_pic_flag',True)
    data['gallery_id'] = gallery_id
    title_pic = pe.get_title_pic(gallery_id)
    data['caption'] = ''
    if title_pic: data['caption'] = title_pic.get('blurb','') or ''
    if request.method == 'POST': # Save button clicked
        if 'file' not in request.files: # Save button clicked
            parms = get_parms()
            if 'save' in parms:
                save_changes( get_parms(), gallery_id)
                flash('Title changes saved. Refresh until changes show.')
            else:
                flash('Title changes discarded.')
            return redirect( url_for( gallery_page, gallery_id=gallery_id))
        else: # Title pic was dropped
            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('Please select a file', 'error')
                return redirect(request.url)
            if file: 
                tempfolder = f'''{UPLOAD_FOLDER}/{str(uuid.uuid4())}'''
                os.mkdir( tempfolder)            
                fname = secure_filename(file.filename)
                fname = f'''{tempfolder}/{fname}'''

                file.save(fname)
                helpers.s3_upload_files( [fname])
                Q.enqueue( wf.add_title_image, fname, gallery_id)
                shutil.rmtree(tempfolder) 
                return 'ok'
    else: # Initial hit
        return render_template( 'edit_title.html', error=error, **data, no_links=True )

@app.route('/gallery', methods=['GET', 'POST'])
#@login_required
#@show_error
#-------------------------------------------------
def gallery():
    """ View a gallery on a desktop computer """
    parms = get_parms()
    if session.get('is_mobile',''): return redirect( url_for('gallery_mobile', **parms))
    gallery_id = parms['gallery_id']
    pics = pe.get_gallery_pics( gallery_id)
    galleries = pe.get_galleries( title='', owner='', gallery_id=gallery_id)
    if not galleries:
        return redirect( url_for('login'))
    gallery = galleries[0]
    session['gallery_id'] = gallery['id']
    session['gallery_title'] = gallery['title']
    gallery_html = gui.gen_gallery( gallery, pics)
    mylinks = ''
    # I can edit my own galleries only
    if logged_in() and current_user.data['username'] == gallery['username']:
        mylinks = f'''
        <div style='margin-left:50px;margin-bottom:10px;width:100%;'>
          <a href="{url_for('upload_pics')}">Upload Pics</a> &nbsp;   
          <a href="{url_for('edit_title')}">Layout</a> &nbsp;   
          <a href="{url_for('edit_pics', gallery_id=gallery_id)}">Edit Pics</a> &nbsp;   
          <a href="{url_for('delete_gallery', gallery_id=gallery_id )}">Delete</a> &nbsp;   
        </div>
        '''
    return render_template( 'gallery.html', content=gallery_html, custom_links=mylinks, no_links=True)

@app.route('/gallery_mobile', methods=['GET', 'POST'])
#@login_required
#@show_error
#-------------------------------------------------------
def gallery_mobile():
    """ View a gallery on a phone """
    parms = get_parms()
    gallery_id = parms['gallery_id']
    pics = pe.get_gallery_pics( gallery_id)
    galleries = pe.get_galleries( title='', owner='', gallery_id=gallery_id)
    if not galleries:
        return redirect( url_for('login'))
    gallery = galleries[0]
    session['gallery_id'] = gallery['id']
    session['gallery_title'] = gallery['title']
    gallery_html = gui.gen_gallery_mobile( gallery, pics)
    mylinks = ''
    # I can edit my own galleries only
    if logged_in() and current_user.data['username'] == gallery['username']:
        mylinks = f'''
        <div style='margin-left:5vw;margin-bottom:10px;width:95vw;'>
        <a href="{url_for('upload_pics')}">Upload Pics</a> &nbsp;   
        <a href="{url_for('edit_title')}">Layout</a> &nbsp;   
        <a href="{url_for('edit_pics', gallery_id=gallery_id)}">Edit Pics</a> &nbsp;   
        <a href="{url_for('delete_gallery', gallery_id=gallery_id )}">Delete</a> &nbsp;   
        </div>
        '''
    return render_template( 'gallery_mobile.html', content=gallery_html, custom_links=mylinks, no_links=True)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
#@login_required
#-------------------------------------------------
def index():
    """ Main entry point. Show heading and list of galleries """
    parms = get_parms()
    if session.get('is_mobile',''): return redirect( url_for('index_mobile', **parms))
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
#@login_required
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
            login_user(user, remember=True)
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
    data = {'access':'private'}
    if request.method == 'POST': # form submitted
        parms = get_parms()
        title = parms['title']
        if len(title.strip()) == 0:
            return render_template( 'new_gallery.html', error='Please specify a title', **data)
        today = date.today()
        iid = str(uuid.uuid4())
        private_flag=False; public_flag=False
        if parms['access'] == 'private':
            private_flag=True
        if parms['access'] == 'public':
            public_flag=True
        data = { 
            'id':iid
            ,'username':current_user.data['username']
            ,'title':title
            ,'private_flag':private_flag
            ,'public_flag':public_flag
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

    def chunkfname(dropname, chunk):
        return f'{UPLOAD_FOLDER}/{dropname}.part{chunk}'
    
    def upload_chunk():
        chunk = request.form.get('dzchunkindex',0)
        dzuuid = request.form.get('dzuuid',str(uuid.uuid4()))
        dztotalchunkcount = int(request.form.get('dztotalchunkcount',1))

        # Get the file chunk
        file = request.files['file']

        dropname = dzuuid
        file.save(chunkfname(dropname, chunk))

        # Check if all chunks have been uploaded
        all_chunks_uploaded = all(
            os.path.exists(chunkfname(dropname, i))
            for i in range(dztotalchunkcount)
        )
        # If all chunks are uploaded, combine them into a single file
        tempfolder = f'''{UPLOAD_FOLDER}/{dropname}'''
        # Parallel uploads will create the same tempfolder, so only create it if it doesn't exist
        if all_chunks_uploaded and not os.path.exists(tempfolder):
            os.mkdir(tempfolder)
            fname = secure_filename(file.filename)
            fname = f'''{tempfolder}/{fname}'''
            with open(fname, 'wb') as f:
                for i in range(dztotalchunkcount):
                    chunk_filename = chunkfname(dropname, i)
                    with open(chunk_filename, 'rb') as chunk_file:
                        f.write(chunk_file.read())
                    os.remove(chunk_filename)
            helpers.s3_upload_files([fname])
            Q.enqueue(wf.add_new_images, fname, gallery_id)
            shutil.rmtree(tempfolder) 
            return 'OK'
        else:
            return f'{chunk}/{dztotalchunkcount}'

    error = None
    data = {}
    data['gallery_title'] = session['gallery_title']
    gallery_id = session['gallery_id']
    data['gallery_id'] = gallery_id
    gallery_page = 'gallery_mobile' if session.get(
        'is_mobile', '') else 'gallery'
    if request.method == 'POST':  # File dropped or upload button clicked
        parms = get_parms()
        if 'btn_upload' in parms:
            flash('Uploading. Keep refreshing until the pics show up.')
            return redirect(url_for(gallery_page, gallery_id=gallery_id))
        else:  # Files from dropzone drop
            return upload_chunk()

    else:  # Initial hit
        return render_template('upload_pics.html', error=error, **data, no_links=True)

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

