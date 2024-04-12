from flask import render_template, url_for, flash, redirect
from Assignment import app, db, bcrypt
from Assignment.forms import Registeration, Login
from Assignment.models import User, Message


###homepage
@app.route("/")
def home():
    return render_template('home.html', title='homepage')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Registeration()
    if form.validate_on_submit():
        ##store the name and passwrod into db
        hassed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, password = hassed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to login', 'success')
        return redirect(url_for('home'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {getattr(form, field).label.text}: {error}', 'danger')
    return render_template('register.html', title='Register', form=form)

###login
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(user=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password','danger')
    return render_template('login.html', title='Login', form = form)
