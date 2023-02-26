"""
worker_funcs.py
Andreas Hauenstein
Created: Feb 2023

Functions for background execution via Redis Queue
"""

from pdb import set_trace as BP
import os
import datetime
from PIL import Image, ExifTags
from mod_ahx_pics.helpers import pexc, media_type, run_shell
from mod_ahx_pics import log

from mod_ahx_pics import (
    ORIG_FOLDER, LARGE_FOLDER, MEDIUM_FOLDER, SMALL_FOLDER, SMALL_THUMB_SIZE, MEDIUM_THUMB_SIZE
)

from mod_ahx_pics import FFMPEG_COMPRESSOR, FFMPEG_VIDEO_THUMB, FFMPEG_RESIZE_IMG
from mod_ahx_pics import DOWNLOAD_FOLDER

from mod_ahx_pics.helpers import (
    basename, s3_get_keys, s3_download_file, s3_upload_files, s3_delete_files, s3_get_client
)

def _get_missing_media(subfolder):
    """
    Find all fnames where 1009_176_1.JPG exists in orig folder,
    but sm_1009_176_1.jpg does not exist in small folder.
    Same for medium (aka web) size.
    """
    prefix = 'sm'
    if '/medium/' in subfolder: prefix = 'med'
    elif '/large/' in subfolder: prefix = 'lg'

    s3_client = s3_get_client()
    orig_files = s3_get_keys( s3_client, ORIG_FOLDER)
    orig_files = sorted( [ x['Key'] for x in orig_files ]) 
    # pics/orig/name.jpeg -> name
    orig_basenames = [ basename(x) for x in orig_files ]

    # pics/small/name.jpeg -> name
    existing_target_files = s3_get_keys( s3_client, subfolder)
    existing_target_files =  [ x['Key'] for x in existing_target_files ] 
    existing_target_basenames = [ basename(x) for x in existing_target_files ]

    missing_target_basenames = [ x for x in orig_basenames 
                                 if not f'{prefix}_{x}' in set(existing_target_basenames) ]
    missing_orig_fnames = [ orig_files[i] for (i,x) in enumerate(orig_basenames) 
                            if x in set(missing_target_basenames) ]
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
    if size == 'small':
        prefix = 'sm'
        target_folder = SMALL_FOLDER
        cmd = FFMPEG_VIDEO_THUMB
        ext = '.jpeg'
    elif size == 'medium': 
        prefix = 'med'
        target_folder = MEDIUM_FOLDER
        cmd = FFMPEG_COMPRESSOR
        ext = '.mp4'
    else: # large
        prefix = 'lg'
        target_folder = LARGE_FOLDER
        ext = os.path.splitext(fname)[1]

    try:
        local_fname = s3_download_file(fname)
        #ext = os.path.splitext(fname)[1].lower()
        local_thumb = f'{DOWNLOAD_FOLDER}/{prefix}_{basename(local_fname)}{ext}'
        gallery_id = basename(fname).split('_')[1]
        s3_thumb = f'{target_folder}{gallery_id}/{prefix}_{basename(fname)}{ext}'
        if size == 'large': # Large version remains unchanged
            local_thumb = local_fname
        else:
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
    if size == 'small':
        prefix = 'sm'
        target_folder = SMALL_FOLDER
        #max_size = (SMALL_THUMB_SIZE, SMALL_THUMB_SIZE)
        max_size = SMALL_THUMB_SIZE
    elif size == 'medium': 
        prefix = 'med'
        target_folder = MEDIUM_FOLDER
        #max_size = (MEDIUM_THUMB_SIZE, MEDIUM_THUMB_SIZE)
        max_size = MEDIUM_THUMB_SIZE
    else: # large
        prefix = 'lg'
        target_folder = LARGE_FOLDER
        
    try:
        local_fname = s3_download_file(fname)
        ext = os.path.splitext(fname)[1].lower()
        local_thumb = f'{DOWNLOAD_FOLDER}/{prefix}_{basename(local_fname)}{ext}'
        gallery_id = basename(fname).split('_')[1]
        s3_thumb = f'{target_folder}{gallery_id}/{prefix}_{basename(fname)}{ext}'
        if ext != '.pdf' and size != 'large':
            cmd = FFMPEG_RESIZE_IMG
            image = Image.open( local_fname)
            for orientation_key in ExifTags.TAGS.keys() : 
                if ExifTags.TAGS[orientation_key]=='Orientation' : break 
            try:
                exif = {}
                if image._getexif():
                    exif=dict(image._getexif().items())
                orientation = exif.get(orientation_key,0)    
                rot = ''
                if   orientation == 3 : 
                    rot = ',transpose=1,transpose=1'
                    #image=image.rotate(180, expand=True)
                elif orientation == 6 : 
                    rot = ',transpose=1'
                    #image=image.rotate(270, expand=True)
                elif orientation == 8 : 
                    rot = ',transpose=2'
                    #image=image.rotate(90, expand=True)
                cmd = cmd.replace( '@MAXW', str(max_size))
                cmd = cmd.replace( '@IN', local_fname)
                cmd = cmd.replace( '@OUT', local_thumb)
                cmd = cmd.replace( '@ROT', rot)
                out,err = run_shell( cmd)
                #image.thumbnail( max_size)            
                #image.thumbnail( max_size, resample=Resampling.NEAREST, reducing_gap=2.0 )            
            except Exception as e:
                log(pexc(e))
                log(f'WARNING: ffmpeg resize of {fname} failed. Using PIL.') 
                image.thumbnail( (max_size,max_size))
                image.save( local_thumb, quality=95)

            s3_upload_files( [local_thumb], [s3_thumb])
        else: # Just leave pdfs and large image version alone
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

    log(f'>>>>>>> generating large size')
    # Paths to originals that still need large size versions
    missing_large  = _get_missing_media( LARGE_FOLDER)
    _resize_media( missing_large, 'large')

    log('Done.')

