# /********************************************************************
# Filename: mod_ahx_pics/helpers.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/

from pdb import set_trace as BP
import sys,os,subprocess
import inspect
import uuid

# AWS S3 api
import boto3

from mod_ahx_pics import S3_BUCKET, DOWNLOAD_FOLDER, ORIG_FOLDER, MEDIUM_FOLDER, SMALL_FOLDER, log
from mod_ahx_pics import IMG_EXTENSIONS, VIDEO_EXTENSIONS

# Misc
#--------------

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


# S3 functions
#-----------------------

def s3_get_link( fname, client=''):
    """
    Get presigned URLs for the given file paths.
    These can be used as img urls in an html template.
    Example path: 'test_gallery_01/orig/eiffel.jpg'
    """
    if not client: client = _get_s3_client()
    url = ''
    try:
        url = client.generate_presigned_url(
            ClientMethod='get_object', 
            Params={'Bucket':S3_BUCKET, 'Key':fname},
            ExpiresIn=3600)
    except Exception as e:
        url = 'static/images/img_not_found.jpg'

    return url, client    

def s3_upload_files( fnames, s3_fnames=''):
    if not s3_fnames: s3_fnames = fnames
    client = _get_s3_client()
    for idx,fname in enumerate(fnames):
        s3_fname = s3_fnames[idx]
        if idx % 10 == 0:
            log(f'uploading {idx+1}/{len(fnames)}')
        try:
            response = client.upload_file( fname, S3_BUCKET, s3_fname)
        except Exception as e:
            log(pexc(e))

def s3_delete_files( fnames):
    client = _get_s3_client()
    for idx,fname in enumerate(fnames):
        try:
            log(f'deleting {fname}')
            response = client.delete_object( Bucket=S3_BUCKET, Key=fname)
        except Exception as e:
            log(pexc(e))

def s3_get_keys( prefix, client=''):
    """ Get complete info for all objects starting with prefix, like Key, Size, ... """
    if not client: client = _get_s3_client()
    paginator = client.get_paginator('list_objects_v2')

    infos = []
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)
    for page in pages:
        if 'Contents' in page:
            rows = page['Contents']
            infos.extend( rows )        
    return infos, client

def s3_download_file(fname):
    """ Download a file from s3 into unique filename and return the filename """
    client = _get_s3_client()
    ext = os.path.splitext(fname)[1]
    ofname = DOWNLOAD_FOLDER + '/' + str(uuid.uuid4()) + ext
    client.download_file( S3_BUCKET, fname, ofname)
    return ofname

def s3_prefix(fname, size):
    if size == 'small': res = SMALL_FOLDER + 'sm_' + basename( fname)
    elif size == 'orig': res = ORIG_FOLDER + basename( fname)
    else: res = MEDIUM_FOLDER + 'med_' + basename( fname)
    return res

def _get_s3_client():
    client = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_KEY'],
        aws_secret_access_key=os.environ['AWS_SECRET']
    )
    return client


