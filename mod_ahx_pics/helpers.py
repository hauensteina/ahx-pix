# /********************************************************************
# Filename: mod_ahx_pics/helpers.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/

from pdb import set_trace as BP
import sys,os

# AWS S3 api
import boto3

from mod_ahx_pics import S3_BUCKET

def get_s3_links( fnames):
    """
    Get presigned URLs for the given file paths.
    These can be used as img urls in an html template.
    Example path: 'test_gallery_01/orig/eiffel.jpg'
    """
    client = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_KEY'],
        aws_secret_access_key=os.environ['AWS_SECRET']
    )
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

