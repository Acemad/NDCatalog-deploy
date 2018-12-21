#!/usr/bin/env python3
"""
AWBooks
A web application written in Python/Flask by Ouessai Abdessamed.
For the Udacity 'Full Stack Web Developer Nanodegree'
12/2018
Purpose : this is a data driven tech books catalog.
"""
from flask import Flask, render_template, request, redirect, url_for
from flask import session as user_session, flash, jsonify
from catalog.models import db, Author, User, Book, Category
from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound
import json
import random
import string
import httplib2


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///techBooks.db'
# Adds a sginificant perormance overhead, switching off is recomended
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'  # Required foe session object
db.init_app(app)  # Initialize our database with the app
with app.app_context():  # required for db to identify app context
    db.create_all()

@app.route('/')
def home():
    """
    READ -
    Web app initial route, shows links to all the available categories
    along the login link
    """
    categories = Category.query.all()  # Gets all categories
    return render_template('home.html',
                           categories=categories,
                           user_session=user_session)


@app.route('/tech/<category_slug>')
def showCategory(category_slug):
    """
    READ -
    Displays all the books in the provided category
    """
    # Get all the books in the provided category
    try:
        category = Category.query.filter_by(slug=category_slug).one()
    except NoResultFound:
        # Returns an error page when the category doesn't exist
        return render_template('error.html',
                               header='Category Error',
                               message="""The requested category
                                          does not exist !"""), 404
    books = Book.query.filter_by(category_id=category.id).all()
    return render_template('category.html',
                           books=books,
                           category=category,
                           user_session=user_session)


@app.route('/new',
           methods=['GET', 'POST'])
def newBook():
    """
    CREATE -
    (GET) displays the form needed to add a new book
          for a logged-in user
    (POST) creates a new book and its corresponding author
           from the data provided in the form, the user is
           bound by its id to the book he created
    """
    if 'username' not in user_session:  # in case the user hasn't signed in
        return render_template('error.html',
                               header='You Can\'t Add a New Book !',
                               message="""You need to log-in first before
                                          attempting to create a new book.""")
    if request.method == 'POST':
        category_id = get_category_id(request.form['category'])
        # Create a book
        book = Book(title=request.form['title'],
                    category_id=category_id,
                    publish_year=request.form['year'],
                    link=request.form['link'],
                    cover_url=request.form['coverUrl'],
                    summary=request.form['summary'],
                    isbn=request.form['isbn'],
                    user_id=user_session['user_id'],
                    slug=slugify(request.form['title']))
        db.session.add(book)
        # flush() is used To get the id of the newly created book
        db.session.flush()
        # Create an author
        # Every book has an author, even if his f_name, l_name is blank
        author = Author(book_id=book.id,
                        first_name=request.form['authorFName'],
                        last_name=request.form['authorLName'])
        db.session.add(author)
        db.session.commit()
        # Give feedback to the user
        flash('The Book was Added Successfully !')
        # redirect tp the book's category page
        category = Category.query.filter_by(id=category_id).one()
        return redirect(url_for('showCategory',
                                category_slug=category.slug))
    else:
        # GET request, renders the template containing the form
        categories = Category.query.all()
        return render_template('new.html',
                               categories=categories,
                               user_session=user_session)


@app.route('/tech/<category_slug>/<title_slug>')
def viewBook(category_slug, title_slug):
    """
    READ -
    Displays all the information contained within
    a single book record
    """
    # Retrieve the book using its title.
    try:
        book = Book.query.filter_by(slug=title_slug).one()
    except NoResultFound:
        # Returns an error page if the book doesn't exist
        return render_template('error.html',
                               header='Book Error',
                               message="""The requested book
                                          does not exist."""), 404
    author = Author.query.filter_by(book_id=book.id).one()
    category = Category.query.filter_by(id=book.category_id).one()
    return render_template('book.html',
                           book=book,
                           category=category,
                           author=author,
                           user_session=user_session)


@app.route('/tech/<category_slug>/<title_slug>/edit',
           methods=['GET', 'POST'])
