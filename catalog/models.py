from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """
    Model for storing app users
    """
    __tablename__ = 'user'
    id = db.Column(db.Integer,
                   primary_key=True)
    name = db.Column(db.String(64),
                     nullable=False)
    email = db.Column(db.String,
                      nullable=False)
    picture = db.Column(db.String)


class Category(db.Model):
    """
    Model for storign category information
    description field isn't currently used
    """
    __tablename__ = 'category'
    id = db.Column(db.Integer,
                   primary_key=True)
    name = db.Column(db.String,
                     nullable=False,
                     unique=True)
    icon_url = db.Column(db.String)
    description = db.Column(db.String)
    slug = db.Column(db.String)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description
        }


class Book(db.Model):
    """
    Book model used for storing books and their information
    maybe extended in the fututre for more info
    """
    __tablename__ = 'book'
    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    title = db.Column(db.String,
                      nullable=False)
    summary = db.Column(db.String)
    publish_year = db.Column(db.String(4))
    # Link to the book's web page
    link = db.Column(db.String)
    cover_url = db.Column(db.String)
    isbn = db.Column(db.String)
    # category id of the book
    category_id = db.Column(db.Integer,
                            db.ForeignKey('category.id'),
                            nullable=False)
    # id of the user who added the book
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    slug = db.Column(db.String)

    category = db.relationship(Category)
    user = db.relationship(User)

    # serializes the book data for Json API endpoints
    @property
    def serialize(self):
        return {
            'title': self.title,
            'summary': self.summary,
            'publish_year': self.publish_year,
            'link': self.link,
            'cover_url': self.cover_url,
            'isbn': self.isbn
        }


class Author(db.Model):
    """
    Model for storing author information
    Each author is bound to a book id
    """
    __tablename__ = 'author'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False, )
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)

    book = db.relationship(Book)

    # serializes author data for Json API endpoints
    @property
    def serialize(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name
        }
