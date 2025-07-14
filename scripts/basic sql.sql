select * from newsletter order by received_at desc;

truncate table newsletter restart identity;

UPDATE newsletter
SET chunked_text = NULL;

UPDATE newsletter
SET vectorized = false;

UPDATE newsletter
SET vectorized = false
where id = 155;