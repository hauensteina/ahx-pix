"""
gui.py
Andreas Hauenstein
Created: Jan 2023

Functions to generate html for the GUI
"""

from pdb import set_trace as BP
import os
from flask import url_for, session
from mod_ahx_pix import IMG_EXTENSIONS, VIDEO_EXTENSIONS
import mod_ahx_pix.helpers as helpers
from  mod_ahx_pix.helpers import html_tag as H
from  mod_ahx_pix.helpers import html_img as I
import mod_ahx_pix.persistence as pe

def gen_carousel_images( gallery, active_pic_id):
    """ Generate the page showing one full screen pic at a time. """

    def gen_images( pics):
        #pics = [ x for x in pics if not x['title_flag'] ]
        # The images/videos
        images = []
        pic_links = pe.get_gallery_links( gallery['id']) # image files in S3
        capclass = 'ahx-caption'
        if session.get('is_mobile',''): capclass = 'ahx-caption-mobile' 
        found_active = False
        for i,pic in enumerate(pics):
            ext = os.path.splitext(pic['filename'])[1].lower()
            furl = pic_links.get( 'med_' + helpers.basename( pic['filename']), 'static/images/img_not_found.png')
            if ext in VIDEO_EXTENSIONS:
                furl = pic_links.get(
                  'lg_' + helpers.basename(pic['filename']), 'static/images/img_not_found.png')
                #log( f'gen_carousel_images: furl:{furl} pic:{pic}')

            caption = f''' <div id='cap_{i}' class={capclass}>{pic['blurb']}</div> '''
            
            if ext in VIDEO_EXTENSIONS + IMG_EXTENSIONS:
                if _bad_caption( pic['blurb']): caption = ''
 
            if 'NEW PICTURE' in pic['blurb']: caption = ''

            classes = " class='ahx-slide' "
            if pic['id'] == active_pic_id: 
                found_active = True
                classes = " class='ahx-slide ahx-active' "
            if ext in VIDEO_EXTENSIONS:
                link = f'''
                <li> 
                <video id='img_{i}' preload='none' controls  data-pic-id='{pic["id"]}' {classes}>  
                  <source id=vsrc_{i} data-src='{furl}#t=0.5'>
                </video> 
                {caption}
                </li> 
                '''
                images.append(link)
            elif ext in IMG_EXTENSIONS:
                link = f'''
                <li>
                  <img id='img_{i}' loading='lazy' data-src='{furl}'  data-pic-id='{pic["id"]}' {classes}> 
                  {caption}
                </li>
                '''
                images.append(link)
            else: # Not image or video
                fname = f'''pics_complete/{helpers.basename( pic['filename'])}{ext}'''
                link = f'''
                <li>
                  <img id='img_{i}' loading='lazy' data-fname="{fname}" 
                    data-src='static/images/img_not_found.png'  data-pic-id='{pic["id"]}' {classes}> 
                  {caption}
                </li>
                '''
                images.append(link)
        if not found_active:
            images[0] = images[0].replace('ahx-slide', 'ahx-slide ahx-active')
        html = '\n'.join(images)
        return html
        
    s3_client = ''
    found_active = False
    pics = pe.get_gallery_pics( gallery['id']) # pic filenames in DB
    pics = [ x for x in pics if not x['title_flag'] or gallery.get('show_title_pic_flag', '') ] 
    html = gen_images( pics)
    return html

def gen_edit_pics( gallery):
    """ Generate the page to drag and drop pic order. """
    gallery_id = gallery['id']
    pic_links = pe.get_gallery_links( gallery_id)
    pics = pe.get_gallery_pics( gallery_id)
    pics = [ x for x in pics if not x['title_flag'] or gallery.get('show_title_pic_flag', '') ] 
    picdivs = ''
    for pic in pics:
        #if pic['title_flag']: continue
        blurb = pic['blurb']
        blurb = helpers.desanitize_caption( blurb)
        ext = os.path.splitext(pic['filename'])[1].lower()
        style='width:100%;object-fit:contain;'
        if ext in VIDEO_EXTENSIONS + IMG_EXTENSIONS:
            if _bad_caption(blurb): blurb = '' 
        if ext in VIDEO_EXTENSIONS:    
            img_link = pic_links.get( 'sm_' + helpers.basename( pic['filename']), 'static/images/img_not_found.jpg')
            style += f'border-style:solid; border-color:green; border-width:4px; padding:1px;'  
        else:
            img_link = pic_links.get( 'med_' + helpers.basename( pic['filename']), 'static/images/img_not_found.jpg')

        picdiv = f'''
          <div class='ahx-draggable' draggable=true>
            <div class=ahx-pic id='pic_{pic["id"]}'>
              <img id='{pic["id"]}' src='{img_link}' style='{style}' draggable=false>
            </div> 
          </div>
        '''
        picdivs += picdiv
    return picdivs

