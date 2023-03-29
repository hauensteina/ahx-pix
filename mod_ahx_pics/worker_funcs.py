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
from zipfile import ZipFile
from PIL import Image, ExifTags
from mod_ahx_pics.helpers import pexc, media_type, run_shell, list_files
from mod_ahx_pics import log,pg,Q
import mod_ahx_pics.helpers as helpers

from mod_ahx_pics import (
    LARGE_FOLDER, MEDIUM_FOLDER, SMALL_FOLDER, SMALL_THUMB_SIZE, MEDIUM_THUMB_SIZE, 
    IMG_EXTENSIONS, VIDEO_EXTENSIONS, MEDIA_EXTENSIONS
)

from mod_ahx_pics import FFMPEG_COMPRESSOR, FFMPEG_VIDEO_THUMB, FFMPEG_RESIZE_IMG
from mod_ahx_pics import DOWNLOAD_FOLDER

from mod_ahx_pics.helpers import (
    basename, s3_get_keys, s3_download_file, s3_upload_files, s3_delete_files, s3_get_client
)
    
def _resize_media( fnames, gallery_id, size):
    tstart = datetime.datetime.now()
    for idx,fname in enumerate(fnames):
        if not os.path.exists(fname):
            #log( f'''_resize_media(): File {fname} not found. Skipping''')
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
        local_fname = fname
        local_thumb = f'{DOWNLOAD_FOLDER}/{prefix}_{basename(local_fname)}{ext}'
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
            if local_thumb != fname: os.remove(local_thumb)
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
        local_fname = fname
        ext = os.path.splitext(fname)[1].lower()
        local_thumb = f'{DOWNLOAD_FOLDER}/{prefix}_{basename(local_fname)}{ext}'
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
            os.remove(local_thumb)
        except:
            pass

def gen_thumbnails():
    """ Generate missing thumbnails """
    s3_client = s3_get_client()

    def convert(key, size='small'):
        basename = key.split( '/lg_')[1] # 'pics/large/1/lg_1_1_1' -> 1_1_1
        local_fname = s3_download_file(key)
        ext = os.path.splitext( local_fname)[1]
        pieces = key.split('_')
        gallery_id = pieces[2] 
        s3name = f'''{DOWNLOAD_FOLDER}/{basename}{ext}'''
        shutil.move( local_fname, s3name)
        _resize_media( [s3name], gallery_id, size)
        os.remove(s3name)

    # Find all large images
    large_images = s3_get_keys( s3_client, LARGE_FOLDER)
    large_images = [ os.path.splitext(x['Key'])[0] for x in large_images ]
    # Find all medium images
    medium_images = [ x.replace('/large/','/medium/') for x in large_images ]
    medium_images = [ x.replace('/lg_','/med_') for x in medium_images ]
    # Find all small images
    small_images = [ x.replace('/large/','/small/') for x in large_images ]
    small_images = [ x.replace('/lg_','/sm_') for x in small_images ]

    # Find missing small images
    existing_small_images = s3_get_keys( s3_client, SMALL_FOLDER)
    existing_small_images = [ os.path.splitext(x['Key'])[0] for x in existing_small_images ]
    missing_small_images = [ x for x in small_images if not x in existing_small_images ]

    # Generate missing small images
    for x in missing_small_images:
        log( f'''gen_thumbnails(): generating {x}''')
        idx = small_images.index(x)
        convert( large_images[idx], 'small')

    # Find missing medium images
    existing_medium_images = s3_get_keys( s3_client, MEDIUM_FOLDER)
    existing_medium_images = [ os.path.splitext(x['Key'])[0] for x in existing_medium_images ]
    missing_medium_images = [ x for x in medium_images if not x in existing_medium_images ]

    # Generate missing medium images
    for x in missing_medium_images:
        log( f'''gen_thumbnails(): generating {x}''')
        idx = medium_images.index(x)
        convert( large_images[idx], 'medium')

    log('Done.')

def f01_unzip(fname):
    """ Unzip if its a zip file and kick off the pipeline """
    subfolder = f'''{os.path.split(fname)[0]}/unzipped'''
    with ZipFile( fname, 'r') as zf:
        zf.extractall( path=subfolder)
    files = list_files(subfolder)
    files = [ x for x in files if os.path.splitext(x)[1] ]
    return files

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
    blurb = ''
    ext = os.path.splitext(s3name)[1].lower()
    if ext not in MEDIA_EXTENSIONS:
        blurb = os.path.split(orig_fname)[1]
    data = {
        'id':pic_id
        ,'gallery_id':gallery_id
        ,'blurb':blurb
        ,'filename':s3name
        ,'orig_fname': os.path.split(orig_fname)[1]
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
    subfolder = os.path.split(fname)[0]
    fnames = [fname]
    if os.path.splitext(fname)[1].lower() == '.zip':
        fnames = f01_unzip( fname)
    for idx,fname in enumerate(fnames):
        _set_gallery_status( gallery_id, f'''Adding image {fname} ({idx+1}/{len(fnames)})''')
        pic_id = shortuuid.uuid()
        ext = os.path.splitext(fname)[1].lower()
        #path = os.path.split(fname)[0]
        #s3name = f'''{path}/{pic_id}_{gallery_id}{ext}'''
        s3name = f'''{DOWNLOAD_FOLDER}/{pic_id}_{gallery_id}{ext}'''
        localfname = helpers.s3_download_file( fname)
        shutil.copyfile( localfname, s3name)
        if ext in MEDIA_EXTENSIONS:
            f02_gen_thumbs( s3name, gallery_id)
        else:
            target_name = f'''pics_complete/{pic_id}_{gallery_id}{ext}'''
            s3_upload_files( [s3name], [target_name])

        f03_insert_db( s3name, fname, gallery_id, pic_id)
        os.remove( localfname)
        os.remove( s3name)
    _set_gallery_status( gallery_id, f'ok')
    log( f'''WORKER:  add_new_images() done''')

def add_title_image( fname, gallery_id):
    """ Add new title image to a gallery """
    log( f'''WORKER:  add_title_image( {fname}, {gallery_id}) starting''')
    _set_gallery_status( gallery_id, f'''Adding title image {fname}''')

    subfolder = os.path.split(fname)[0]
    pic_id = shortuuid.uuid()
    ext = os.path.splitext(fname)[1].lower()
    if not ext in MEDIA_EXTENSIONS:
        log( f'''WORKER:  add_title_image(): Unknown extension {ext}. Ignoring.''')
        shutil.rmtree(subfolder)   
        return
        
    s3name = f'''{DOWNLOAD_FOLDER}/{pic_id}_{gallery_id}{ext}'''
    localfname = helpers.s3_download_file( fname)
    shutil.copyfile( localfname, s3name)
    f02_gen_thumbs( s3name, gallery_id)
    f03_insert_db( s3name, fname, gallery_id, pic_id)
    sql = f''' update picture set title_flag = false where gallery_id=%s'''
    pg.run( sql, [gallery_id])
    sql = f''' update picture set title_flag = true where id=%s '''
    pg.run( sql, [pic_id])
    os.remove( localfname)
    os.remove( s3name)
    _set_gallery_status( gallery_id, f'ok')
    log( f'''WORKER:  add_title_image() done''')
