from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    
    # --- ЖАҢА ӨРІС: Студенттің тобы ---
    group_number = db.Column(db.String(20), nullable=True) 
    
    password_hash = db.Column(db.String(128))
    # Рөлдер: 'user' (студент), 'staff' (қызметкер), 'admin'
    role = db.Column(db.String(10), nullable=False, default='user')
    
    created_tickets = db.relationship('Ticket', foreign_keys='Ticket.creator_id', backref='creator', lazy=True)
    assigned_tickets = db.relationship('Ticket', foreign_keys='Ticket.assignee_id', backref='assignee', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(50)) # Мұны "Кабинет" немесе "Байланыс телефоны" деп қолдануға болады
    status = db.Column(db.String(20), nullable=False, default='Новая')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    attachment_filename = db.Column(db.String(255), nullable=True)
    
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
    category = db.relationship('Category', backref=db.backref('tickets', lazy=True))
    comments = db.relationship('Comment', backref='ticket', lazy=True, cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)