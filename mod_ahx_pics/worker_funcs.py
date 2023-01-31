
from pdb import set_trace as BP
from mod_ahx_pics import log
from mod_ahx_pics.helpers import s3_get_keys, basename

def _get_missing_imgs(subfolder):
    """
    Find all fnames where 1009_176_1.jpg exists in orig folder,
    but sm_1009_176_1.jpg does not exist in small folder.
    """
    prefix = 'sm'
    if subfolder == 'medium': prefix = 'med'

    orig_files = s3_get_keys( 'pics/orig/')
    # pics/orig/bla.jpeg -> bla
    orig_basenames = [ basename(x) for x in orig_files ]

    # pics/small/bla.jpeg -> bla
    existing_target_files = s3_get_keys( f'pics/{subfolder}/')
    existing_target_basenames = [ basename(x) for x in existing_target_files ]

    missing_target_basenames = [ x for x in orig_basenames if not f'{prefix}_{x}' in set(existing_target_basenames) ]
    missing_orig_fnames = [ orig_files[i] for (i,x) in enumerate(orig_basenames) if x in set(missing_target_basenames) ]
    return missing_orig_fnames
    
def gen_thumbnails():
    log(f'>>>>>>> generating thumbnails')
    missing_small  = _get_missing_imgs('small')
    missing_medium  = _get_missing_imgs('medium')
    BP()
    log('Done.')


