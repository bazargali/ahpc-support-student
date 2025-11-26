from app import create_app, db
from app.models import User, Category

app = create_app()

with app.app_context():
    # db.drop_all()  <--- ЭТУ СТРОКУ МЫ УДАЛИЛИ ИЛИ ЗАКОММЕНТИРОВАЛИ
    
    # Создаем таблицы, только если их нет
    db.create_all()

    # 1. Проверяем и создаем Админа
    if not User.query.filter_by(email='admin@ahpc.kz').first():
        admin = User(email='admin@ahpc.kz', full_name='Администратор Системы', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
    
    # 2. Проверяем и создаем Staff
    if not User.query.filter_by(email='support@ahpc.kz').first():
        staff = User(email='support@ahpc.kz', full_name='Студенческий Отдел', role='staff')
        staff.set_password('staff123')
        db.session.add(staff)

    # 3. Категории
    default_categories = [
        'Успеваемость / Оценки',
        'Справки и документы (ЦОН)',
        'Вопросы по общежитию',
        'Стипендия и оплата',
        'Психологическая помощь',
        'Ошибки Platonus',
        'Другие вопросы'
    ]

    for cat_name in default_categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
    
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)