# /********************************************************************
# Filename: mod_ahx_pics/helpers.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/

from pdb import set_trace as BP
import sys,os,subprocess
import inspect
import uuid
#from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
#from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import TimestampSigner
from flask_mail import Message
from flask import url_for

# AWS S3 api
import boto3

from mod_ahx_pics import S3_BUCKET, DOWNLOAD_FOLDER, LARGE_FOLDER, MEDIUM_FOLDER, SMALL_FOLDER, log
from mod_ahx_pics import IMG_EXTENSIONS, VIDEO_EXTENSIONS
from mod_ahx_pics import app,mail

# Misc
#--------------

def send_reset_email( user):
    ''' User requested a password reset. Send him an email with a reset link. '''
    expires_sec = 3600 * 24 * 7 
    s = TimestampSigner( app.config['SECRET_KEY'])
    token = s.sign( user.id)
    msg = Message('Password Reset Request',
                  sender='noreply@ahaux.com',
                  recipients=[user.data['email']])
    #msg.body = 'hi there testing a reset'
    tstr = f'''
To reset your Picture Galleries password, visit the following link:

{url_for('reset_token', token=token, _external=True)}

If you did not request a password change, you can safely ignore this email.
    '''
    msg.body = tstr
    mail.send(msg)

def media_type( fname):
    ext = os.path.splitext(fname)[1].lower()
    if ext in IMG_EXTENSIONS:
        return 'image'
    elif ext in VIDEO_EXTENSIONS:
        return 'video'
    return 'unknown'

def run_shell(cmd):
    sp = subprocess.Popen(cmd,
                          shell=True,
                          encoding='utf8',
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    out,err=sp.communicate()
    return out,err

def basename(fname):
    """ pics/orig/bla.jpeg -> bla """
    res = os.path.splitext( os.path.split(fname)[1])[0]
    return res

def pexc( e):
    """ Return  function and line number of exception """
    func = inspect.stack()[1].function
    exc_type, exc_obj, exc_tb = sys.exc_info()
    msg = f'{func}():{exc_tb.tb_lineno}: {str(e)}'
    return msg

def html_tag( tag, content='', style=''):
    """
    Make a piece of HTML surrounded by tag,
    with content and style.
    Example: 
    html_tag( 'div', 'hello', 'width:100px;')
    """
    if content is None: content = ''
    res = '\n'
    res += f'<{tag}'
    if style: res += f' style="{style}">\n'
    else: res += '>\n'
    res += f'{content}\n' 
    res += f'</{tag.split()[0]}>\n'
    return res

def html_img( link, style='', attributes=''):
    """
    Make an HTML image tag.
    Examples: 
    html_tag( 'hello.png', 'width:100px;', 'class="whatever"')
    """
    res = f'''<img src='{link}' {attributes} style='{style}'>\n'''
    return res

# S3 functions
#-----------------------

def s3_get_link( client, fname, expire_hours=1):
    """
    Get presigned URL for the given file path.
    The URL can be used as img url in an html template.
    Example: img_link, s3_client = helpers.s3_get_link( 'test_gallery_01/orig/eiffel.jpg', s3_client)
    Note that this happens locally and does not cause an API hit.
    """
    url = ''
    try:
        url = client.generate_presigned_url(
            ClientMethod='get_object', 
            Params={'Bucket':S3_BUCKET, 'Key':fname},
            ExpiresIn = expire_hours * 3600)
    except Exception as e:
        url = 'static/images/img_not_found.jpg'

    return url

def s3_upload_files( fnames, s3_fnames=''):
    if not s3_fnames: s3_fnames = fnames
    client = s3_get_client()
    for idx,fname in enumerate(fnames):
        s3_fname = s3_fnames[idx]
        if idx % 10 == 0:
            log(f'uploading {idx+1}/{len(fnames)}')
        try:
            response = client.upload_file( fname, S3_BUCKET, s3_fname)
        except Exception as e:
            log(pexc(e))

def s3_delete_files( fnames):
    client = s3_get_client()
    for idx,fname in enumerate(fnames):
        try:
            log(f'deleting {fname}')
            response = client.delete_object( Bucket=S3_BUCKET, Key=fname)
        except Exception as e:
            log(pexc(e))

def s3_get_keys( client, prefix):
    """ Get complete info for all objects starting with prefix, like Key, Size, ... """
    paginator = client.get_paginator('list_objects_v2')

    infos = []
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)
    for page in pages:
        if 'Contents' in page:
            rows = page['Contents']
            infos.extend( rows )        
    return infos

def s3_download_file(fname):
    """ Download a file from s3 into unique filename and return the filename """
    client = s3_get_client()
    ext = os.path.splitext(fname)[1]
    ofname = DOWNLOAD_FOLDER + '/' + str(uuid.uuid4()) + ext
    client.download_file( S3_BUCKET, fname, ofname)
    return ofname

def s3_prefix(fname, size):
    parts = fname.split('_')
    gallery_id = parts[1]
    if size == 'small': res = SMALL_FOLDER + gallery_id + '/sm_' + basename( fname)
    elif size == 'large': res = LARGE_FOLDER + gallery_id + '/' + basename( fname)
    else: res = MEDIUM_FOLDER + gallery_id + '/med_' + basename( fname)
    return res

def s3_get_client():
    client = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_KEY'],
        aws_secret_access_key=os.environ['AWS_SECRET']
    )
    return client


