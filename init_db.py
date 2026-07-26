from app import app, db
from app.models import User, Earthquake

def init_db():
    with app.app_context():
        db.create_all()
        
        # Delete old users if they exist
        users_to_delete = ['admin', 'user1', 'staff1', 'admin1']
        for username in users_to_delete:
            u = User.query.filter_by(username=username).first()
            if u:
                db.session.delete(u)
                print(f"Deleted user: {username}")

        # Create requested users
        users_to_create = [
            {'username': 'User1', 'password': '111111', 'role': 'ROLE_USER'},
            {'username': 'Staff1', 'password': '111111', 'role': 'ROLE_STAFF'},
            {'username': 'Admin1', 'password': '111111', 'role': 'ROLE_ADMIN'}
        ]

        for u in users_to_create:
            if not User.query.filter_by(username=u['username']).first():
                new_user = User(username=u['username'], role=u['role'])
                new_user.set_password(u['password'])
                db.session.add(new_user)
                print(f"User created (username: {u['username']}, role: {u['role']}).")
            
        db.session.commit()
        print("Database initialized.")

if __name__ == '__main__':
    init_db()
