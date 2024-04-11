from flask import render_template, url_for, flash, redirect
from Assignment import app
from Assignment.forms import Registeration, Login
from Assignment.models import User, Message

###homepage
@app.route("/")
def home():
    return "Hello world"

###register
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Registeration()
    if form.validate_on_submit():
        ##store the name and passwrod into db
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form = form)

###login
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        if form.username.data == "11" and form.password.data == '11': ###change to database and search in db, 
            return redirect(url_for('home'))
    return render_template('login.html', title='Login', form = form)
