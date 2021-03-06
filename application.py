import os

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

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
grKEY = "kBqu25B5BBam4sUalojslg"

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

# Check if the string user has searched for exists in the books database. Check on title author and isbn.
def isBookInDB(searchStr):
    searchTitle = db.execute("SELECT * FROM books WHERE title ILIKE" + '\'%' + searchStr + '%\'').fetchall()
    searchAuthor = db.execute("SELECT * FROM books WHERE author ILIKE" + '\'%' + searchStr + '%\'').fetchall()
    searchISBN = db.execute("SELECT * FROM books WHERE isbn ILIKE" + '\'%' + searchStr + '%\'').fetchall()
    return searchTitle, searchAuthor, searchISBN

# Check if the given ISBN exists in the Books Database
def isBookISBNInDB(ISBN):
    searchISBN = db.execute("SELECT * FROM books WHERE isbn = :ISBN",{"ISBN":ISBN}).fetchone()
    return searchISBN

# Create the Book Review Table
def createBookReviewTable():
    db.execute("CREATE TABLE IF NOT EXISTS bookreview (id SERIAL PRIMARY KEY, userID INTEGER REFERENCES appuser, bookID INTEGER REFERENCES books, review VARCHAR NOT NULL, rating INTEGER NOT NULL)")
    db.commit()

# Check if user review exists in the Book Review Table
def isUserReviewInTable(uid,bookid):
    if db.execute("SELECT * FROM bookreview WHERE userID =:uID AND bookID =:bID",{'uID':uid,'bID':bookid}).rowcount == 0:
        return False
    else:
        return True

# Check if there are any Reviews in the Book Review Table
def isReviewInTable(bookid):
    if db.execute("SELECT * FROM bookreview WHERE bookID =:bID",{'bID':bookid}).rowcount == 0:
        return False
    else:
        return True

# Insert a given review in the Book Review Database
def insertReviewInBook(uid,bookid,reviewStr,rating):
    if not isUserReviewInTable(uid, bookid):
        db.execute("INSERT INTO bookreview (userID, bookID, review, rating) VALUES (:userID, :bookID, :review,:rating)", {"userID":uid, "bookID":bookid, "review":reviewStr, "rating":rating})
        db.commit()
        return True
    else:
        return False

# Get all book reviews for a particular book.
def getBookReviews(bookID):
    if isReviewInTable(bookID):
        return db.execute("SELECT * FROM bookreview WHERE bookID =:bookID",{'bookID':bookID}).fetchall()
    else:
        return False # Check This

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
    session.clear()
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
        return render_template("login.html")
    else:
        return render_template("error.html",message="Wrong Credentials. Pls Try Again")


@app.route("/signup",methods=["GET"])
def signup():
    return render_template("signup.html")

@app.route("/logoff",methods=["GET"])
def logoff():
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
            bookStr = request.form.get('searchStr')
            findTitle, findAuthor, findISBN = isBookInDB(bookStr)
            if not findTitle and not findAuthor and not findISBN:
                return render_template("error.html",message="No Match Found, Change the search Query.")
            else:
                return render_template("results.html",titles=findTitle,authors=findAuthor,isbn=findISBN)
        else:
            return render_template("error.html",message="Session Ended. Pls go to Home Page and Log In Again")
    except:
        return render_template("error.html",message="Exception in Application Caught Error Code 2")

@app.route("/book/<int:book_id>",methods=["GET","POST"])
def book(book_id):
    try:
        if isAuth():
            bookSel = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
            user = db.execute("SELECT * FROM appuser WHERE userID = :id",{'id':session["user"]}).fetchone()
            debugCode = 0
            userReview = request.form.get('bookReview')
            userRating = request.form.get('rate')
            print(userRating)

            if isUserReviewInTable(user[0],bookSel[0]):
                debugCode = 1

            elif userReview:
                debugCode = 1
                insertReviewInBook(user[0],bookSel[0],userReview,userRating)

            else:
                debugCode = 0

            bookReviews = db.execute("SELECT review,rating, fname, lname FROM bookreview JOIN appuser ON bookreview.userID = appuser.id WHERE bookreview.bookID=:bookID",{'bookID':bookSel[0]}).fetchall()
            gr = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key":grKEY,"isbns":bookSel[1]})
            if gr.status_code != 200:
                raise Exeception("Error: API request unsuccessful.")
            grDATA = gr.json()
            grAvgRating = grDATA['books'][0]['average_rating']
            grReviewCount = grDATA['books'][0]['ratings_count']
            return render_template("book.html",book=bookSel,grAvgRating=grAvgRating,grReviewCount=grReviewCount,debugCode=debugCode,bookreview=bookReviews)
        else:
            return render_template("error.html",message="Session Ended. Pls Try Again")
    except:
         return render_template("error.html",message="Exception in Application Caught Error Code 3")

@app.route("/api/<isbn>")
def book_api(isbn):
    """Return details about a single book."""
    searchISBN = isBookISBNInDB(isbn);
    # Make sure book exists.
    if searchISBN is None:
        return jsonify({"error": "Invalid book ISBN"}), 404

    #bookRating, bookRatingCount =
    avgRating = db.execute("SELECT AVG(rating)from bookreview WHERE bookID=:bookID",{'bookID':searchISBN.id}).fetchall()
    ratingCount = db.execute("SELECT COUNT(rating)from bookreview WHERE bookID=:bookID",{'bookID':searchISBN.id}).fetchall()
    bookTitle = searchISBN.title
    bookAuthor = searchISBN.author
    bookYear =  searchISBN.year
    bookISBN = searchISBN.isbn
    bookRating = round(avgRating[0][0],1)
    bookRatingCount = str(ratingCount[0][0])
    # review_counnt = db.execute("SELECT ")
    return jsonify({
            "title": bookTitle,
            "author": bookAuthor,
            "year":bookYear,
            "isbn":bookISBN,
            "review_count":bookRatingCount,
            "average_score":str(bookRating)
        })

#
# End of Routes
#
################################################################################

# Logical Block to Operate the code

createUserTable()
createBookReviewTable()
