import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine, inspect
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
def createUser(fname, lname, email, uid, password):
    db.execute("INSERT INTO appuser (fname, lname, email, userID, password) VALUES (:fname, :lname, :email, :userID, :password)", {"fname":fname, "lname":lname, "userID":uid, "email":email, "password":password})
    db.commit()

# Check whether a user exists in the database
def isUserInDB(userID):
    if db.execute("SELECT * FROM appuser WHERE userid = :id",{"id":userID}).rowcount == 0:
        return False
    else:
        return True

# Check a user session is authenticated
def isAuth():
    try:
        # print(session["auth"],"1")
        if session["auth"] == True:
            return True
        else:
            return False
    except:
        return False


# Check if a given username and password exists in the database
def pwdChk(userID,passW):
    if db.execute("SELECT * FROM appuser WHERE userid = :id AND password = :password", {"id":userID, "password":passW}).rowcount == 1:
        return True
    else:
        return False

def isBookInDB(searchStr):
    searchTitle = db.execute("SELECT * FROM books WHERE title ILIKE" + '\'%' + searchStr + '%\'').fetchall()
    searchAuthor = db.execute("SELECT * FROM books WHERE author ILIKE" + '\'%' + searchStr + '%\'').fetchall()
    searchISBN = db.execute("SELECT * FROM books WHERE isbn ILIKE" + '\'%' + searchStr + '%\'').fetchall()
    return searchTitle, searchAuthor, searchISBN

def createBookReviewTable():
    db.execute("CREATE TABLE IF NOT EXISTS bookreview (id SERIAL PRIMARY KEY, userID INTEGER REFERENCES appuser, bookID INTEGER REFERENCES books, review VARCHAR NOT NULL)")
    db.commit()

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
                try:
                    createUser(fname, lname, email, uid, password)
                except:
                    return render_template("error.html",message="There was some error. Please check your enteries")
            else:
                return render_template("error.html",message="User already exists ! Pls go to Sign In Page")
        else:
            return render_template("error.html",message="Passwords Dont Match- Pls try again")

    return render_template("index.html")

@app.route("/login",methods=["POST"])
def login():
    session["auth"]=False
    uid = request.form.get('uid')
    password = request.form.get('password')
    if session.get("user") is None:
        session["user"]=uid
    if session.get("pwd") is None:
        session["pwd"]=password
    print(session["user"],session["pwd"])
    if pwdChk(uid,password):
        session["auth"]=True;
        print(session["auth"],"1")
        return render_template("login.html")
    else:
        return render_template("error.html",message="Wrong Credentials. Pls Try Again")


@app.route("/signup",methods=["GET"])
def signup():
    return render_template("signup.html")

@app.route("/logoff",methods=["GET"])
def logoff():
    # print(session["user"],session["pwd"])
    # session[""]
    session.clear()
    return render_template("index.html")

@app.route("/search",methods=["GET"])
def search():
    try:
        if isAuth():
            return render_template("search.html")
        else:
            return render_template("error.html",message="Wrong Credentials. Pls Try Again")
    except:
        return render_template("error.html",message="Exception in Application Caught 1")


@app.route("/results",methods=["POST"])
def results():
    try:
        if isAuth():
            # return render_template("login.html")
            bookStr = request.form.get('searchStr')
            print(bookStr)
            findTitle, findAuthor, findISBN = isBookInDB(bookStr)
            if not findTitle and not findAuthor and not findISBN:
                return render_template("error.html",message="No Match Found, Change the search Query.")
            else:
                print("reached here ---- > 1")
                print(findTitle,findAuthor,findISBN)
                return render_template("results.html",titles=findTitle,authors=findAuthor,isbn=findISBN)
        else:
            return render_template("error.html",message="Session Ended. Pls Try Again")
    except:
        return render_template("error.html",message="Exception in Application Caught Error Code 2")

@app.route("/book/<int:book_id>",methods=["GET","POST"])
def book(book_id):
    try:
        if isAuth():
            book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
            if book is None:
                return render_template("error.html", message="No such book.")
            else:
                return render_template("book.html", book=book)
        else:
            return render_template("error.html",message="Session Ended. Pls Try Again")
    except:
        return render_template("error.html",message="Exception in Application Caught Error Code 3")
#
# End of Routes
#
################################################################################

# Logical Block to Operate the code

createUserTable()
createBookReviewTable()
