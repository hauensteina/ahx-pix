"""
gui.py
Andreas Hauenstein
Created: Jan 2023

Functions to generate sql for the GUI
"""

from flask import url_for
from mod_ahx_pics import AppError
from mod_ahx_pics.helpers import pexc

def gen_gallery_list( galleries, action1, title1, action2='', title2=''):
    """
    Generate html to display a list of galleries
    If action is given, a link with that action is generated on the right.
    For styling, use class dbtable in main.css .
    """
    try:
        columns = { 'Title':'title', 'Owner':'username', 'Date':'create_date', 'Hits':'n_hits' }
        # Table header
        theader = ''
        for col in columns:
            theader += H('th',col)
        theader = H('tr',theader)
        # Table body
        tbody = ''
        for idx,gal in enumerate(galleries):
            trow = ''
            for col in columns:
                val = gal[columns[col]]
                trow += H('td',val)
            if action1:    
                trow += H('td', _gen_gallery_link( gal, action1, title1))   
            if action2:   
                trow += H('td', _gen_gallery_link( gal, action2, title2))    
            trow = H('tr',trow) 
            tbody += trow
        html = H('table class="gallery-list"', theader + tbody)
        return html
    except Exception as e:
        raise AppError(pexc(e))

def _gen_gallery_link( gallery, action, title):   
    """ Generate an html link to a gallery """
    url = url_for( 'gallery', 
                   _id=gallery['id'], _action=action)
    link = H(f'a href={url}', title)
    return link

def _html_tag( tag, content='', style=''):
    """
    Make a piece of HTML surrounded by tag,
    with content and style. Plus a hack for images.
    Examples: 
    html_tag('div','hello')
    html_tag('div', ('fig.png','width:100px'))
    """
    if content is None: content = ''
    res = '\n'
    if type(content) not in  [list,tuple]:
        content = [content,'']
    cont = content[0]
    contstyle = content[1]
    res += f'<{tag} '
    res += f'style="{style}">\n'
    if type(cont) == str and (cont[-4:] in ('.png', '.svg')):
        cont = f'<img src="{cont}" style="{contstyle}">'
    res += f'{cont}\n' 
    res += f'</{tag.split()[0]}>\n'
    return res
# short function alias
H = _html_tag 