def gen_gallery( gallery, pics, n_cols=5):
    """
    Generate html to display all pics in a gallery at once.
    Gallery title and blurb at the top.
    """
    pic_links = pe.get_gallery_links( gallery['id'])

    # Heading
    heading_h = H( 'div', gallery['title'], 'margin:0 auto; font-size:2.0em;')

    # Title pic
    title_pic = [x for x in pics if x['title_flag']]
    if title_pic:
        title_pic = title_pic[0]
        img_link = pic_links.get( 'med_' + helpers.basename( title_pic['filename']), '')
        visit_url = f''' '{url_for( "carousel", gallery_id=gallery["id"], picture_id=title_pic["id"])}' '''
        onclick = f''' onclick="window.location.href={visit_url}" '''
        title_pic_h = ''
        if img_link:
            title_pic_h = I( img_link, 'object-fit:contain;margin:0 auto; height:30vh;', f' {onclick} ')
            title_pic_h +=  H( 'span', gallery['title_pic_caption'] or '&nbsp;', 'margin:0 auto; font-size:1.2em')
    else:
        title_pic_h = ''

    # Blurb
    gallery_blurb_h = H( 'div', gallery['blurb'] or '', 
                         'font-size: 1.2em; padding-left:10px; padding-top:20px; padding-bottom:30px;')

    # Images
    n_cols = 5
    if gallery['layout'] == 'single_column': n_cols = 1
    elif gallery['layout'] == 'double_column': n_cols = 2
    n_cols = min( n_cols, max(1,len( pics)))
    images_h = _gen_image_grid( gallery, pics, pic_links, n_cols=n_cols)

    html = H('div', heading_h + title_pic_h + gallery_blurb_h + images_h,
             'display:grid; grid-template-columns:fit-content(1200px); margin-left:50px; margin-right:50px; width:50em;')
    return html

def gen_gallery_mobile( gallery, pics, n_cols=5):
    """
    Generate html to display all pics in a gallery at once.
    Gallery title and blurb at the top.
    """
    pic_links = pe.get_gallery_links( gallery['id'])

    # Heading
    heading_h = H( 'div', gallery['title'], 'margin:0 auto; font-size:2.0em;')

    # Title pic
    title_pic = [x for x in pics if x['title_flag']]
    if title_pic:
        title_pic = title_pic[0]
        img_link = pic_links.get( 'med_' + helpers.basename( title_pic['filename']), '')
        visit_url = f''' '{url_for( "carousel", gallery_id=gallery["id"], picture_id=title_pic["id"])}' '''
        onclick = f''' onclick="window.location.href={visit_url}" '''
        title_pic_h = ''
        if img_link:        
            title_pic_h = I( img_link, 'object-fit:contain;margin:0 auto; height:30vh; max-height:30vh; max-width:90vw;', f' {onclick} ')
            title_pic_h +=  H( 'span', gallery['title_pic_caption'] or '&nbsp;', 'margin:0 auto; font-size:1.2em')
    else:
        title_pic_h = ''

    # Blurb
    gallery_blurb_h = H( 'div', gallery['blurb'] or '', 
                         'font-size: 1.2em; padding-left:10px; padding-top:20px; padding-bottom:30px;')

    # Images
    n_cols = 3
    if gallery['layout'] == 'single_column': n_cols = 1
    elif gallery['layout'] == 'double_column': n_cols = 2
    n_cols = min( n_cols, max(1,len( pics)))
    images_h = _gen_image_grid( gallery, pics, pic_links, n_cols=n_cols)

    html = H('div', heading_h + title_pic_h + gallery_blurb_h + images_h,
             'display:grid; grid-template-columns:fit-content(1200px); margin-left:5vw; margin-right:5vw;')
    return html

