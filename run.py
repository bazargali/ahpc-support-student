from app import create_app, db
from app.models import User, Category

app = create_app()

# Бұл код сайт іске қосылған сайын орындалады
with app.app_context():
    # 1. Барлық кестелерді құру (Егер жоқ болса)
    db.create_all()

    # 2. Админді тексеру және қосу
    if not User.query.filter_by(email='admin@college.kz').first():
        print("Админ құрылуда...")
        admin = User(email='admin@college.kz', full_name='Администратор Системы', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
    
    # 3. Қызметкерді (Staff) қосу
    if not User.query.filter_by(email='support@college.kz').first():
        print("Staff құрылуда...")
        staff = User(email='support@college.kz', full_name='Студенческий Отдел', role='staff')
        staff.set_password('staff123')
        db.session.add(staff)

    # 4. Категорияларды қосу
    default_categories = [
        'Успеваемость / Оценки',
        'Справки и документы (ЦОН)',
        'Вопросы по общежитию',
        'Стипендия и оплата',
        'Психологическая помощь',
        'Ошибки Canvas/Platonus',
        'Другие вопросы'
    ]

    for cat_name in default_categories:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
    
    # Өзгерістерді сақтау
    db.session.commit()
    print("Дерекқор тексерілді және жаңартылды!")

if __name__ == '__main__':
    app.run(debug=True)