

-- All topics where the owner is Andreas (19) or JC(31) or any picture 
-- is owned by Andreas or JC

drop table rescue_topics;
create table rescue_topics as 

select
  topic_id
  ,topic_name
  ,text
  ,visibility
  ,date_changed
  ,date_started
  ,case when user_id in (19,31) 
        then user_id
        else puser_id 
   end as user_id
from (
    select
      t.topic_id, t.topic_name, t.user_id, t.text, t.visibility, t.date_changed, t.date_started
      ,min(p.user_id) as puser_id
    from
      topic t
    left outer join
      picture p
    on
      t.topic_id = p.topic_id
    group by 
      t.topic_id, t.topic_name, t.user_id, t.text, t.visibility, t.date_changed, t.date_started
    ) as t0
where
  t0.user_id in (19,31) or t0.puser_id in (19,31)
;
 
