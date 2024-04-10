from flask import Flask, render_template, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from forms import Registeration, Login

app = Flask(__name__)
app.config['SECRET_KEY'] = '365eff69d1d3c150a10adc94f2926365'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
db = SQLAlchemy(app)
from models import User, Message

###homepage
@app.route("/")
def home():
    return "Hello world"

###register
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Registeration()
    if form.validate_on_submit():
        return redirect(url_for('home'))
    
    return render_template('register.html', title='Register', form = form)

###login
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        if form.username.data == "1" and form.password.data == '1':
            return redirect(url_for('home'))
    return render_template('login.html', title='Login', form = form)
if __name__ == '__main__':
    app.run(debug=True)