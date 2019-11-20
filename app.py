
import os

import flask
import requests
from flask import Flask, session, render_template, flash, request, url_for
from functools import wraps
from flask.json import jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from flask import redirect
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

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
connection = engine.raw_connection()
#
API_KEY = os.getenv("API_KEY")

curs = connection.cursor()
curs.execute("ROLLBACK")
connection.commit()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            next = url_for(request.endpoint, **request.view_args)
            return redirect(url_for('login', next=next))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/", methods=['GET', 'POST'])
def index():

    return render_template('index.html')


@app.route("/registration", methods=['GET', 'POST'])
def registration():
    if flask.request.method=='POST':
        session.clear()
        email = request.form.get('email')
        password = flask.request.values.get('password1')
        pw_hash = generate_password_hash(password)
        if db.execute("SELECT * from users WHERE email = :email", {'email': email}).first():
            flash("That username is already taken, please choose another")
            return redirect(url_for('registration'))
            #return render_template('registration.html', message="That username is already taken, please choose another")
        db.execute("INSERT INTO users (email, _password) VALUES (:email, :_password)",
                   {"email": email, "_password": pw_hash})
        db.commit()
        user = db.execute("SELECT * FROM users where email = :email", {"email": email}).first()
        session['email'] = email
        session['user_id'] = user.id

        return render_template('success.html')
    return render_template('registration.html')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if flask.request.method == 'POST':
        session.clear()
        email = request.form.get('email')
        password = flask.request.values.get('password')
        user = db.execute("SELECT * FROM users WHERE email=:email", {"email": email}).first()
        if user is None or not check_password_hash(user._password, password):
            flash("Invalid password or username")
            return redirect(url_for('login'))
        session['email'] = email
        session['user_id'] = user.id
        next_value = request.args.get('next')
        return redirect(next_value or url_for('books_search'))
    return render_template('login.html')


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route("/books-search", methods=['POST','GET'])
@login_required
def books_search():

    return render_template('books_search.html')


@app.route('/books')
@login_required
def books():
    if request.method == 'GET':
        isbn = request.args.get('isbn')
        author = request.args.get('author')
        title = request.args.get('title')
        if isbn or author or title:
            list_of_books = db.execute("SELECT * from books where isbn LIKE :isbn "
                                        "AND lower(author) LIKE :author AND lower(title) LIKE :title",
                                        {"isbn": '%'+isbn+'%', "author": '%'+author.lower()+'%', "title": '%'+title.lower()+'%'}).fetchall()
            # list_of_books = Book.query.filter(Book.isbn.startswith(isbn), Book.author.startswith(author),
            #                                   Book.title.startswith(title)).all()
            return render_template('books.html', list_of_books=list_of_books, isbn=isbn, author=author, title=title)
        else:
            return render_template('books_search.html')


@app.route("/books/<int:book_id>", methods=['POST', 'GET'])
@login_required
def book(book_id):
    if request.method == 'POST':
        if not db.execute("SELECT * FROM book_reviews WHERE user_id=:user_id AND book_id=:book_id",
                   {"user_id" : session['user_id'], "book_id": book_id}).first():
            rating = request.form.get('rating')
            review = request.form.get('review')
            db.execute("INSERT INTO book_reviews (user_id, book_id, rating, review) VALUES (:user_id, :book_id, :rating, :review)",{
                    "user_id": session["user_id"], "book_id": book_id, "rating": rating, "review": review})
            db.commit()
    book = db.execute("SELECT * FROM books where id=:book_id", {"book_id": book_id}).first()
    book_reviews = db.execute("SELECT * FROM book_reviews JOIN users u on u.id=book_reviews.user_id "
                              "WHERE book_id=:book_id AND user_id!=:user_id",
                              {"book_id": book_id, "user_id": session['user_id']}).fetchall()
    user_review = db.execute("SELECT * FROM book_reviews WHERE user_id=:user_id AND book_id=:book_id",
                             {"user_id": session['user_id'], "book_id": book_id}).first()
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": API_KEY, "isbns" : book.isbn})
    if res.status_code != 200:
        no_response = True
        return render_template('book.html', book=book, user_review=user_review, book_reviews=book_reviews,
                               user_email=session['email'], no_response=no_response)

    data = res.json()
    average_rating = data['books'][0]['average_rating']
    number_of_ratings = data['books'][0]['work_ratings_count']
    return render_template('book.html', book=book, user_review=user_review, book_reviews=book_reviews,
                           average_rating=average_rating, number_of_ratings=number_of_ratings,
                           user_email=session['email'])


@app.route("/api/<isbn>")
@login_required
def book_api(isbn):
    book = db.execute("SELECT b.id, title, author, year, isbn, ROUND((SUM(rating))/(COUNT(*))::numeric, 2) average_rating, "
                      "COUNT(*) no_of_ratings FROM books b JOIN book_reviews br on b.id = br.book_id WHERE isbn=:isbn "
                      "GROUP BY 1,2,3,4,5", {"isbn": isbn}).first()
    if book is None:
        book_no_reviews = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).first()
        if book_no_reviews is None:
            return jsonify({"error": "Invalid isbn"}), 404
        return jsonify({
            "title": book_no_reviews.title,
            "author": book_no_reviews.author,
            "year": book_no_reviews.year,
            "isbn": book_no_reviews.isbn,
            "review_count": 0,
            "average_score": 0.0,
            })
    average = float(book.average_rating)
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": book.no_of_ratings,
        "average_score": average,
        })