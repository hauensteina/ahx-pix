"""
gui.py
Andreas Hauenstein
Created: Jan 2023

Functions to generate html for the GUI
"""

from pdb import set_trace as BP
import os
from flask import url_for
from mod_ahx_pics import AppError, log, SMALL_FOLDER
from mod_ahx_pics import IMG_EXTENSIONS, VIDEO_EXTENSIONS
from mod_ahx_pics.helpers import pexc
import mod_ahx_pics.helpers as helpers
from  mod_ahx_pics.helpers import html_tag as H
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
            link = f'''<li> <video preload='none' controls {classes}>  
                       <source id=vsrc_{i} data-src='{furl}#t=0.5'></video> </li> '''
            images.append(link)
        elif ext in IMG_EXTENSIONS:
            link = f"<li> <img loading='lazy' data-src='{furl}' {classes}> </li>"
            images.append(link)
        else:
            #log(f'ERROR: unknown media extension {ext}. Ignoring {pic}')
            continue
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

def gen_gallery_list( galleries):
    """
    Generate html to display a list of galleries
    """
    columns = { 'Title':'title', 'Date':'create_date', 'Owner':'username'} 

    layout =  f'''
             display:grid; 
             grid-template-columns: fit-content(50%) fit-content(50%) fit-content(50%);
             margin-left:50px
             '''

    html = ''

    # Table header
    theader = ''
    style = f'background-color: #8fc3f5; border: 1px solid #bbb;'
    for idx,col in enumerate(columns):
        pos = f'grid-column-start:{idx+1}; grid-column-end:{idx+2}'
        theader += H('div class="gallery-list-cell"',col,f'{pos};{style}')
    html += theader

    # One row per gallery
    for ridx,gal in enumerate(galleries):
        visit_url = f"'{url_for( 'gallery', gallery_id=gal['id'])}'"
        onclick = f''' onclick="window.location.href={visit_url}" '''
        row_html = ''
        for cidx,col in enumerate(columns):
            pos = f'grid-column-start:{cidx+1}; grid-column-end:{cidx+2}'
            val = gal[columns[col]]
            style = 'margin-top:auto;margin-bottom:auto;'
            if col != 'Title': style += 'white-space:nowrap;'
            col_html = H( f'div class="gallery-list-cell"', 
                          H('span', val, style), 
                          f'{pos}')
            row_html += col_html
        row_html = H( f'div {onclick} class="gallery-list-row"', row_html )
        html += row_html

    html = H('div', html, layout)

    return html

def gen_gallery_list_mobile( galleries):
    """
    Generate html to display a list of galleries
    """
    columns = { 'Title':'title', 'Date':'create_date', 'Owner':'username'} 

    layout =  f'''
             display:grid; 
             grid-template-columns: 1fr fit-content(50%) fit-content(8ch);
             margin-left:5vw;margin-right:5vw;
             '''

    html = ''

    # Table header
    theader = ''
    style = f'background-color: #8fc3f5; border: 1px solid #bbb;'
    for idx,col in enumerate(columns):
        pos = f'grid-column-start:{idx+1}; grid-column-end:{idx+2}'
        theader += H('div class="gallery-list-cell"', 
                     H('span', col, 'margin-top:auto;margin-bottom:auto;'), 
                     f'{pos};{style}')
    html += theader

    # One row per gallery
    for ridx,gal in enumerate(galleries):
        visit_url = f"'{url_for( 'gallery', gallery_id=gal['id'])}'"
        onclick = f''' onclick="window.location.href={visit_url}" '''
        row_html = ''
        for cidx,col in enumerate(columns):
            pos = f'grid-column-start:{cidx+1}; grid-column-end:{cidx+2}'
            val = gal[columns[col]]
            style = 'margin-top:auto;margin-bottom:auto;'
            if col != 'Title': style += 'white-space:nowrap;'
            col_html = H( f'div class="gallery-list-cell"', 
                          H('span', val, style), 
                          f'{pos}')
            row_html += col_html
        row_html = H( f'div {onclick} class="gallery-list-row"', row_html )
        html += row_html

    html = H('div', html, layout)

    return html


def gen_gallery_search( title='', owner=''):
    """ Generate a form to search galleries by title and owner """

    html = f'''
    <form method=post class=search-form>
      <input type=hidden name=_action value="search_gallery">
      <div style='display:grid; grid-template-columns: fit-content(0) fit-content(0) fit-content(0);'>
        <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
          Title:
        </div>
        <div style='display:grid;grid-column-start:2; grid-column-end:3;'>
          Owner:
        </div>

        <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
          <input type=text name=title size=20 value='{title}'>
        </div>
        <div style='display:grid;grid-column-start:2; grid-column-end:3;'>
          <input type=text name=owner size=20 value='{owner}'>
        </div>

        <div style='display:grid;grid-column-start:3; grid-column-end:4;'>
          <input type=submit name=btn_search value=Search >
        </div>
      </div>
    </form>
    '''
    return html

def gen_gallery_search_mobile( title='', owner=''):
    """ Generate a form to search galleries by title and owner """

    html = f'''
    <form method=post class=search-form-mobile>
      <input type=hidden name=_action value="search_gallery">
      <div style='display:grid; grid-template-columns: fit-content(0) fit-content(0) fit-content(0);'>
        <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
          Title:
        </div>
        <div style='display:grid;grid-column-start:2; grid-column-end:3;'>
          Owner:
        </div>

        <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
          <input type=text name=title size=15 value='{title}'>
        </div>
        <div style='display:grid;grid-column-start:2; grid-column-end:3;'>
          <input type=text name=owner size=15 value='{owner}'>
        </div>

        <div style='display:grid;grid-column-start:3; grid-column-end:4;'>
          <input type=submit name=btn_search value=Search >
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

