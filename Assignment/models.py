##database
from Assignment import db


##User table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    messages = db.relationship('Message', lazy=True)

    def __repr__(self):
        return f"User('{self.username}','{self.password}')"


##Message table
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Mesage('{self.message}')"  
    
        