def editBook(category_slug, title_slug):
    """
    UPDATE -
    (GET) displays the book edit form for a loged-in user
          that created the corresponding book
    (POST) updates the book with the data entred in
           the edit form, only updates fields which content
           was modified
    """
    if 'username' not in user_session:  # Check if user isn't loged-in
        return render_template('error.html',
                               header='You Can\'t Edit a Book !',
                               message="""You need to log-in first
                                          before attempting to edit a book.""")
    try:
        book = Book.query.filter_by(slug=title_slug).one()
    except NoResultFound:
        # Returns an error page if the book doesn't exist
        return render_template('error.html',
                               header='Book Error',
                               message="""The requested book
                                          does not exist."""), 404
    # Check if the loged-in user is the one who added the book
    if book.user_id != user_session['user_id']:
        return render_template('error.html',
                               header='You Can\'t Edit this Book !',
                               message="""This book was added by another user,
                                          you can\'t edit other
                                          user\'s books.""")
    # If cuurent user is the creator, continue
    author = Author.query.filter_by(book_id=book.id).one()
    categories = Category.query.all()
    if request.method == 'POST':
        # Update only the fields where there's new content
        if request.form['title'] != book.title:
            book.title = request.form['title']
            book.slug = slugify(book.title)
        if get_category_id(request.form['category']) != book.category_id:
            book.category_id = get_category_id(request.form['category'])
        if request.form['year'] != book.publish_year:
            book.publish_year = request.form['year']
        if request.form['link'] != book.link:
            book.link = request.form['link']
        if request.form['coverUrl'] != book.cover_url:
            book.cover_url = request.form['coverUrl']
        if request.form['summary'] != book.summary:
            book.summary = request.form['summary']
        if request.form['isbn'] != book.isbn:
            book.isbn = request.form['isbn']
        if request.form['authorFName'] != author.first_name:
            author.first_name = request.form['authorFName']
        if request.form['authorLName'] != author.last_name:
            author.last_name = request.form['authorLName']

        db.session.add(author)
        db.session.add(book)
        db.session.commit()
        flash('The Book was Edited Successfully !')
        # Redirect to the book's page
        return redirect(url_for('viewBook',
                                category_slug=slugify(
                                    get_category_name(book.category_id)),
                                title_slug=book.slug))
    else:
        return render_template('editBook.html',
                               book=book,
                               book_category_slug=category_slug,
                               categories=categories,
                               author=author,
                               user_session=user_session)


@app.route('/tech/<category_slug>/<title_slug>/delete',
           methods=['POST', 'GET'])
def deleteBook(category_slug, title_slug):
    """
    DELETE -
    (POST) Deletes a book from the database, can only
           be performed by the loged-in book creator
    (GET) Only accepted to return error messages
    """
    if 'username' not in user_session:  # Check if the user isn't logged-in
        return render_template('error.html',
                               header='You Can\'t Delete a Book !',
                               message="""You need to log-in first before
                                          attempting to delete a book.""")
    try:
        book = Book.query.filter_by(slug=title_slug).one()
    except NoResultFound:
        # Returns an error page if the book doesn't exist
        return render_template('error.html',
                               header='Book Error',
                               message="""The requested book
                                          does not exist."""), 404
    # Check if the current user is the creator of the book
    if book.user_id != user_session['user_id']:
        return render_template('error.html',
                               header='You Can\'t Delete this Book !',
                               message="""This book was added by another user, you can\'t
                                          delete other user\'s books.""")
    # Retrieve the book's author
    author = Author.query.filter_by(book_id=book.id).one()
    # Delete the book's author and the book from the database
    db.session.delete(author)
    db.session.delete(book)
    db.session.commit()
    flash('The Book was Deleted Successfully !')
    # Redirect to the deleted book's category page
    return redirect(url_for('showCategory',
                            category_slug=category_slug))


@app.route('/tech/<category_slug>/<title_slug>/json')
def bookJSON(category_slug, title_slug):
    """
    API Endpoint - READ -
    Returns informations about the provided book
    in JSON format
    """
    try:
        book = Book.query.filter_by(slug=title_slug).one()
    except:
        return render_template('error.html',
                               header='Book Error',
                               message="""The requested book
                                          does not exist."""), 404
    author = Author.query.filter_by(book_id=book.id).one()
    category = Category.query.filter_by(id=book.category_id).one()
    return jsonify(Book=book.serialize,
                   Author=author.serialize,
                   Category=category.serialize)


