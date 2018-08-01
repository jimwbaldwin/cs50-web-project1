CREATE TABLE users (
  id SERIAL PRIMARY KEY
  ,password_hash VARCHAR NOT NULL
  ,given_name VARCHAR NULL
  ,email_addr_text VARCHAR NULL
  ,create_timestamp TIMESTAMP DEFAULT NOW()
);


CREATE TABLE books (
  id SERIAL PRIMARY KEY
  ,isbn_text VARCHAR NOT NULL
  ,title_text VARCHAR NOT NULL
  ,author_name VARCHAR NOT NULL
  ,published_year SMALLINT NOT NULL
);
