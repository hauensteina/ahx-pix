#!/usr/bin/env python

'''
Copy the PIX Postgres DB from dev to prod or the other way round
AHN, Jan 2023
'''

import sys,os,re
import argparse
from pdb import set_trace as BP
import mysql.connector

from os.path import dirname
sys.path.append( f'{dirname(__file__)}/..')

from mod_ahx_pics.postgres import Postgres 

def usage(printmsg=False):
    name = os.path.basename( __file__)
    msg = f'''
    Name:
      {name}: Copy the PIX Postgres DB from dev to prod or the other way round
    Example:
      python {name} --direction dev2prod

--
''' 
    if printmsg:
        print(msg)
        exit(1)
    else:
        return msg

def main():
    parser = argparse.ArgumentParser(usage=usage())
    parser.add_argument( "--direction", required=True, choices=['dev2prod','prod2dev'])
    args = parser.parse_args()
    run(args.direction)

def run( direction):
    if direction == 'dev2prod':
        yn = input("Are you really really sure you want to overwrite the production DB? (YES/No) ")
        if yn != 'YES':
            print('Bugging out.')
            exit(0)

    if direction == 'dev2prod':
        db_target = Postgres( os.environ['PIX_DB_URL'])
        db_source =  Postgres( os.environ['AHX_PIX_LOCAL_DB_URL'])
    else:
        db_source = Postgres( os.environ['PIX_DB_URL'])
        db_target =  Postgres( os.environ['AHX_PIX_LOCAL_DB_URL'])
        
    copy_table( 'login', db_source, db_target)
    copy_table( 'gallery', db_source, db_target)
    copy_table( 'picture', db_source, db_target)

def copy_table( table, db_source, db_target):
    print( f'Reading source for table {table} ...')
    rows = db_source.slurp( table)
    print( f'Read {len(rows)} rows')  
    yn = input( 'Continue? (y/n) ')
    if yn != 'y':
        print( 'Aborted.')
        return
    print( 'Clearing target ...')
    db_target.run( f'delete from {table}')
    print('Inserting into target ...')
    db_target.insert_bulk( table, rows) 
    print( 'Done.')

if __name__ == '__main__':
  main()

