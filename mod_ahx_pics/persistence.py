"""
persistence.py
Andreas Hauenstein
Created: Jan 2023

Functions to abstract all data persistence stuff, like postgres and S3 access.
"""

from pdb import set_trace as BP
from mod_ahx_pics import pg

def get_galleries( title='', owner=''):
    """
    Get galleries as a list of dicts. Filter by title and owner.
    TODO: If logged in, show private pages of user. 
    """

    where = ' where true '
    if owner: where += f''' and lower(username) like '%%{owner.lower()}%%' '''
    if title: where += f''' and lower(title) like '%%{title.lower()}%%' '''
    sql = f'''
    select * from gallery {where} order by create_date desc
    '''

    rows = pg.select(sql)
    return rows
