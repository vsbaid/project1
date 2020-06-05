import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker
from appuser import AppUser

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

Session(app)
# session["userinfo"]=[]

################################################################################
#
# Functions here
#
# Create a table for user if not already exists
def createUserTable():
    db.execute("CREATE TABLE IF NOT EXISTS appuser (id SERIAL PRIMARY KEY,fname VARCHAR NOT NULL, lname VARCHAR NOT NULL, email VARCHAR, userID VARCHAR NOT NULL UNIQUE, password VARCHAR NOT NULL CHECK (char_length(password) >= 5 AND char_length(password) <=50)) ")
    db.commit()

# Create a new user in the appuser table once they sign up
def createUser(NewUser):
    db.execute("INSERT INTO appuser (fname, lname, email, userID, password) VALUES (:fname, :lname, :email, :userID, :password)", {"fname":NewUser.fname, "lname":NewUser.lname, "userID":NewUser.uid, "email":NewUser.email, "password":NewUser.password})
    db.commit()

# Check whether a user exists in the database
def isUserInDB(userID):
    if db.execute("SELECT * FROM appuser WHERE userid = :id",{"id":userID}).rowcount == 0:
        return False
    else:
        return True

# Check if a given username and password exists in the database
def pwdChk(userID,passW):
    if db.execute("SELECT * FROM appuser WHERE userid = :id AND password = :password", {"id":userID, "password":passW}).rowcount == 1:
        return True
    else:
        return False
#
# End of Functions
################################################################################
#
# Routes here
#

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        uid = request.form.get("uid")
        password = request.form.get("password")
        password_chk = request.form.get("password_chk")

        if password == password_chk:
            if isUserInDB(uid) == False:
                NewUser = AppUser(fname, lname, email, uid, password)
                print("Debug before createUser",NewUser)
                try:
                    createUser(NewUser)
                except:
                    return render_template("error.html",message="There was some error. Please check your enteries")
            else:
                return render_template("error.html",message="User already exists ! Pls go to Sign In Page")
        else:
            return render_template("error.html",message="Passwords Dont Match- Pls try again")

    return render_template("index.html")

@app.route("/login",methods=["POST"])
def login():
    uid = request.form.get('uid')
    password = request.form.get('password')
    if pwdChk(uid,password):
        return render_template("login.html")
    else:
        return render_template("error.html",message="Wrong Credentials. Pls Try Again")


@app.route("/signup",methods=["GET"])
def signup():
    fname_user = request.form.get("fname")
    print(fname_user)
    return render_template("signup.html")
#
# End of Routes
#
################################################################################

# Logical Block to Operate the code

createUserTable()
