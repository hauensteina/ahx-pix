"""
worker_funcs.py
Andreas Hauenstein
Created: Feb 2023

Functions for background execution via Redis Queue
"""

from pdb import set_trace as BP
import os, shutil, json
import datetime
import shortuuid
from PIL import Image, ExifTags
from mod_ahx_pics.helpers import pexc, media_type, run_shell
from mod_ahx_pics import log,pg,Q

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
    #orig_files = pg.select( f''' select filename from picture where id = '6846' order by gallery_id, position, filename ''')
    #orig_files = pg.select( f''' select filename from picture where gallery_id = '423' order by gallery_id, position, filename ''')
    orig_files = pg.select( f''' select filename from picture order by gallery_id, position, filename ''')
    # 'pics_complete/1009_176_1.JPG'
    orig_files = [ f'''{ORIG_FOLDER}{os.path.split(x['filename'])[1]}''' for x in orig_files ]

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
    
def _resize_media( fnames, gallery_id, size):
    tstart = datetime.datetime.now()
    for idx,fname in enumerate(fnames):
        if not os.path.exists(fname):
            log( f'''_resize_media(): File {fname} not found. Skipping''')
            continue
        log( f' {idx+1}/{len(fnames)} Generating {size} version for {fname}') 
        if media_type( fname) == 'image':
            _resize_image( fname, gallery_id, size)
        elif media_type( fname) == 'video':
            _resize_video( fname, gallery_id, size)
        else:
            log( f'ERROR: unknown media extension: {fname}. Skipping resize.')
            
    tend = datetime.datetime.now()
    log( f'{size} size media generated in {tend - tstart}')

def _resize_video( fname, gallery_id, size):
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
        smallwidth = MEDIUM_THUMB_SIZE
    else: # large
        prefix = 'lg'
        target_folder = LARGE_FOLDER
        ext = os.path.splitext(fname)[1]
    try:
        #local_fname = s3_download_file(fname)
        local_fname = fname
        local_thumb = f'{DOWNLOAD_FOLDER}/{prefix}_{basename(local_fname)}{ext}'
        #gallery_id = basename(fname).split('_')[1]
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
            #os.remove(local_fname)
            os.remove(local_thumb)
        except:
            pass
    
def _resize_image( fname, gallery_id, size='small'):
    """ Resize images to either small or medium size and store in target folder """
    if size == 'small':
        prefix = 'sm'
        target_folder = SMALL_FOLDER
        max_size = SMALL_THUMB_SIZE
        qual = 100
    elif size == 'medium': 
        prefix = 'med'
        target_folder = MEDIUM_FOLDER
        max_size = MEDIUM_THUMB_SIZE
        qual = 90
    else: # large
        prefix = 'lg'
        target_folder = LARGE_FOLDER
        max_size = 0
        
    try:
        #local_fname = s3_download_file(fname)
        local_fname = fname
        ext = os.path.splitext(fname)[1].lower()
        local_thumb = f'{DOWNLOAD_FOLDER}/{prefix}_{basename(local_fname)}{ext}'
        #gallery_id = basename(fname).split('_')[1]
        s3_thumb = f'{target_folder}{gallery_id}/{prefix}_{basename(fname)}{ext}'
        if ext != '.pdf' and size != 'large':
            try:
                cmd = f''' convert {local_fname} -auto-orient -resize {max_size}x{max_size}\> -quality {qual} +profile '*' {local_thumb} '''
                out,err = run_shell( cmd)
            except Exception as e:
                log(pexc(e))
                log(f'WARNING: ImageMagick resize of {fname} failed. Using PIL.') 
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
            #os.remove(local_fname)
            os.remove(local_thumb)
        except:
            pass

""" TODO: This is outdated and needs fixing """
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

def f01_unzip(fname):
    """ Unzip if its a zip file and kick off the pipeline """
    log('  ERROR: Unzip not implemented yet.')

def f02_gen_thumbs( s3name, gallery_id):
    log(f'''  WORKER: f02_gen_thumbs({s3name},{gallery_id}) starting''')
    # Generate smaller images and upload to S3
    _resize_media( [s3name], gallery_id, 'small')
    _resize_media( [s3name], gallery_id, 'medium')
    _resize_media( [s3name], gallery_id, 'large')
    log(f'''  WORKER: f02_gen_thumbs() done''')

def f03_insert_db( s3name, orig_fname, gallery_id, pic_id):
    """ Tell the DB about the new image """
    log(f'''  WORKER: f03_insert_db({s3name},{gallery_id}) starting''')
    today = datetime.date.today()
    s3name = os.path.split(s3name)[1]
    data = {
        'id':pic_id
        ,'gallery_id':gallery_id
        ,'blurb':''
        ,'filename':s3name
        ,'orig_fname': orig_fname
        ,'title_flag':False
        ,'create_date':today
        ,'change_date':today
    }
    pg.insert( 'picture', [data])
    log(f'''  WORKER: f03_insert_db() done''')

def _set_gallery_status( gallery_id, msg):
    data = { 'status': json.dumps({'msg':msg}) }
    pg.update_row( 'gallery', 'id', gallery_id, data)

def add_new_images( fname, gallery_id):
    """ Add new images to a gallery """
    log( f'''WORKER:  add_new_images( {fname}, {gallery_id}) starting''')
    fnames = [fname]
    if os.path.splitext(fname)[1].lower() == '.zip':
        fnames = f01_unzip( fname)
    for idx,fname in enumerate(fnames):
        BP()
        _set_gallery_status( gallery_id, f'''Adding image {fname} ({idx+1}/{len(fnames)})''')
        pic_id = shortuuid.uuid()
        ext = os.path.splitext(fname)[1].lower()
        path = os.path.split(fname)[0]
        s3name = f'''{path}/{gallery_id}_{pic_id}{ext}'''
        shutil.copyfile( fname, s3name)
        f02_gen_thumbs( s3name, gallery_id)
        f03_insert_db( s3name, fname, gallery_id, pic_id)
    _set_gallery_status( gallery_id, f'ok')
    log( f'''WORKER:  add_new_images() done''')
