"""
worker_funcs.py
Andreas Hauenstein
Created: Jan 2023

Functions for background execution via Redis Queue
"""

from pdb import set_trace as BP
import os
import datetime
from PIL import Image
from mod_ahx_pics.helpers import pexc
from mod_ahx_pics import log
from mod_ahx_pics import ORIG_FOLDER, MEDIUM_FOLDER, SMALL_FOLDER, SMALL_THUMB_SIZE, MEDIUM_THUMB_SIZE
from mod_ahx_pics import DOWNLOAD_FOLDER
from mod_ahx_pics.helpers import s3_get_keys, basename, s3_download_file, s3_upload_files

def _get_missing_imgs(subfolder):
    """
    Find all fnames where 1009_176_1.JPG exists in orig folder,
    but sm_1009_176_1.jpg does not exist in small folder.
    """
    prefix = 'sm'
    if '/medium/' in subfolder: prefix = 'med'

    orig_files = sorted( s3_get_keys( ORIG_FOLDER))
    # pics/orig/name.jpeg -> name
    orig_basenames = [ basename(x) for x in orig_files ]

    # pics/small/name.jpeg -> name
    existing_target_files = s3_get_keys( subfolder)
    existing_target_basenames = [ basename(x) for x in existing_target_files ]

    missing_target_basenames = [ x for x in orig_basenames if not f'{prefix}_{x}' in set(existing_target_basenames) ]
    missing_orig_fnames = [ orig_files[i] for (i,x) in enumerate(orig_basenames) if x in set(missing_target_basenames) ]
    return missing_orig_fnames
    
def _resize_images( fnames, size='small'):
    """ Resize images to either small or medium size and store in target folder """
    prefix = 'sm'
    target_folder = SMALL_FOLDER
    max_size = (SMALL_THUMB_SIZE, SMALL_THUMB_SIZE)
    if size == 'medium': 
        prefix = 'med'
        target_folder = MEDIUM_FOLDER
        max_size = (MEDIUM_THUMB_SIZE, MEDIUM_THUMB_SIZE)

    tstart = datetime.datetime.now()
    for idx,fname in enumerate(fnames):
        try:
            log( f' {idx+1}/{len(fnames)} Generating {size} thumbnail for {fname}') 
            local_fname = s3_download_file(fname)
            ext = os.path.splitext(fname)[1].lower()
            local_thumb = f'{DOWNLOAD_FOLDER}/{prefix}_{basename(local_fname)}{ext}'
            s3_thumb = f'{target_folder}{prefix}_{basename(fname)}{ext}'
            image = Image.open( local_fname)
            MAX_SIZE = (100, 100)
            image.thumbnail( max_size)
            image.save( local_thumb)
            s3_upload_files( [local_thumb], [s3_thumb])
        except Exception as e:
            log( pexc(e))
        finally:
            try:
                os.remove(local_fname)
                os.remove(local_thumb)
            except:
                pass
    tend = datetime.datetime.now()
    log( f'Thumbnails generated in {tend - tstart}')

def gen_thumbnails():
    log(f'>>>>>>> generating thumbnails')
    # Paths to originals that still need thumbnails
    missing_small  = _get_missing_imgs( SMALL_FOLDER)
    #missing_medium  = _get_missing_imgs( MEDIUM_FOLDER)
    _resize_images( missing_small, 'small')
    #resize_images( missing_medium, 'medium')
    log('Done.')

