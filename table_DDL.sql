CREATE TABLE users (
  id SERIAL PRIMARY KEY
  ,user_name VARCHAR NOT NULL
  ,password_hash BYTEA NOT NULL
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


CREATE TABLE reviews (
  id SERIAL PRIMARY KEY
  ,book_id INTEGER NOT NULL
  ,user_id INTEGER NOT NULL
  ,score_value SMALLINT NOT NULL
  ,review_text VARCHAR NULL
  ,create_timestamp TIMESTAMP DEFAULT NOW()
);

