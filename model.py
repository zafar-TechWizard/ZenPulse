from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    moods = db.relationship('MoodEntry', backref='user', lazy=True)
    chat_history = db.relationship('ChatMessage', backref='user', lazy=True)
    daily_activities = db.relationship('DailyActivity', backref='user', lazy=True)
    pet_conversations = db.relationship('PetConversation', backref='user', lazy=True)

class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class DailyActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    fed_pet = db.Column(db.Boolean, default=False)
    logged_mood = db.Column(db.Boolean, default=False)
    played_with_pet = db.Column(db.Boolean, default=False)
    pet_slept = db.Column(db.Boolean, default=False)
    completed_challenge = db.Column(db.Boolean, default=False)
    last_pet_interaction = db.Column(db.DateTime, default=None)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='user_daily_activity'),)

class PetConversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.Date, default=date.today)

    __table_args__ = (db.Index('idx_user_date', user_id, date),)
