from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('earthquake_id', db.Integer, db.ForeignKey('earthquakes.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='ROLE_USER', nullable=False)

    favorited_earthquakes = db.relationship('Earthquake', secondary=favorites, lazy='dynamic',
                                    backref=db.backref('favorited_by', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def favorite(self, earthquake):
        if not self.is_favoriting(earthquake):
            self.favorited_earthquakes.append(earthquake)

    def unfavorite(self, earthquake):
        if self.is_favoriting(earthquake):
            self.favorited_earthquakes.remove(earthquake)

    def is_favoriting(self, earthquake):
        return self.favorited_earthquakes.filter(
            favorites.c.earthquake_id == earthquake.id).count() > 0

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Earthquake(db.Model):
    __tablename__ = 'earthquakes'
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer) # 序号
    time = db.Column(db.DateTime, nullable=False, index=True) # 发震日期
    longitude = db.Column(db.Float, nullable=False, index=True) # 经度
    latitude = db.Column(db.Float, nullable=False, index=True) # 纬度
    depth = db.Column(db.Float, nullable=False) # 震源深度
    magnitude = db.Column(db.Float, nullable=False, index=True) # 震级
    location = db.Column(db.String(255)) # 震中位置
    event_type = db.Column(db.String(50)) # 事件类型

    def to_dict(self):
        return {
            'id': self.id,
            'time': self.time.strftime('%Y-%m-%d %H:%M:%S'),
            'longitude': self.longitude,
            'latitude': self.latitude,
            'depth': self.depth,
            'magnitude': self.magnitude,
            'location': self.location,
            'event_type': self.event_type
        }

class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(255))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    def to_dict(self):
        return {
            'name': self.name,
            'display_name': self.display_name,
            'lat': self.latitude,
            'lon': self.longitude
        }

class UploadLog(db.Model):
    __tablename__ = 'upload_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    records_count = db.Column(db.Integer)  # 上传的记录数
    status = db.Column(db.String(50), default='success')  # success 或 failed
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=lambda: datetime.now())
    
    user = db.relationship('User', backref='upload_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.user.username if self.user else 'Unknown',
            'filename': self.filename,
            'records_count': self.records_count,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }
