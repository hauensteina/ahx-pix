"""
worker_funcs.py
Andreas Hauenstein
Created: Feb 2023

Functions for background execution via Redis Queue
"""

from pdb import set_trace as BP
import os
import datetime
from PIL import Image
from mod_ahx_pics.helpers import pexc, media_type, run_shell
from mod_ahx_pics import log
from mod_ahx_pics import ORIG_FOLDER, MEDIUM_FOLDER, SMALL_FOLDER, SMALL_THUMB_SIZE, MEDIUM_THUMB_SIZE
from mod_ahx_pics import FFMPEG_COMPRESSOR, FFMPEG_THUMB
from mod_ahx_pics import DOWNLOAD_FOLDER
from mod_ahx_pics.helpers import s3_get_keys, basename, s3_download_file, s3_upload_files, s3_delete_files

def _get_missing_media(subfolder):
    """
    Find all fnames where 1009_176_1.JPG exists in orig folder,
    but sm_1009_176_1.jpg does not exist in small folder.
    Same for medium (aka web) size.
    """
    prefix = 'sm'
    if '/medium/' in subfolder: prefix = 'med'

    orig_files = sorted( [ x['Key'] for x in s3_get_keys( ORIG_FOLDER) ]) 
    # pics/orig/name.jpeg -> name
    orig_basenames = [ basename(x) for x in orig_files ]

    # pics/small/name.jpeg -> name
    existing_target_files =  [ x['Key'] for x in s3_get_keys( subfolder) ] 
    existing_target_basenames = [ basename(x) for x in existing_target_files ]

    missing_target_basenames = [ x for x in orig_basenames if not f'{prefix}_{x}' in set(existing_target_basenames) ]
    missing_orig_fnames = [ orig_files[i] for (i,x) in enumerate(orig_basenames) if x in set(missing_target_basenames) ]
    return missing_orig_fnames
    
def _resize_media( fnames, size):
    tstart = datetime.datetime.now()
    for idx,fname in enumerate(fnames):
        log( f' {idx+1}/{len(fnames)} Generating {size} version for {fname}') 
        if media_type( fname) == 'image':
            _resize_image( fname, size)
        elif media_type( fname) == 'video':
            _resize_video( fname, size)
        else:
            log( f'ERROR: unknown media extension: {fname}')
            log( f'deleting')
            s3_delete_files([fname])
            
    tend = datetime.datetime.now()
    log( f'{size} size media generated in {tend - tstart}')

def _resize_video( fname, size):
    """ Compress video. The small version is just a single thumbnail frame. """
    prefix = 'sm'
    target_folder = SMALL_FOLDER
    cmd = FFMPEG_THUMB
    ext = '.jpeg'
    if size == 'medium': 
        prefix = 'med'
        target_folder = MEDIUM_FOLDER
        cmd = FFMPEG_COMPRESSOR
        ext = '.mp4'

    try:
        local_fname = s3_download_file(fname)
        #ext = os.path.splitext(fname)[1].lower()
        local_thumb = f'{DOWNLOAD_FOLDER}/{prefix}_{basename(local_fname)}{ext}'
        s3_thumb = f'{target_folder}{prefix}_{basename(fname)}{ext}'
        cmd = cmd.replace( '@IN', local_fname)
        cmd = cmd.replace( '@OUT', local_thumb)
        out,err = run_shell( cmd)
        s3_upload_files( [local_thumb], [s3_thumb])
    except Exception as e:
        log( f'EXCEPTION: {pexc(e)}')
    finally:
        try:
            os.remove(local_fname)
            os.remove(local_thumb)
        except:
            pass
    
def _resize_image( fname, size='small'):
    """ Resize images to either small or medium size and store in target folder """
    prefix = 'sm'
    target_folder = SMALL_FOLDER
    max_size = (SMALL_THUMB_SIZE, SMALL_THUMB_SIZE)
    if size == 'medium': 
        prefix = 'med'
        target_folder = MEDIUM_FOLDER
        max_size = (MEDIUM_THUMB_SIZE, MEDIUM_THUMB_SIZE)

    try:
        local_fname = s3_download_file(fname)
        ext = os.path.splitext(fname)[1].lower()
        local_thumb = f'{DOWNLOAD_FOLDER}/{prefix}_{basename(local_fname)}{ext}'
        s3_thumb = f'{target_folder}{prefix}_{basename(fname)}{ext}'
        if ext != '.pdf':
            image = Image.open( local_fname)
            MAX_SIZE = (100, 100)
            image.thumbnail( max_size)
            image.save( local_thumb)
            s3_upload_files( [local_thumb], [s3_thumb])
        else: # Just leave pdfs alone
            s3_upload_files( [local_fname], [s3_thumb])
    except Exception as e:
        if 'truncated' in str(e):
          s3_upload_files( [local_fname], [s3_thumb])
        log( f'EXCEPTION: {pexc(e)}')
    finally:
        try:
            os.remove(local_fname)
            os.remove(local_thumb)
        except:
            pass

def gen_thumbnails():
    log(f'>>>>>>> generating thumbnails')
    # Paths to originals that still need thumbnails
    missing_small  = _get_missing_media( SMALL_FOLDER)
    _resize_media( missing_small, 'small')

    log(f'>>>>>>> generating web size')
    # Paths to originals that still need web size versions
    missing_medium  = _get_missing_media( MEDIUM_FOLDER)
    _resize_media( missing_medium, 'medium')
    log('Done.')

