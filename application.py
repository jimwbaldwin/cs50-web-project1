import os
import bcrypt
import requests

from flask import Flask, session, render_template, redirect, url_for, request, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Get the goodreads API key.
key = os.getenv("GOODREADS_KEY")

@app.route("/",methods=["GET","POST"])
def index():
    if session.get("user_id") is not None:
        return redirect(url_for('search'))
    else:
        #pop the message so it only displays once
        message = session.pop("message", None)
        return render_template("index.html", message=message, user_id=session.get("user_id"))


@app.route("/register",methods=["POST"])
def register():
    if db.execute("SELECT 1 FROM users WHERE user_name = :user_name;",{"user_name": request.form['register_username']}).fetchone() is not None:
        db.commit()
        #Return error message.
        session["message"] = "user_exists"
        return redirect(url_for('index'))
    #Else user must not exist.
    else:
        #Create the user.
        db.execute("INSERT INTO users (user_name, password_hash, given_name, email_addr_text) VALUES (:user_name, :password_hash, :given_name, :email_addr_text)",
                   {"user_name": request.form['register_username']
                   #Use bcrypt to hash the password. I'm trying not to store it in a variable at all.
                   , "password_hash": bcrypt.hashpw(request.form['register_password'].encode("utf8"), bcrypt.gensalt())
                   , "given_name": request.form['register_email']
                   , "email_addr_text": request.form['register_given_name']
                   })
        #Commit so we don't lock the database.
        db.commit()
        session["message"] = "user_created"
        return redirect(url_for('index'))


@app.route("/login",methods=["POST"])
def login():
    rs_login_result = db.execute("SELECT id, password_hash FROM users WHERE user_name = :user_name;"
            ,{"user_name": request.form['login_username']}).fetchone()
    db.commit()
    if rs_login_result is not None and bcrypt.checkpw(request.form['login_password'].encode("utf8"), bytes(rs_login_result[1])):
        session["user_id"] = rs_login_result[0]
        return redirect(url_for('search'))
    else:
        session["message"] = "invalid_login"
        return redirect(url_for('index'))


@app.route("/search",methods=["GET", "POST"])
def search():
    if session.get("user_id") is None:
        return redirect(url_for('index'))
    else:
        if request.form.get('search_term') is not None:
            #session.get("search_result") = "'%" + "%','%".join(request.form["search_term"].lower().split(' ')) + "%'"
            search_terms = "%" + request.form["search_term"].lower() + "%"
            search_result = db.execute("""
                select *
                from books
                WHERE lower(isbn_text) like (:search_terms)
                OR lower(title_text)   like (:search_terms)
                OR lower(author_name)  like (:search_terms)
                ;
                """,{"search_terms": search_terms}
                ).fetchall()
            db.commit()
        else:
            search_result = None
        return render_template("search.html", message="", user_id=session.get("user_id"), search_result=search_result)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    session["message"]="user_logout"
    return redirect(url_for('index'))
    #return render_template("index.html", message="user_logout", user_id=session.get("user_id"))


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book(book_id):
    if session.get("user_id") is None:
        return redirect(url_for('index'))
    else:
        rs_book = db.execute("""
            select *
            from books
            WHERE id = :book_id
            ;
            """,{"book_id": book_id}
            ).fetchone()
        db.commit()

        rs_user_review = db.execute("""
            select 1
            from reviews
            WHERE book_id = :book_id
            and user_id = :user_id
            ;
            """,{"book_id": book_id, "user_id": session.get("user_id")}
            ).fetchone()
        db.commit()

        if rs_user_review is None and request.form.get("review_score") is not None:
            db.execute("""
                INSERT INTO  reviews
                (book_id, user_id, score_value, review_text)
                VALUES
                (:book_id, :user_id, :score_value, :review_text)
                ;
                """,{"book_id": book_id, "user_id": session.get("user_id")
                    , "score_value": request.form.get("review_score"), "review_text": request.form.get("review_text")}
                )
            rs_user_review = 1
            db.commit()

        rs_reviews = db.execute("""
        select 
             u.user_name
            ,r.score_value
            ,r.review_text
            ,r.create_timestamp
        from reviews       as r
        INNER JOIN users   as u
        ON r.user_id = u.id
        WHERE r.book_id = :book_id
        ORDER BY r.create_timestamp DESC
        ;
        """,{"book_id": book_id}
        ).fetchall()
        db.commit()

        gr_reviews_request = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": rs_book["isbn_text"]})
        gr_reviews_json = gr_reviews_request.json().get("books")[0]
        return render_template("book.html", message="", user_id=session.get("user_id"), 
                               book_row=rs_book, ratings=gr_reviews_json, 
                               user_review=rs_user_review, reviews=rs_reviews
                               )


@app.route("/api/<isbn_text>", methods=["GET", "POST"])
def api(isbn_text):
    book_details = db.execute("""
        SELECT   b.title_text as title
                ,b.author_name as author
                ,b.published_year as year
                ,b.isbn_text as isbn
                ,COUNT(distinct r.id) as review_count
                ,CAST(AVG(r.score_value) AS DECIMAL(2,1)) as average_score
        FROM books as b 
        INNER JOIN reviews as r
        on b.id = r.book_id
        WHERE isbn_text = :isbn_text
        GROUP BY
                b.title_text
                ,b.author_name
                ,b.published_year
                ,b.isbn_text
        ;
        """,{"isbn_text": isbn_text}).fetchone()
    db.commit()
    if book_details is None:
        abort(404)
    else:
        output_dict = {}
        output_dict["title"] = book_details["title"]
        output_dict["author"] = book_details["author"]
        output_dict["year"] = book_details["year"]
        output_dict["isbn"] = book_details["isbn"]
        output_dict["review_count"] = book_details["review_count"]
        output_dict["average_score"] = book_details["average_score"]
    return jsonify(output_dict)
