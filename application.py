import os
import bcrypt

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


@app.route("/",methods=["GET","POST"])
def index():
    if request.method == "POST" and request.form['btn'] == 'Register':
        if db.execute("SELECT 1 FROM users WHERE user_name = :user_name;",{"user_name": request.form['register_username']}).fetchone() is None:
            db.execute("INSERT INTO users (user_name, password_hash, given_name, email_addr_text) VALUES (:user_name, :password_hash, :given_name, :email_addr_text)",
            {"user_name": request.form['register_username']
            #Use bcrypt to hash the password. I'm trying not to store it in a variable at all.
            , "password_hash": bcrypt.hashpw(request.form['register_password'].encode("utf8"), bcrypt.gensalt())
            , "given_name": request.form['register_email']
            , "email_addr_text": request.form['register_given_name']
            })
            db.commit()
            return render_template("index.html", message="user_created", user_id=session.get("user_id"))
        else:
            return render_template("index.html", message="user_exists", user_id=session.get("user_id"))
    elif request.method == "POST" and request.form['btn'] == 'Login':
        pass
        #bcrypt.hashpw(request.form['register_password'].encode("utf8"), hashed)
        #return render_template("index.html", headline="You are logged in", user_id="1")
    
    return render_template("index.html", message="", user_id=session.get("user_id"))

@app.route("/search",methods=["GET","POST"])
def register():
    if session.get("user_id") is None:
        return redirect(url_for('index'))
    if request.method == "POST":
        pass
