import os

from flask import Flask, session, render_template, redirect, url_for
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
    return render_template("index.html", headline="You are logged in", user_id=session.get("user_id"))
    #return render_template("index.html", headline="You are logged in", user_id="1")


@app.route("/search",methods=["GET","POST"])
def register():
    if session.get("user_id") is None:
        return redirect(url_for('index'))
    if request.method == "POST":
        pass