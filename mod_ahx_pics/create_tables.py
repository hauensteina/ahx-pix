# /********************************************************************
# Filename: mod_ahx_pics/create_tables.py
# Author: AHN
# Creation Date: Jan, 2023
# **********************************************************************/
#
# Create any missing DB tables and fill them with initial values
#

from pdb import set_trace as BP
from datetime import datetime, date
from mod_ahx_pics import pg # postgres connection
from mod_ahx_pics import auth

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
      ,password text
      ,fname text
      ,lname text
      ,admin_flag Boolean
      ,create_date date
      ,change_date date
    )
    '''
    pg.run(sql)
    user = auth.User('hauensteina@gmail.com')
    today = date.today()
    data = { 
        'email':'hauensteina@gmail.com'
        ,'fname':'Andreas'
        ,'lname':'Hauenstein'
        ,'admin_flag':True
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
      ,private_flag boolean
      ,n_hits int
      ,create_date date
      ,change_date date
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
      ,position int
      ,title_flag boolean
      ,create_date date
      ,change_date date
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


