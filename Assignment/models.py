##database
from Assignment import db, login_manager
from flask_login import UserMixin
from enum import Enum

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

###Role table
class UserRole(Enum):
    student = 'STUDENT'
    academics = 'ACADEMICS STAFF'
    administrative = 'ADMINISTRATIVE STAFF'
    admin = 'ADMIN STAFF'

##User table
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    # salt = db.Column(db.String(4), nullable=False)
    messages = db.relationship('Message', lazy=True)
    role = db.Column(db.Enum(UserRole))
    online = db.Column(db.Boolean, default=False)
    def __repr__(self):
        return f"User('{self.username}','{self.password}','{self.salt}')"

##Room table
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4), unique=True, nullable=False)
    messages = db.relationship('Message', backref='room', lazy=True)
    creater = db.Column(db.String(20), db.ForeignKey('user.username'),nullable=True)
    receiver = db.Column(db.String(20), db.ForeignKey('user.username'),nullable=True)
    def __repr__(self):
        return f"Room('{self.code}')"

##Message table
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    user_name = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    def __repr__(self):
        return f"Mesage('{self.message}')"  
    
##Friend Request table
class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    accepted = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    

    def __repr__(self):
        return f"Friend Request from('{self.sender_id}') to ('{self.receiver_id}', state:('{self.accepted}'))"
##Key table
# class Key(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
#     public_key = db.Column(db.String(256), nullable=False)


###Post table
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poster = db.relationship('User', foreign_keys=[poster_id])
    content = db.Column(db.Text, nullable=False)
    