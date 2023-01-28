#!/usr/bin/env python

'''
Remove images from S3 if they do not belong to one of the galleries in the DB
AHN, Jan 2023
'''

import sys,os,re
import argparse
from pdb import set_trace as BP

from os.path import dirname
sys.path.append( f'{dirname(__file__)}/..')

from mod_ahx_pics.postgres import Postgres
import mod_ahx_pics.helpers as helpers
from mod_ahx_pics import log

pg = Postgres( os.environ['AHX_PICS_LOCAL_DB_URL'])

def usage(printmsg=False):
    name = os.path.basename( __file__)
    msg = f'''
    Name:
      {name}: Remove images from S3 if they do not belong to one of the galleries in the DB
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
    gallery_ids = get_gallery_ids()
    delete_unused( gallery_ids, 'pics/small/')
    delete_unused( gallery_ids, 'pics/medium/')
    delete_unused( gallery_ids, 'pics/orig/')
    log('Done.')
    
def delete_unused( gallery_ids, s3_prefix):
    keys = helpers.s3_get_keys( s3_prefix)
    key2gallery = { k:k.split('_')[-2] for k in keys }
    unused_keys = [ k for k in key2gallery if key2gallery[k] not in gallery_ids ]
    helpers.s3_delete_files( unused_keys)

def get_gallery_ids():
    sql = f'''
    select distinct id from gallery order by 1
    '''
    rows = pg.select(sql)
    ids = [ x['id'] for x in rows ]
    return ids


if __name__ == '__main__':
  main()

