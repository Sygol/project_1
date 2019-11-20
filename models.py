# from flask import Flask
# from flask_login import UserMixin
# from flask_sqlalchemy import SQLAlchemy
#
# app = Flask(__name__)
# db = SQLAlchemy()
# db.init_app(app)
#
# class User(db.Model, UserMixin):
#     __tablename__ = "users"
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     email = db.Column(db.String(50), unique=True, nullable=False)
#     _password = db.Column(db.String(128))
#
#
# class Book(db.Model):
#     __tablename__="books"
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     isbn = db.Column(db.String(50), unique=True)
#     title = db.Column(db.String(100))
#     author = db.Column(db.String(100))
#     year = db.Column(db.Integer)
#
#
# class BookReview(db.Model):
#     __tablename__="book_review"
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     book_id = db.relationship("Book", backref="book", lazy=True)
#     rating = db.Column(db.Integer, nullable=False)
#     review = db.Column(db.Text, nullable=True)
#
# def main() :
#     db.create_all()
#
# if __name__=="__main__":
#     with app.app_context():
#         main()