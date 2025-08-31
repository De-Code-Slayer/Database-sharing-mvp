# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, URL

class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=160)])
    username = StringField("Username", validators=[DataRequired(), Length(max=160)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField("Confirm password", validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField("Create account")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=160)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=160)])
    submit = SubmitField("Send reset link")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("New password", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField("Confirm password", validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField("Update password")

class CreateTenantForm(FlaskForm):
    #  name = StringField("Database Name", validators=[DataRequired()])
     db_type = SelectField(
        "Database Type",
        choices=[("postgresql", "PostgreSQL", "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg"), ("mysql", "MySQL", "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mysql/mysql-original.svg"), ("mongodb", "MongoDB", "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mongodb/mongodb-original.svg"), ("sqlite", "SQLite","https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sqlite/sqlite-original.svg")],
        validators=[DataRequired()]
                             ) 
     submit = SubmitField("Create")


class MigrateForm(FlaskForm):
    external_database_url = StringField("External DATABASE_URL", validators=[DataRequired(), URL(), Length(max=2000)])
    submit = SubmitField("Migrate")
