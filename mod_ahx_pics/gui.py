"""
gui.py
Andreas Hauenstein
Created: Jan 2023

Functions to generate html for the GUI
"""

from pdb import set_trace as BP
import os
from flask import url_for
from mod_ahx_pics import AppError, SMALL_FOLDER
from mod_ahx_pics import IMG_EXTENSIONS, VIDEO_EXTENSIONS
from mod_ahx_pics.helpers import pexc
import mod_ahx_pics.helpers as helpers
import mod_ahx_pics.persistence as pe

def gen_carousel_images( gallery_id, active_pic_id):
    images = []
    s3_client = ''
    found_active = False
    pics = pe.get_gallery_pics( gallery_id) # pic filenames in DB 
    pic_links = pe.get_gallery_links( gallery_id) # image files in S3
    for i,pic in enumerate(pics):
        furl = pic_links.get( 'med_' + helpers.basename( pic['filename']), 'static/images/img_not_found.png')
        ext = os.path.splitext(pic['filename'])[1].lower()
        classes = " class='ahx-slide' "
        #if i == 0: classes = " class='ahx-slide ahx-active' "
        if pic['id'] == active_pic_id: 
            found_active = True
            classes = " class='ahx-slide ahx-active' "
        if ext in VIDEO_EXTENSIONS:
            link = f"<li> <video preload='none' controls {classes}>  <source data-src='{furl}#t=0.5'></video> </li>"
        elif ext in IMG_EXTENSIONS:
            link = f"<li> <img loading='lazy' data-src='{furl}' {classes}> </li>"
        else:
            log(f'ERROR: unknown media extension .{ext}. Ignoring {f}')
            continue
        images.append(link)
    if not found_active:
        images[0] = images[0].replace('ahx-slide', 'ahx-slide ahx-active')
    images = '\n'.join(images)
    return images

def gen_gallery_as_table( gallery, pics, n_cols=5):
    """
    Generate html to display all pics in a gallery in table format.
    Gallery title and blurb at the top.
    """
    pic_links = pe.get_gallery_links( gallery['id'])
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
        img_link = pic_links.get( 'med_' + helpers.basename( title_pic['filename']), 'static/images/img_not_found.jpg')
        html += f'''<img src='{img_link}' id='gallery_img' class='gallery-title-img'>'''
        html += f'''<span class='gallery-title-blurb'>{title_pic['blurb']}</span>'''
    else:
        html += f''' 
        <img src='static/images/img_not_found.jpg'> 
        '''
        
    # Blurb
    html += f'''
    <div id='gallery_blurb' class=gallery-blurb>
    {gallery['blurb']}
    </div> 
    '''
    # Images
    html += _gen_image_grid( gallery, pics, pic_links, n_cols)
    return html

def _gen_image_grid( gallery, pics, pic_links, n_cols):
    """ Arrange image thumbs as a grid """
    
    s3_client = ''
    html = f'''<table class=gallery-table> ''' 
    colw = f'{100.0/n_cols}%'

    for left_idx in range( 0, len(pics), n_cols):
        html += f''' <tr> \n ''' 
        for col in range(n_cols):
            idx = left_idx + col
            if idx >= len(pics): break
            pic = pics[idx]
            img_link = pic_links.get( 'sm_' + helpers.basename( pic['filename']), 'static/images/img_not_found.jpg')
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