def gen_gallery_list( galleries, sort_col, next_order):
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
        sort = ''
        if col == sort_col:
            sort = f''' <input type=hidden name=sort_order value={next_order} form=gallery_search> '''
        link = f''' <input type=submit name=btn_sort value='{col}' class=linkbtn form=gallery_search > '''
        theader += H(f'''div class="gallery-list-cell" ''', 
                     sort + link, f'{pos};{style}')
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
            if col == 'Title': style += 'width:400px;'
            col_html = H( f'div class="gallery-list-cell"', 
                          H('span', val, style), 
                          f'{pos}')
            row_html += col_html
        row_html = H( f'div {onclick} class="gallery-list-row"', row_html )
        html += row_html

    html = H('div', html, layout)
    return html

def gen_gallery_list_mobile( galleries, sort_col, next_order):
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
        sort = ''
        if col == sort_col:
            sort = f''' <input type=hidden name=sort_order value={next_order} form=gallery_search> '''
        link = f''' <input type=submit name=btn_sort value='{col}' class=linkbtn form=gallery_search > '''
        theader += H(f'''div class="gallery-list-cell" ''', 
                     sort + link, f'{pos};{style}')
    html += theader

    # One row per gallery
    for ridx,gal in enumerate(galleries):
        visit_url = f"'{url_for( 'gallery_mobile', gallery_id=gal['id'])}'"
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

    if session.get('all_pics_flag',''):
        html = f'''
        <form id='gallery_search' method=post class=search-form>
          <input type=hidden name=_action value="search_gallery">
          <div style='display:grid; grid-template-columns: fit-content(0) fit-content(0) fit-content(0);'>
            <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
              Title:
            </div>
            <div style='display:grid;grid-column-start:2; grid-column-end:3;'>
              Owner:
            </div>

            <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
              <input type=text name=title size=20 value='{title}' style='margin-top:auto;margin-bottom:auto;'>
            </div>
            <div style='display:grid;grid-column-start:2; grid-column-end:3;'>
              <input type=text name=owner size=20 value='{owner}' style='margin-top:auto;margin-bottom:auto;'>
            </div>

            <div style='display:grid;grid-column-start:3; grid-column-end:4;'>
              <input type=submit name=btn_search value=Search class='ahx-small-submit-button'>
            </div>
          </div>
        </form>
        '''
    else:
        html = f'''
        <form id='gallery_search' method=post class=search-form>
          <input type=hidden name=_action value="search_gallery">
          <div style='display:grid; grid-template-columns: fit-content(0) fit-content(0);'>
            <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
              Title:
            </div>
            <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
              <input type=text name=title size=20 value='{title}' style='margin-top:auto;margin-bottom:auto;'>
            </div>
            <div style='display:grid;grid-column-start:2; grid-column-end:3;'>
              <input type=submit name=btn_search value=Search class='ahx-small-submit-button' >
            </div>
          </div>
        </form>
        '''
    return html

def gen_gallery_search_mobile( title='', owner=''):
    """ Generate a form to search galleries by title and owner """
    if session.get('all_pics_flag',''):
        html = f'''
        <form id='gallery_search' method=post class=search-form-mobile>
          <input type=hidden name=_action value="search_gallery">
          <div style='display:grid; grid-template-columns: fit-content(0) fit-content(0) fit-content(0);'>
            <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
              Title:
            </div>
            <div style='display:grid;grid-column-start:2; grid-column-end:3;'>
              Owner:
            </div>

            <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
              <input type=text name=title size=15 value='{title}' style='margin-top:auto;margin-bottom:auto;'>
            </div>
            <div style='display:grid;grid-column-start:2; grid-column-end:3;'>
              <input type=text name=owner size=15 value='{owner}' style='margin-top:auto;margin-bottom:auto;'>
            </div>

            <div style='display:grid;grid-column-start:3; grid-column-end:4;'>
              <input type=submit name=btn_search value=Search class='ahx-small-submit-button' >
            </div>
          </div>
        </form>
        '''
    else: 
        html = f'''
        <form id='gallery_search' method=post class=search-form-mobile>
          <input type=hidden name=_action value="search_gallery">
          <div style='display:grid; grid-template-columns: fit-content(0) fit-content(0) fit-content(0);' >
            <div style='display:grid;grid-column-start:1; grid-column-end:4;'>
              Title:
            </div>

            <div style='display:grid;grid-column-start:1; grid-column-end:2;'>
              <input type=text name=title size=15 value='{title}' style='margin-top:auto;margin-bottom:auto;'>
            </div>
            <div style='display:grid;grid-column-start:2; grid-column-end:4;' >
              <input type=submit name=btn_search value=Search class='ahx-small-submit-button'>
            </div>

          </div>
        </form>
        '''
    return html

