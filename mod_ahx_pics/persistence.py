"""
persistence.py
Andreas Hauenstein
Created: Jan 2023

Functions to abstract all data persistence stuff, like postgres and S3 access.
"""

from mod_ahx_pics import pg

def get_galleries( username=None, public_only=True):
    """
    Get all galleries as a list of dicts. If username is given, only 
    those owned by that user.
    """

    where = ' where true '
    if public_only: where += ' and private_flag = false '
    if username: where += ' and owner_id = username '
    sql = f'''
    select * from gallery {where} order by title
    '''

    rows = pg.select(sql)
    return rows
