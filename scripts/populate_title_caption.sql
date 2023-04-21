update
    gallery
set
    title_pic_caption = tt.blurb
from
    (
        select
            g.id as gallery_id,
            p.blurb
        from
            gallery as g
            join picture as p on p.gallery_id = g.id
            and p.title_flag = true
    ) as tt
where
    gallery.id = tt.gallery_id;


