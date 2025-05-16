# library_app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    author = db.Column(db.String(100))
    isbn = db.Column(db.String(20))
    category = db.Column(db.String(100))
    total_copies = db.Column(db.Integer)
    available_copies = db.Column(db.Integer)

class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User')
    book = db.relationship('Book')

# Admin credentials (for demo purposes)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')

# # Routes

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('student_dashboard'))

        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    books = Book.query.all()
    borrows = Borrow.query.all()
    return render_template('admin_dashboard.html', books=books, borrows=borrows)

@app.route('/admin/add_book', methods=['POST'])
def add_book():
    if not session.get('admin'):
        return redirect(url_for('login'))
    book = Book(
        title=request.form['title'],
        author=request.form['author'],
        isbn=request.form['isbn'],
        category=request.form['category'],
        total_copies=int(request.form['total_copies']),
        available_copies=int(request.form['total_copies'])
    )
    db.session.add(book)
    db.session.commit()
    flash("Book added successfully")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_book/<int:book_id>')
def delete_book(book_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    book = Book.query.get(book_id)
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted")
    return redirect(url_for('admin_dashboard'))

@app.route('/student')
def student_dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    books = Book.query.all()
    return render_template('student_dashboard.html', books=books)

@app.route('/borrow/<int:book_id>')
def borrow_book(book_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    book = Book.query.get(book_id)
    if book.available_copies > 0:
        borrow = Borrow(
            user_id=session['user_id'],
            book_id=book.id,
            due_date=datetime.utcnow() + timedelta(days=14)
        )
        book.available_copies -= 1
        db.session.add(borrow)
        db.session.commit()
        flash("Book borrowed successfully")
    else:
        flash("No copies available")
    return redirect(url_for('student_dashboard'))

@app.route('/return/<int:borrow_id>')
def return_book(borrow_id):
    borrow = Borrow.query.get(borrow_id)
    if borrow.return_date is None:
        borrow.return_date = datetime.utcnow()
        book = Book.query.get(borrow.book_id)
        book.available_copies += 1
        db.session.commit()
        flash("Book returned")
    return redirect(url_for('student_dashboard'))

@app.route('/mybooks')
def my_books():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    borrows = Borrow.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_books.html', borrows=borrows)

# Entry point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


