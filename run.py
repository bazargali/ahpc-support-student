from app import create_app, db
from app.models import User, Category

app = create_app()

with app.app_context():
    # --- НАЗАР АУДАРЫҢЫЗ: ОСЫ ЖЕР ӨЗГЕРДІ ---
    # Бұл ескі, қате кестелерді мәжбүрлеп өшіреді
    db.drop_all()  
    
    # Содан кейін жаңа, дұрыс кестелерді құрады
    db.create_all()
    # ----------------------------------------

    # Админді қосу
    if not User.query.filter_by(email='admin@college.kz').first():
        print("Админ құрылуда...")
        admin = User(email='admin@college.kz', full_name='Администратор Системы', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Staff қосу
    if not User.query.filter_by(email='support@college.kz').first():
        print("Staff құрылуда...")
        staff = User(email='support@college.kz', full_name='Студенческий Отдел', role='staff')
        staff.set_password('staff123')
        db.session.add(staff)

    # Категорияларды қосу
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
    
    db.session.commit()
    print("БАЗА ТОЛЫҒЫМЕН ЖАҢАРТЫЛДЫ!")

if __name__ == '__main__':
    app.run(debug=True) 