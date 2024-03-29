"""
persistence.py
Andreas Hauenstein
Created: Jan 2023

Functions to abstract all data persistence stuff, like postgres and S3 access.
"""

from pdb import set_trace as BP
from datetime import datetime, timedelta, date
import json
from flask_login import current_user
from mod_ahx_pix import pg, log, logged_in
from mod_ahx_pix import SMALL_FOLDER, MEDIUM_FOLDER, LARGE_FOLDER, LINK_EXPIRE_HOURS
import mod_ahx_pix.helpers as helpers

def get_galleries( title='', owner='', body='', gallery_id='', order_by='create_date desc'):
    """
    Get galleries as a list of dicts. Filter by title and owner.
    """
    username = current_user.data['username'] if logged_in() else ''
    if not username:
        where = f''' where deleted_flag = false and public_flag = true '''
    else:   
        where = f''' where deleted_flag = false and (username='{username}' or private_flag = false)  '''

    if owner: where += f''' and lower(username) like '%%{owner.lower()}%%' '''
    if title: where += f''' and lower(title) like '%%{title.lower()}%%' '''
    if gallery_id: where += f''' and id = '{gallery_id}' '''
    sql = f'''
    select id from gallery {where} order by {order_by} limit 200
    '''
    title_matching_rows = pg.select(sql)
    ids = [ x['id'] for x in title_matching_rows ]
    rows = find_galleries_with_text(ids, body, order_by)
    return rows

def get_my_galleries( title='', body='', order_by='create_date desc'):
    """
    Get my galleries as a list of dicts. Filter by title.
    """
    username = current_user.data['username'] if logged_in() else ''
    if not username:
        where = f''' where deleted_flag = false and public_flag = true '''
    else:   
        where = f''' where deleted_flag = false and username = '{username}' '''

    if title: where += f''' and lower(title) like '%%{title.lower()}%%' '''
    sql = f'''
    select id from gallery {where}  
    '''
    title_matching_rows = pg.select(sql)
    ids = [ x['id'] for x in title_matching_rows ]
    rows = find_galleries_with_text(ids, body, order_by)
    return rows

def find_galleries_with_text(ids, text, order_by):
    """
    Find galleries with any word in text in their blurb.
    """
    if not ids: return []
    words = text.split()
    words = [ w.lower() for w in words]
    
    wordsql = ''
    for idx,w in enumerate(words):
        if idx > 0: wordsql += ' or ' 
        wordsql += f''' lower(blurb) like '%%{w}%%' '''
    
    placeholders = ','.join( ['%s'] * len(ids))
    
    if not wordsql: wordsql = 'true'
    
    sql = f'''
    select id from gallery 
    where 
      id in ({placeholders}) 
      and ( {wordsql} ) 
    union distinct
      select gallery_id from picture
    where 
      gallery_id in ({placeholders}) 
      and ( {wordsql} ) 
      
    '''
    gallery_ids = pg.select(sql, ids + ids)
    gallery_ids = [ x['id'] for x in gallery_ids ]
    if not gallery_ids: return []
    placeholders = ','.join( ['%s'] * len(gallery_ids))
    
    # Get the gallery objects for the gallery ids
    sql = f'''
    select * from gallery where id in ({placeholders}) order by {order_by}
    '''    
    galleries = pg.select(sql, gallery_ids)
    return galleries

def get_gallery_pics( gallery_id):
    """ Get gallery pics, sorted by gallery.piclist """

    def add_pics_to_piclist( gallery, pics):
        """ 
        The gallery table has a list defining the order of the pics.
        Add any missing pics at the end of the list.
        """
        piclist = []
        if gallery['piclist']:
            piclist = json.loads( gallery['piclist'])
        newpics = []
        for pic in pics:
            if not pic['id'] in piclist:
                newpics.append( pic['id'])
        piclist += newpics
        pg.update_row( 'gallery', 'id', gallery['id'], { 'piclist': json.dumps(piclist) }) 
        return piclist

    gallery = pg.select(f'''select * from gallery where id = '{gallery_id}' ''')[0]
    pics = pg.select( f''' select * from picture where gallery_id = '{gallery_id}' and deleted_flag = false order by position ''')
    piclist = add_pics_to_piclist( gallery, pics)
    pics = sorted( pics, key = lambda x: piclist.index(x['id']))
    return pics