@app.route('/tech/<category_slug>/json')
def categoryJSON(category_slug):
    """
    API Endpoint - READ -
    Returns informations about all the books in the
    provided category in JSON format
    """
    try:
        category = Category.query.filter_by(slug=category_slug).one()
    except NoResultFound:
        return render_template('error.html',
                               header='Category Error',
                               message="""The requested category
                                          does not exist !"""), 404
    books = Book.query.filter_by(category_id=category.id).all()
    booksJson = []
    # Serialize each book in JSON format, with its author info
    for book in books:
        author = Author.query.filter_by(book_id=book.id).one()
        booksJson.append({'Book': book.serialize,
                          'Author': author.serialize,
                          'Category': category.serialize})
    return jsonify(Books=booksJson)


@app.route('/login')
def showLogin():
    """
    (GET) Generates a random session token and
          displays the login page
    """
    # Generates a random session token, length : 32 characters
    # used to protect against CSRF attacks
    state = ''.join(random.choice(
                    string.ascii_uppercase + string.digits)
                    for i in range(32))
    # Save token in session variable
    user_session['state'] = state
    return render_template('login.html',
                           state=user_session['state'],
                           user_session=user_session)


@app.route('/gconnect',
           methods=['POST'])
def gconnect():
    """
    (POST) Receievs the google user token from the client
           side and verifies it.
           Request user data from google and save it to
           the session object.
           A new user is created if it doesn't already exist.
    """
    # Check if the session token returned by the user is not
    # the same token that was generated for him -> CSRF protection
    # returns an error if true
    if request.args.get('state') != user_session['state']:
        return render_template('error.html',
                               header='Invalid Session',
                               message="""This session is invalid,
                                          please try again.""")
    # Verify google token validity by sending it back for verification
    h = httplib2.Http()
    url = "https://www.googleapis.com/oauth2/v3/tokeninfo?id_token=%s"
    url = url % request.data.decode('utf-8')
    resp, cont = h.request(url, 'GET')
    # Check response to see if token is valid
    if resp['status'] != '200':
        # Display an error if token not valid
        return render_template('error.html',
                               header='Invalid Issuer',
                               message='Token wasn\'t issued by Google.')
    # Deserialize data into a Json format
    data = json.loads(cont)
    # Save user data
    user_session['username'] = data['name']
    user_session['email'] = data['email']
    user_session['picture'] = data['picture']
    user_session['g_id'] = data['sub']
    # Check to see if user exists in our database
    # Create a new user if not
    user_id = get_user_id(user_session['email'])
    if not user_id:
        user_id = create_user(user_session)
    user_session['user_id'] = user_id
    flash('You have successfully Loged-in')
    # Redirect back home upon successful log-in
    return redirect(url_for('home'))


@app.route('/disconnect')
def disconnect():
    """
    (GET) Delete user data from session, disconnecting him
          from our app
    """
    del user_session['username']
    del user_session['email']
    del user_session['picture']
    del user_session['g_id']
    del user_session['user_id']
    flash('You have been Loged-out Successfully !')
    return redirect(url_for('home'))

######################
# Helper Functions ##
######################


def get_category_id(name):
    """
    Return a category's id given its name
    """
    category = Category.query.filter_by(name=name).one()
    return category.id


def get_category_name(id):
    """
    Returns a catergory's name given its id
    """
    category = Category.query.filter_by(id=id).one()
    return category.name


def get_user_id(email):
    """
    Returns a user id given his email
    Returns None if user doesn't exist
    """
    try:
        user = User.query.filter_by(email=email).one()
        return user.id
    except:
        return None


def create_user(user_session):
    """
    Creates a new user in the app's database
    with data from the session object
    """
    user = User(name=user_session['username'],
                email=user_session['email'],
                picture=user_session['picture'])
    db.session.add(user)
    # flush() is used to get the id of the new user
    db.session.flush()
    db.session.commit()
    return user.id

###########################
# Execution point ########
###########################

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
