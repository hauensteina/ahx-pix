# /********************************************************************
# Filename: mod_ahx_pix/create_tables.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/
#
# Create any missing DB tables and fill them with initial values
#

from pdb import set_trace as BP
from datetime import datetime, date
from mod_ahx_pix import pg # postgres connection
from mod_ahx_pix import auth

def create_tables( pg):
    _create_login( pg)
    _create_gallery( pg)
    _create_picture( pg)
    _create_img_url_cache( pg) 

def _create_login( pg):
    tabname = 'login'
    if pg.table_exists( tabname): return

    sql = f'''
    create table {tabname} (
      email text
      ,username text
      ,password text
      ,fname text
      ,lname text
      ,admin_flag Boolean
      ,create_date date
      ,change_date date
    )
    '''
    pg.run(sql)
    today = date.today()
    user = auth.User('hauensteina@gmail.com')
    data = { 
        'email':'hauensteina@gmail.com'
        ,'username':'ahn'
        ,'fname':'Andreas'
        ,'lname':'Hauenstein'
        ,'admin_flag':True
        ,'create_date':today
        ,'change_date':today
    }   
    user.create_user( data, 'welcome321!')
    user = auth.User('jc.chetrit@gmail.com')
    data = { 
        'email':'jc.chetrit@gmail.com'
        ,'username':'jc'
        ,'fname':'Jean Claude'
        ,'lname':'Chetrit'
        ,'admin_flag':False
        ,'create_date':today
        ,'change_date':today
    }   
    user.create_user( data, 'welcome321!')
    user = auth.User('jsh@gmail.com')
    data = { 
        'email':'jsh@gmail.com'
        ,'username':'jsh'
        ,'fname':'Joe'
        ,'lname':'Schmoe'
        ,'admin_flag':False
        ,'create_date':today
        ,'change_date':today
    }   
    user.create_user( data, 'welcome321!')

def _create_gallery( pg):
    tabname = 'gallery'
    if pg.table_exists( tabname): return

    sql = f'''
    create table {tabname} (
      id text
      ,username text
      ,title text
      ,blurb text

      -- Three types of gallery: private (just me tf), public (the world ft), and shared (all logins ff)
      ,private_flag boolean default true
      ,public_flag boolean default false
      ,n_hits int
      ,create_date date
      ,change_date date
      ,deleted_flag boolean not null default false
      ,piclist text not null default ''::text
      ,status text not null default ''::text
      ,title_pic_caption text
      ,layout text -- multi_column or single_column
      ,show_title_pic_flag boolean default true
    )
    '''
    pg.run(sql)

def _create_picture( pg):
    tabname = 'picture'
    if pg.table_exists( tabname): return

    sql = f'''
    create table {tabname} (
      id text
      ,gallery_id text
      ,blurb text
      ,filename text
      ,orig_fname text
      ,position int
      ,title_flag boolean
      ,create_date date
      ,change_date date
      ,pic_taken_ts timestamp
      ,deleted_flag boolean not null default false
    )
    '''
    pg.run(sql)

def _create_img_url_cache( pg):
    """
    Cache presigned URLs for each gallery. 
    Stored as json text, see persistence.py .
    """
    tabname = 'img_url_cache'
    if pg.table_exists( tabname): return

    sql = f'''
    create table {tabname} (
      gallery_id text
      ,url_json text
      ,replace_ts timestamp
    )
    '''
    pg.run(sql)


