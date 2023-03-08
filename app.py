import os
from flask import Flask
from flask import redirect, render_template, url_for, flash, request
from flask_login import LoginManager, UserMixin, current_user, logout_user, login_user, login_required
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import secrets
from PIL import Image
import forms


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

bcrypt = Bcrypt(app)
app.app_context().push()
app.config['SECRET_KEY'] = '4654f5dfadsrfasdr54e6rae'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'notes.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'register'
login_manager.login_message_category = 'info'

notes_categories = db.Table('notes_categories', db.metadata,
    db.Column('id', db.Integer, primary_key=True),
    db.Column('note_id', db.Integer, db.ForeignKey('notes.id')),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'))
)


class User(db.Model, UserMixin):
     __tablename__ = "user"
     id = db.Column(db.Integer, primary_key=True)
     name = db.Column("Name", db.String(20), unique=True, nullable=False)
     email = db.Column("Email", db.String(120), unique=True, nullable=False)
     password = db.Column("Password", db.String(60), unique=True, nullable=False)
     categories = db.relationship("Category", lazy=True)
     notes = db.relationship("Note", lazy=True)

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("Name", db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", lazy=True)
    notes = db.relationship("Note", secondary=notes_categories, back_populates="categories")

class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column("Title", db.String(20), nullable=False)
    text =db.Column("Text", db.Text, nullable=False)
    photo = db.Column("Image", db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", lazy=True)
    categories = db.relationship('Category', secondary=notes_categories, back_populates="notes")


@login_manager.user_loader
def load_user(user_id):
    # db.create_all()
    return User.query.get(int(user_id))


@app.route("/register", methods=['GET', 'POST'])
def register():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('login'))
    form = forms.RegisterForm()
    if form.validate_on_submit():
        coded_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, email=form.email.data, password=coded_password)
        db.session.add(user)
        db.session.commit()
        flash('Registracija sekminga! Prisijunk!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('note'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('note'))
        else:
            flash('Failed to sign in. Check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.context_processor
def base():
    form = forms.SearchForm()
    return dict(form = form)


@app.route('/search', methods=["POST"])
@login_required
def search():
    forma = forms.SearchForm()
    notes = Note.query
    if forma.validate_on_submit():
        note.searched = forma.searched.data
        notes = notes.filter(Note.title.like('%' + note.searched + '%'))
        return render_template("search.html", form=forma, searched=note.searched, notes=notes)


@app.route('/category', methods=['GET', 'POST'])
@login_required
def category():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    forma = forms.CategoryForm()
    if forma.validate_on_submit():
        new_category = Category(name=forma.name.data, user_id=current_user.id)
        db.session.add(new_category)
        db.session.commit()
        db.create_all()
        categories = Category.query.filter_by(user_id=current_user.id).all()
        return redirect(url_for('category', form=False, categories=categories))
    return render_template('category.html', form=forma, categories=categories)


@app.route("/edit_category/<int:id>", methods=['GET', 'POST'])
@login_required
def edit_category(id):
    forma = forms.CategoryForm()
    category = Category.query.get(id)
    if forma.validate_on_submit() :
        category.name = forma.name.data
        db.session.commit()
        return redirect(url_for('category'))
    forma.name.data = category.name
    return render_template("edit_category.html", form=forma, category=category)


@app.route("/delete_category/<int:id>")
@login_required
def delete_category(id):
    category = Category.query.get(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('category'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images', picture_fn)
    picture_relative_path = '/static/images/' + picture_fn

    output_size = (225, 225)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_relative_path


@app.route('/note', methods=['GET', 'POST'])
@login_required
def note():
    notes = Note.query.filter_by(user_id=current_user.id).all()
    forma = forms.NoteForm()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    forma.categories.query = categories
    if forma.validate_on_submit():
        new_note = Note(title=forma.title.data, text=forma.text.data, user_id=current_user.id)  
        if forma.photo.data:
            photo_path = save_picture(forma.photo.data) 
            new_note.photo = photo_path
        for category in forma.categories.data:
            new_note.categories.append(Category.query.get(category.id))
        db.session.add(new_note)
        db.session.commit()
        notes = Note.query.filter_by(user_id=current_user.id).all()
        return redirect(url_for("note", form=False, notes=notes, categories=categories))
    return render_template('note.html', form=forma, notes=notes, categories=categories)


@app.route("/edit_note/<int:id>", methods=['GET', 'POST'])
@login_required
def edit_note(id):
    note = Note.query.get(id)
    forma = forms.NoteForm(obj=note)
    forma.categories.query = Category.query.filter_by(user_id=current_user.id).all()
    if forma.validate_on_submit():
        note.title = forma.title.data
        note.text = forma.text.data
        note.categories = forma.categories.data
        db.session.commit()
        return redirect(url_for('note'))
    return render_template("edit_note.html", form=forma, note=note)


@app.route("/delete/<int:id>")
@login_required
def delete_note(id):
    note = Note.query.get(id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('note'))


@app.route("/filter")
@login_required
def filter_notes():
    category_id = request.args.get('category')
    category = Category.query.get(category_id)
    if category:
        notes = category.notes
    else:
        notes = Note.query.all()
    return render_template("filter.html", notes=notes, category=category)


@app.route('/')
def index():
     return render_template('index.html')

if __name__ == '__main__':
    
    app.run(host='127.0.0.1', port=8000, debug=True)