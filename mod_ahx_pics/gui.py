"""
gui.py
Andreas Hauenstein
Created: Jan 2023

Functions to generate html for the GUI
"""

from pdb import set_trace as BP
from flask import url_for
from mod_ahx_pics import AppError, SMALL_FOLDER
from mod_ahx_pics.helpers import pexc
import mod_ahx_pics.helpers as helpers

def gen_gallery_as_table( gallery, pics, n_cols=5):
    """
    Generate html to display all pics in a gallery in table format.
    Gallery title and blurb at the top.
    """
    html = ''
    # Heading
    html += f'''
    <div class="row gallery-title">
    {gallery['title']}
    </div>
    '''
    # Title pic
    title_pic = [x for x in pics if x['title_flag']]
    if title_pic:
        title_pic = title_pic[0]
        img_prefix = helpers.s3_prefix( title_pic['filename'], size='medium')
        keys, _ =  helpers.s3_get_keys( img_prefix)
        key = 'pics/img_not_found.jpg'
        if keys: key = keys[0]['Key']
        img_link, _  = helpers.s3_get_link( key)
        html += f'''<img src='{img_link}' id='gallery_img' class='gallery-title-img'>'''
        html += f'''<span class='gallery-title-blurb'>{title_pic['blurb']}</span>'''
    else:
        html += f''' 
        <img src='img_not_found.jpg'> 
        '''
        
    # Blurb
    html += f'''
    <div id='gallery_blurb' class=gallery-blurb>
    {gallery['blurb']}
    </div> 
    '''
    # Images
    html += _gen_image_grid( gallery, pics, n_cols)
    return html

def _gen_image_grid( gallery, pics, n_cols):
    """ Arrange image thumbs as a grid """
    
    s3_client = ''
    html = f'''<table class=gallery-table> ''' 
    colw = f'{100.0/n_cols}%'
    img_prefix = SMALL_FOLDER + gallery['id'] + '/'
    images, s3_client =  helpers.s3_get_keys( img_prefix)
    keys = [ x['Key'] for x in images ]
    id2key = { k.split('_')[1]:k for k in keys }

    for left_idx in range( 0, len(pics), n_cols):
        html += f''' <tr> \n ''' 
        for col in range(n_cols):
            idx = left_idx + col
            if idx >= len(pics): break
            pic = pics[idx]
            #img_prefix = helpers.s3_prefix( pic['filename'], size='small')
            #keys, s3_client =  helpers.s3_get_keys( img_prefix, s3_client)
            key =  id2key.get( pic['id'], 'pics/img_not_found.jpg')
            img_link, s3_client = helpers.s3_get_link( key, s3_client)
            visit_url = f''' '{url_for( "carousel", gallery_id=gallery["id"], picture_id=pic["id"])}' '''
            onclick = f''' onclick="window.location.href={visit_url}" '''
            html += f''' <td class='gallery-thumb' style='width:{colw};' > '''
            html += f''' <img loading='lazy' {onclick} src='{img_link}' style='width:100%;'>\n '''
            html += f''' <br>{pic['blurb']} '''
        html += '</tr>'
    html += f'''</table>'''
    return html

def gen_gallery_list( galleries, action1='', title1='', action2='', title2=''):
    """
    Generate html to display a list of galleries
    If action is given, a link with that action is generated on the right.
    For styling, use class dbtable in main.css .
    """
    columns = { 'Title':'title', 'Owner':'username', 'Date':'create_date'} # , 'Hits':'n_hits' }
    # Table header
    theader = ''
    for col in columns:
        theader += H('th',col)
    theader = H('tr',theader)
    # Table body
    tbody = ''
    for idx,gal in enumerate(galleries):
        visit_url = f"'{url_for( 'gallery', gallery_id=gal['id'])}'"
        trow = ''
        for col in columns:
            val = gal[columns[col]]
            if col in (('Owner','Date')):
                trow += H('td align=center',val)
            else:
                trow += H(f'td',val)
        if action1:    
            trow += H('td', _gen_gallery_link( gal, action1, title1))   
        if action2:   
            trow += H('td', _gen_gallery_link( gal, action2, title2))    
        trow = H(f'tr onclick="window.location.href={visit_url}"',trow) 
        tbody += trow
    html = H('table class="gallery-list"', theader + tbody)
    return html

def gen_gallery_search( title='', owner=''):
    """ Generate a form to search galleries by title and owner """

    html = f'''
    <form method=post class=search_form>
      <input type=hidden name=_action value="search_gallery">
      <div class="row">
        <div class="column right-space-20">
          <div>Title:</div>
          <div> 
             <input type=text name=title size={20} value="{title}">
          </div>
        </div>
        <div class="column right-space-20">
          <div>Owner:</div>
          <div> 
            <input type=text name=owner size={20} value="{owner}">
          </div>
        </div>
        <div class="column">
          <div>&nbsp;</div>
          <div> <input type=submit name=btn_search value=Search > </div>
        </div>
      </div>  
    </form>
    '''
    return html

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

