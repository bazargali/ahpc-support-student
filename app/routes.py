import os
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from . import db, mail
from .models import User, Ticket, Comment, Category

main = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('У вас нет доступа к этой странице.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
@login_required
def index():
    stats = {}
    if current_user.role == 'admin':
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
        stats = {
            'total_tickets': Ticket.query.count(),
            'total_users': User.query.count(),
            'open_tickets': Ticket.query.filter(Ticket.status.in_(['Новая', 'В работе'])).count()
        }
    elif current_user.role == 'staff': # Бывший engineer
        tickets = Ticket.query.filter((Ticket.assignee_id == current_user.id) | (Ticket.assignee_id == None)).order_by(Ticket.created_at.desc()).all()
        stats = {
            'new': Ticket.query.filter_by(status='Новая').count(),
            'assigned_to_me': Ticket.query.filter_by(assignee_id=current_user.id, status='В работе').count()
        }
    else: # 'user' (Студент)
        tickets = Ticket.query.filter_by(creator_id=current_user.id).order_by(Ticket.created_at.desc()).all()
        stats = {
            'total': len(tickets),
            'active': len([t for t in tickets if t.status in ['Новая', 'В работе']]),
            'completed': len([t for t in tickets if t.status == 'Выполнена'])
        }
    return render_template('index.html', tickets=tickets, stats=stats)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Неверный email или пароль.', 'danger')
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        group_number = request.form.get('group_number') # Группа студента
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован.', 'danger')
            return redirect(url_for('main.register'))
            
        new_user = User(email=email, full_name=full_name, group_number=group_number)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('main.index'))
    return render_template('register.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/create_ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location') # Контакты или кабинет
        category_id = request.form.get('category_id')
        attachment_filename = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                attachment_filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], attachment_filename))
        
        new_ticket = Ticket(
            title=title, description=description, location=location, 
            creator_id=current_user.id, category_id=category_id if category_id else None, 
            attachment_filename=attachment_filename
        )
        db.session.add(new_ticket)
        db.session.commit()
        flash('Ваша заявка успешно создана!', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_ticket.html', categories=categories)

@main.route('/ticket/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role == 'user' and ticket.creator_id != current_user.id:
        flash('У вас нет доступа к этой заявке.', 'danger')
        return redirect(url_for('main.index'))
    comments = Comment.query.filter_by(ticket_id=ticket.id).order_by(Comment.created_at.asc())
    return render_template('ticket_detail.html', ticket=ticket, comments=comments)

@main.route('/ticket/<int:ticket_id>/update', methods=['POST'])
@login_required
def update_ticket_status(ticket_id):
    # Только admin и staff могут менять статус
    if current_user.role not in ['staff', 'admin']: 
        flash('У вас нет прав для этого действия.', 'danger')
        return redirect(url_for('main.index'))
        
    ticket = Ticket.query.get_or_404(ticket_id)
    new_status = request.form.get('status')
    
    if new_status == 'В работе' and ticket.status == 'Новая':
        ticket.assignee_id = current_user.id
        
    ticket.status = new_status
    db.session.commit()
    
    # Отправка уведомления на Email
    if new_status in ['В работе', 'Выполнена']:
        try:
            msg = Message(
                f'Статус заявки #{ticket.id} обновлен',
                recipients=[ticket.creator.email]
            )
            msg.body = f"Здравствуйте, {ticket.creator.full_name}!\n\nСтатус вашей заявки «{ticket.title}» был изменен на «{new_status}».\n\nПодробности в личном кабинете."
            mail.send(msg)
            flash(f'Статус обновлен. Уведомление отправлено.', 'success')
        except Exception as e:
            flash(f'Статус обновлен, но не удалось отправить email: {e}', 'warning')
    else:
        flash(f'Статус заявки обновлен.', 'info')
        
    return redirect(url_for('main.ticket_detail', ticket_id=ticket.id))

@main.route('/ticket/<int:ticket_id>/add_comment', methods=['POST'])
@login_required
def add_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role == 'user' and ticket.creator_id != current_user.id:
        flash('У вас нет прав.', 'danger')
        return redirect(url_for('main.index'))
    comment_text = request.form.get('comment_text')
    if comment_text:
        new_comment = Comment(text=comment_text, user_id=current_user.id, ticket_id=ticket.id)
        db.session.add(new_comment)
        db.session.commit()
        flash('Комментарий добавлен.', 'success')
    else:
        flash('Комментарий не может быть пустым.', 'danger')
    return redirect(url_for('main.ticket_detail', ticket_id=ticket.id))

@main.route('/admin/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_categories():
    if request.method == 'POST':
        category_name = request.form.get('name')
        if category_name and not Category.query.filter_by(name=category_name).first():
            new_category = Category(name=category_name)
            db.session.add(new_category)
            db.session.commit()
            flash('Категория успешно добавлена.', 'success')
        else:
            flash('Такая категория уже существует или имя пустое.', 'danger')
        return redirect(url_for('main.admin_categories'))
    categories = Category.query.all()
    return render_template('admin_categories.html', categories=categories)

@main.route('/admin/category/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    category_to_delete = Category.query.get_or_404(category_id)
    if category_to_delete.tickets:
        flash('Нельзя удалить категорию, в которой есть заявки.', 'danger')
    else:
        db.session.delete(category_to_delete)
        db.session.commit()
        flash(f'Категория «{category_to_delete.name}» удалена.', 'success')
    return redirect(url_for('main.admin_categories'))

@main.route('/uploads/<path:filename>')
def serve_upload(filename):
    upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
    return send_from_directory(os.path.abspath(upload_folder), filename)