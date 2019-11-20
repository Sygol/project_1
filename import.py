import csv
import os

from flask import Flask
from models import Book
from app import app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app import db, engine

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    next(reader, None)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        # book = Book(isbn=isbn, title=title, author=author, year=year)
        # db.session.add(book)
    db.commit()

if __name__ == "__main__":
    main()