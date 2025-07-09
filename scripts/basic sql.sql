select * from newsletter;

truncate table newsletter restart identity;

UPDATE newsletter
SET chunked_text = NULL;
