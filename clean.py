from Assignment import db,app,bcrypt
from Assignment.models import User
with app.app_context():
    db.drop_all()
    db.create_all()
    hassed_password = bcrypt.generate_password_hash("123").decode('utf-8')
    user = User(username = "123", password = hassed_password)
    db.session.add(user)
    db.session.commit()
    hassed_password = bcrypt.generate_password_hash("321").decode('utf-8')
    user = User(username = "321", password = hassed_password)
    db.session.add(user)
    db.session.commit()