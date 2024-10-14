from manage_and_serve import app, db
with app.app_context():
    db.create_all()

