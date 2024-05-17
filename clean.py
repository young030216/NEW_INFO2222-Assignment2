from Assignment import db,app
from Assignment.models import User, UserRole
with app.app_context():
    db.drop_all()
    db.create_all()
    user1 = User(username = "Sherlock", password = "2003", role = UserRole.admin)
    user2 = User(username = "Young", password = "123", role = UserRole.admin)
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    