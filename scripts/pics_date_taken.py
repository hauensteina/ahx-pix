#!/usr/bin/env python

'''
Get date taken for all pics in DB
AHN, Sep 2023
'''

from datetime import datetime
import sys,os,re
import argparse
from pdb import set_trace as BP

from PIL import Image
from PIL.ExifTags import TAGS

from os.path import dirname
sys.path.append( f'{dirname(__file__)}/..')

from mod_ahx_pix.postgres import Postgres
import mod_ahx_pix.helpers as helpers
from mod_ahx_pix import log

pg = Postgres( os.environ['AHX_PIX_LOCAL_DB_URL'])

def usage(printmsg=False):
    name = os.path.basename( __file__)
    msg = f'''
    Name:
      {name}: Update pic_taken_ts from exif data if it is null.  
    Example:
      python {name} --run

--
''' 
    if printmsg:
        print(msg)
        exit(1)
    else:
        return msg

def main():
    parser = argparse.ArgumentParser(usage=usage())
    parser.add_argument( "--run", required=True, action='store_true')
    args = parser.parse_args()
    run()

def run():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    galleries = get_galleries()
    galleries = [ x for x in galleries if x['title'] == 'Year 2022' ]
    sql = f''' update picture set pic_taken_ts = %s where id = %s '''
    for idx,g in enumerate(galleries):
        print(f'>>> Gallery {idx+1}/{len(galleries)}:{g["title"]}')
        gid = g['id']
        pics = pg.select( f''' select * from picture where gallery_id = '{gid}' and deleted_flag = false order by filename''')
        for p in pics:
            if p['pic_taken_ts']: continue
            print(f'>>>>>> Pic:{p["id"]}')
            s3_path = helpers.s3_path_for_pic( gid, p['id'], 'large') 
            local_fname = helpers.s3_download_file( s3_path)
            date_taken = helpers.get_pic_date(local_fname)
            pg.run( sql, (date_taken, p['id']) )
            os.remove(local_fname)
    print('Done.')
    
def get_galleries():
    sql = f'''
    select distinct id,title,create_date from gallery order by create_date desc
    '''
    rows = pg.select(sql)
    return rows


if __name__ == '__main__':
  main()