def get_title_pic( gallery_id):
    """ Get the gallery title pic """
    pics = pg.select( f''' select * from picture where gallery_id = '{gallery_id}' and deleted_flag = false and title_flag = true ''')
    if pics: return pics[0]
    return None

def gallery_changed(gallery_id):
    pg.run( 'update gallery set change_date = %s where id = %s', (date.today(), gallery_id))

def get_gallery_links( gallery_id):
    """
    Get presigned S3 links for all small and medium pics. 
    They are kept in a table in the DB so they don't change all the time and
    cause image reloads.
    If they are about to expire or a link is not found, make new ones.
    Link data structure: 
    { 'sm_6917_423_0':'https://ahx-pics.s3.amazonaws.com/pics/small/423/sm_6917_423_0.jpeg?AWSAccessKeyId=...'
    ,'med_6801_423_2':'https://ahx-pics.s3.amazonaws.com/pics/medium/423/med_6801_423_2.jpeg?AWSAccessKeyId=...'
    , ... }
    """

    def pic_keys( pic):
        fname = helpers.basename(pic['filename'])
        small_key = 'sm_' + fname
        medium_key = 'med_' + fname
        large_key = 'lg_' + fname
        return small_key, medium_key, large_key
        
    def needs_regen( links, pics):
        """
        Links need regenerating if
        (a) At least one is missing or
        (b) replace_ts is in the past 
        """
        if not links: return True
        links = links[0]
        if links['replace_ts'] < datetime.utcnow():
            log( 'link cache out of date')
            return True
        links = json.loads( links['url_json'])
        for pic in pics:
            small_key, medium_key, large_key = pic_keys( pic)
            if not small_key in links:
                log( small_key + ' not found in link cache')
                return True
            if not medium_key in links:
                log( medium_key + ' not found in link cache')
                return True
            if not large_key in links:
                log( large_key + ' not found in link cache')
                return True
        return False

    def regen_links( gallery_id, pics, folder=''):
        if not folder:
            slinks, timeout = regen_links( gallery_id, pics, SMALL_FOLDER)
            mlinks, timeout = regen_links( gallery_id, pics, MEDIUM_FOLDER)
            llinks, timeout = regen_links( gallery_id, pics, LARGE_FOLDER)
            links = slinks | mlinks | llinks
            return links, timeout
        img_prefix = folder + gallery_id + '/'
        s3_client = helpers.s3_get_client()
        images = helpers.s3_get_keys( s3_client, img_prefix)
        links = { helpers.basename(x['Key']) : helpers.s3_get_link( s3_client, x['Key'], LINK_EXPIRE_HOURS) 
                  for x in images }
        timeout = datetime.utcnow() + timedelta( hours=LINK_EXPIRE_HOURS)
        return links, timeout

    def store_links( gallery_id, links, timeout):
        pg.run( f''' delete from img_url_cache where gallery_id = %s ''', [gallery_id] )
        jlinks = json.dumps(links)
        pg.insert( 'img_url_cache', [ { 'gallery_id':gallery_id, 'url_json':jlinks, 'replace_ts':timeout } ])

    pics = get_gallery_pics( gallery_id)
    sql = f'''
    select * from img_url_cache where gallery_id = %s
    '''
    links = pg.select( sql, [gallery_id])
    if needs_regen( links, pics):
        log( f'''Regenerating pic links for gallery {gallery_id}''')
        links, timeout = regen_links( gallery_id, pics)
        store_links( gallery_id, links, timeout)
        links = pg.select( sql, [gallery_id])

    links = json.loads( links[0]['url_json'])
    return links