def _gen_image_grid( gallery, pics, pic_links, n_cols=5):
    """ Arrange image thumbs as a grid """
    
    MAX_CAP_LEN = 100
    colw = f'{100.0/n_cols}% '
    html = []
    for pic in pics:
        if pic.get('title_flag','') and not gallery.get('show_title_pic_flag',''): continue
        ext = os.path.splitext( pic['filename'])[1].lower()
        img_link = pic_links.get( 'sm_' + helpers.basename( pic['filename']), 'static/images/img_not_found.jpg')
        if n_cols <= 2 and ext not in VIDEO_EXTENSIONS:
          img_link = pic_links.get( 'med_' + helpers.basename( pic['filename']), 'static/images/img_not_found.jpg')
            
        visit_url = f''' '{url_for( "carousel", gallery_id=gallery["id"], picture_id=pic["id"])}' '''
        if ext not in IMG_EXTENSIONS and ext not in VIDEO_EXTENSIONS:
            fname = f'''pics_complete/{os.path.split(pic['filename'])[1]}'''
            visit_url = f''' '{url_for( "download_file", fname=fname)}' '''

        onclick = f''' onclick="window.location.href={visit_url}" '''
        style = f'width:100%;object-fit:contain;'
        if ext in VIDEO_EXTENSIONS: style += f'border-style:solid; border-color:green; border-width:4px; padding:1px;'
        pic_h = I( img_link, style, f' {onclick} ')
        caption_h = pic['blurb']
        if len(caption_h) > MAX_CAP_LEN and not '<a' in caption_h and n_cols > 2:
            caption_h = caption_h[:MAX_CAP_LEN] + '...'
        # Some captions are just filenames. Hide them. 
        if ext in VIDEO_EXTENSIONS + IMG_EXTENSIONS:
            if _bad_caption( caption_h): caption_h = ''
        if 'NEW PICTURE' in caption_h: caption_h = ''
            
        #style = f'padding:10px 0; margin:auto 10px auto 10px;text-overflow:ellipsis;overflow:hidden;'
        style = f'padding:10px 0; margin:0 10px auto 10px;text-overflow:ellipsis;overflow:hidden;'
        if n_cols == 1:
          #style = f'padding:10px 0; margin:10px 10px auto 10px;text-overflow:ellipsis;overflow:hidden;'
          style = f'padding:10px 0; margin:10px 10px auto 10px;text-overflow:ellipsis;overflow:hidden;'
            
        #if ext in VIDEO_EXTENSIONS: style += f'border-style:solid; border-color:green; border-width:4px;padding:2px;'
        pic_h = H( 'div', pic_h + caption_h, style)
        html.append(pic_h)
    
    html = '\n'.join(html)    
    if session.get('is_mobile',''):
        html = H('div', html,
                 f''' display:grid; grid-template-columns:{colw * n_cols}; max-width:1000px; min-width:90vw; ''')
    else:
        html = H('div', html,
                 f''' display:grid; grid-template-columns:{colw * n_cols};''')        
    return html

### Helpers ###
###############

def _bad_caption( blurb):
    """ Return True if empty caption or the caption looks like just a filename """
    if not blurb: return True
    if not blurb.strip(): return True
    return ( len(blurb.split()) == 1 and len(os.path.splitext(blurb)[1]) > 1 )

