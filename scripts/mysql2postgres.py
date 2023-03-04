#!/usr/bin/env python

'''
Read old bgc data from mysql and store them in postgres
AHN, Jan 2023
'''

import sys,os,re
import argparse
from pdb import set_trace as BP
import mysql.connector

from os.path import dirname
sys.path.append( f'{dirname(__file__)}/..')

from mod_ahx_pics.postgres import Postgres 

pg = Postgres( os.environ['AHX_PICS_LOCAL_DB_URL'])

def usage(printmsg=False):
    name = os.path.basename( __file__)
    msg = f'''
    Name:
      {name}: Read old bgc data from mysql and store them in postgres
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
    rows = read_topics()
    insert_gallery(rows)
    #rows = read_pics()
    #insert_picture(rows)

def insert_gallery(rows):
    newrows = []
    for row in rows:
        nr = {}
        nr['id'] = str(row['topic_id'])
        nr['username'] = 'ahn' if row['user_id'] == 19 else 'jc'
        nr['title'] = row['topic_name']
        nr['blurb'] = row['text']
        nr['private_flag'] = False if row['visibility'] == 'public' else True
        nr['create_date'] = row['date_started']
        nr['change_date'] = row['date_changed']
        newrows.append(nr)
    pg.insert( 'gallery', newrows)

def insert_picture(rows):
    newrows = []
    for row in rows:
        nr = {}
        nr['id'] = str(row['pic_id'])
        nr['gallery_id'] = str(row['topic_id'])
        nr['blurb'] = row['caption']
        nr['filename'] = row['filename']
        nr['position'] = row['position']
        nr['title_flag'] = True if row['type'] == 'primary' else False
        nr['create_date'] = row['date_submitted']
        nr['change_date'] = row['date_submitted']
        newrows.append(nr)
    pg.insert( 'picture', newrows)

def read_topics():
    msql = mysql.connector.connect(user='root', password='Hikaru01',
                                   host='127.0.0.1',
                                   database='bgc')
    sql = f'''
    select * from rescue_topics
    '''
    curs = msql.cursor(dictionary=True)
    curs.execute( sql)
    rows = []
    for row in curs:
        rows.append(row)
    return rows

def read_pics():
    msql = mysql.connector.connect(user='root', password='Hikaru01',
                                   host='127.0.0.1',
                                   database='bgc')
    sql = f'''
    select * from picture where
    topic_id in (select topic_id from rescue_topics)
    '''
    curs = msql.cursor(dictionary=True)
    curs.execute( sql)
    rows = []
    for row in curs:
        rows.append(row)
    return rows

if __name__ == '__main__':
  main()

