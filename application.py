import os
import bcrypt
import requests

from flask import Flask, session, render_template, redirect, url_for, request
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
    #The register user process.
    if request.method == "POST" and request.form['btn'] == 'Register':
        #Check if the user exists.
        if db.execute("SELECT 1 FROM users WHERE user_name = :user_name;",{"user_name": request.form['register_username']}).fetchone() is not None:
            #Return error message.
            return render_template("index.html", message="user_exists", user_id=session.get("user_id"))
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
            return render_template("index.html", message="user_created", user_id=session.get("user_id"))
    elif request.method == "POST" and request.form['btn'] == 'Login':
        session.login_result = db.execute("SELECT id, password_hash FROM users WHERE user_name = :user_name;"
             ,{"user_name": request.form['login_username']}).fetchone()
        db.commit()
        if session.login_result is not None and bcrypt.checkpw(request.form['login_password'].encode("utf8"), bytes(session.login_result[1])):
            session["user_id"] = session.login_result[0]
            #Clear the variables that had the password hash.
            session.login_result = None
            return redirect(url_for('search'))
        else:
            return render_template("index.html", message="invalid_login", user_id=session.get("user_id"))
        #return render_template("search.html", message="", user_id=session.get("user_id"))
    elif session.get("message") == "user_logout":
        session.pop("message")
        return render_template("index.html", message="user_logout", user_id=session.get("user_id"))
    if session.get("user_id") is None:
        return render_template("index.html", message="", user_id=session.get("user_id"))
    else:
        return redirect(url_for('search'))


@app.route("/search",methods=["GET", "POST"])
def search():
    if session.get("user_id") is None:
        return redirect(url_for('index'))
    else:
        if request.form.get('search_term') is not None:
            #session.get("search_result") = "'%" + "%','%".join(request.form["search_term"].lower().split(' ')) + "%'"
            session["search_terms"] = "%" + request.form["search_term"].lower() + "%"
            session["search_result"] = db.execute("""
                select *
                from books
                WHERE lower(isbn_text) like (:search_terms)
                OR lower(title_text)   like (:search_terms)
                OR lower(author_name)  like (:search_terms)
                ;
                """,{"search_terms": session.get("search_terms")}
                ).fetchall()
            db.commit()
        else:
            session["search_result"] = None
        return render_template("search.html", message="", user_id=session.get("user_id"), search_result=session.get("search_result"))

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
        session["book_row"] = db.execute("""
            select *
            from books
            WHERE id = :book_id
            ;
            """,{"book_id": book_id}
            ).fetchone()
        db.commit()

        session["rs_user_review"] = db.execute("""
            select 1
            from reviews
            WHERE book_id = :book_id
            and user_id = :user_id
            ;
            """,{"book_id": book_id, "user_id": session.get("user_id")}
            ).fetchone()
        db.commit()

        if session.get("rs_user_review") is None and request.form.get("review_score") is not None:
            db.execute("""
                INSERT INTO  reviews
                (book_id, user_id, score_value, review_text)
                VALUES
                (:book_id, :user_id, :score_value, :review_text)
                ;
                """,{"book_id": book_id, "user_id": session.get("user_id")
                    , "score_value": request.form.get("review_score"), "review_text": request.form.get("review_text")}
                )
            session["rs_user_review"] = 1
            db.commit()

        session["rs_reviews"] = db.execute("""
        select *
        from reviews
        WHERE book_id = :book_id
        ;
        """,{"book_id": book_id}
        ).fetchall()
        db.commit()

        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": session["book_row"]["isbn_text"]})
        ratings = res.json().get("books")[0]
        return render_template("book.html", message="", user_id=session.get("user_id"), book_row=session.get("book_row")
            , ratings=ratings, user_review=session.get("rs_user_review"))
    