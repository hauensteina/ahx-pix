# /********************************************************************
# Filename: mod_ahx_pics/helpers.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/

from pdb import set_trace as BP
import sys,os

# AWS S3 api
import boto3

from mod_ahx_pics import S3_BUCKET, log

def get_s3_links( fnames):
    """
    Get presigned URLs for the given file paths.
    These can be used as img urls in an html template.
    Example path: 'test_gallery_01/orig/eiffel.jpg'
    """
    client = _get_client()
    urls = []
    for f in fnames:
        try:
            url = client.generate_presigned_url(
                ClientMethod='get_object', 
                Params={'Bucket':S3_BUCKET, 'Key':f},
                ExpiresIn=3600)
        except Exception as e:
            url = 'static/images/img_not_found.jpg'
        urls.append(url)

    return urls    

def s3_upload_files( fnames):
    client = _get_client()
    for idx,fname in enumerate(fnames):
        if idx % 10 == 0:
            log(f'uploaded {idx}/{len(fnames)}')
        try:
            response = client.upload_file( fname, S3_BUCKET, fname)
        except Exception as e:
            log(e)

def s3_delete_files( fnames):
    client = _get_client()
    for idx,fname in enumerate(fnames):
        try:
            log(f'deleting {fname}')
            response = client.delete_object( Bucket=S3_BUCKET, Key=fname)
        except Exception as e:
            log(e)

def s3_get_keys( prefix):
    MAX_KEYS = 10000
    client = _get_client()
    paginator = client.get_paginator('list_objects_v2')

    keys = []
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)
    for page in pages:
        rows = page['Contents']
        keys.extend( [ x['Key'] for x in rows ] )        
    return keys

def _get_client():
    client = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_KEY'],
        aws_secret_access_key=os.environ['AWS_SECRET']
    )
    return client


