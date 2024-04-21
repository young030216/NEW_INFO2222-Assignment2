from Assignment import db,app,bcrypt
from Assignment.models import User,Room
with app.app_context():
    db.drop_all()
    db.create_all()
    db.session.commit()