import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    insert_count = 0
    reader = csv.reader(f)
    for isbn_text, title_text, author_name, published_year in reader:
      print("loop")
      if insert_count != 0: #skip the header
        db.execute("INSERT INTO books (isbn_text, title_text, author_name, published_year) VALUES (:isbn_text, :title_text, :author_name, :published_year)",
          {"isbn_text": isbn_text, "title_text": title_text, "author_name": author_name, "published_year": published_year})
        print(insert_count)
      insert_count += 1
    db.commit()

if __name__ == "__main__":
    main()

