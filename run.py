from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Загрузка моделей
        from app.models import User, Category

        # Создание таблиц
        db.create_all()

        # 1. АДМИНИСТРАТОР
        if not User.query.filter_by(email='admin@college.kz').first():
            admin = User(email='admin@college.kz', full_name='Администратор Системы', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
        
        # 2. СОТРУДНИК ПОДДЕРЖКИ (Staff)
        if not User.query.filter_by(email='support@college.kz').first():
            staff = User(email='support@college.kz', full_name='Студенческий Отдел', role='staff')
            staff.set_password('staff123')
            db.session.add(staff)

        # 3. КАТЕГОРИИ ЗАЯВОК (На русском языке)
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
        print("База данных обновлена: добавлены русские категории и сотрудник.")

    app.run(debug=True)