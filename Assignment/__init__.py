from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import join_room, leave_room, send, SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = '365eff69d1d3c150a10adc94f2926365'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)
bcrypt = Bcrypt(app) 
login_manager = LoginManager(app)


from Assignment import routes