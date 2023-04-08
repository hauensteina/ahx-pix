#!/usr/bin/env python

'''
Back up all ahx-pix data
AHN, Apr 2023
'''

import sys,os,re
import argparse
from pdb import set_trace as BP
import boto3

from os.path import dirname
sys.path.append( f'{dirname(__file__)}/..')

from mod_ahx_pics.postgres import Postgres 

PROD_BUCKET = 'ahx-pics'
BACKUP_BUCKET = 'ahx-pics-backup'

BACKUP_FOLDER = '/Volumes/One Touch/ahx-pics'

def usage(printmsg=False):
    name = os.path.basename( __file__)
    msg = f'''
    Name:
      {name}: Back up all ahx-pix data
    Synopsis:
      python {name} --mode [ DB | S3 | local |all ]
    Description:
      --mode DB: Back up Heroku postgres to local postgres  
      --mode S3: Back up pictures to another S3 bucket
      --mode local: Back up pictures to local disk
      --mode all: All of the above
    Example:
      python {name} --mode S3 

--
''' 
    if printmsg:
        print(msg)
        exit(1)
    else:
        return msg

def main():
    parser = argparse.ArgumentParser(usage=usage())
    parser.add_argument( "--mode", required=True, choices=['DB','S3', 'local', 'all'])
    args = parser.parse_args()
    if args.mode in ['DB', 'all']:
        copy_db()
    if args.mode in ['S3', 'all']:
        copy_s3()
    if args.mode in ['local', 'all']:
        copy_local()

def copy_s3():
    print(f'Copying pics from bucket {PROD_BUCKET} to {BACKUP_BUCKET} ...')

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_KEY'],
        aws_secret_access_key=os.environ['AWS_SECRET']
    )

    paginator = s3.get_paginator('list_objects_v2')    
    pages = paginator.paginate(Bucket=PROD_BUCKET)
    n_copied = 0
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                if n_copied % 100 == 0 or n_copied < 10: print(f'Copied {n_copied} ...')
                key = obj['Key']
                s3.copy_object(Bucket=BACKUP_BUCKET, CopySource=f'{PROD_BUCKET}/{key}', Key=key)
                n_copied += 1

    print(f'Copied {n_copied} objects.')
    print('Done.')

def copy_local():
    print(f'Copying pics from bucket {PROD_BUCKET} to local folder {BACKUP_FOLDER} ...')

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_KEY'],
        aws_secret_access_key=os.environ['AWS_SECRET']
    )

    paginator = s3.get_paginator('list_objects_v2')    
    pages = paginator.paginate(Bucket=PROD_BUCKET)
    n_copied = 0
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                if n_copied % 100 == 0 or n_copied < 10: print(f'Copied {n_copied} ...')
                key = obj['Key']
                path, _ = os.path.split(key)
                local_path = os.path.join(BACKUP_FOLDER, path)
                local_filename = os.path.join(BACKUP_FOLDER, key)
    
                if not os.path.exists(local_path):
                    os.makedirs(local_path)

                s3.download_file(PROD_BUCKET, key, local_filename)    
                n_copied += 1

    print(f'Copied {n_copied} objects.')
    print('Done.')

def copy_db():
    source_url = os.environ['PIX_DB_URL']
    target_url = os.environ['AHX_PIX_LOCAL_DB_URL']
    db_source = Postgres(source_url)
    db_target = Postgres(target_url)
    print(f'Copying {source_url} to {target_url} ...')
    copy_table( 'login', db_source, db_target)
    copy_table( 'gallery', db_source, db_target)
    copy_table( 'picture', db_source, db_target)
    print('Done.')

def copy_table( table, db_source, db_target):
    print( f'Reading source for table {table} ...')
    rows = db_source.slurp( table)
    print( f'Read {len(rows)} rows')  
    #yn = input( 'Continue? (y/n) ')
    #if yn != 'y':
    #    print( 'Aborted.')
    #    return
    print( 'Clearing target ...')
    db_target.run( f'delete from {table}')
    print('Inserting into target ...')
    db_target.insert( table, rows) 
    print( 'Done.')

if __name__ == '__main__':
  main()

