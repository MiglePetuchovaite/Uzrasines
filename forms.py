from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, StringField, PasswordField, TextAreaField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, ValidationError, EqualTo, Length
from wtforms_sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
import app

class RegisterForm(FlaskForm):
    name = StringField('Name', [DataRequired()])
    email = StringField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    repeat_password = PasswordField("Repeat Password", [EqualTo('password', "Password have to macth.")])
    submit = SubmitField('Register')

    def check_name(self, name):
        user = app.User.query.filter_by(name=name.data).first()
        if user:
            raise ValidationError('This name is used. Please enter other name.')

    def check_email(self, email):
        user = app.User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is used. Please enter other email.')
            
class LoginForm(FlaskForm):
    email = StringField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log in')


class SearchForm(FlaskForm):
    searched = StringField('Paieška', [DataRequired()])
    submit = SubmitField('Ieškoti')


class CategoryForm(FlaskForm):
    name = StringField('Pavadinimas', [DataRequired()])
    submit = SubmitField('Pridėti')


class NoteForm(FlaskForm):
    title = StringField('Pavadinimas', [DataRequired(), Length(max=25)])
    text = TextAreaField('Užrašas', [DataRequired()])
    photo = FileField('Nuotrauka', validators=[FileAllowed(['jpg', 'png'])])
    categories = QuerySelectMultipleField("Kategorijos", get_label="name", get_pk=lambda obj: str(obj.id))
    submit = SubmitField('Pridėti')