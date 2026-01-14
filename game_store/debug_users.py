import os
import django
import sqlite3

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from django.contrib.auth.hashers import make_password

print("🔍 ДЕБАГ ПОЛЬЗОВАТЕЛЕЙ")
print("=" * 60)

# 1. Проверим через Django ORM
from django.contrib.auth.models import User

print("1. Проверка через Django ORM:")
users = User.objects.all()
if users:
    for user in users:
        status = []
        if user.is_superuser: status.append("👑 Админ")
        if user.is_staff: status.append("📊 Менеджер")
        if user.is_active:
            status.append("✅ Активен")
        else:
            status.append("❌ Неактивен")

        print(f"   👤 {user.username:15} | {' | '.join(status)}")
else:
    print("   ❌ Нет пользователей в базе")

print("\n2. Проверка базы SQLite напрямую:")
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Проверяем таблицу auth_user
cursor.execute("SELECT username, password, is_staff, is_superuser, is_active FROM auth_user")
rows = cursor.fetchall()

if rows:
    print("   Таблица auth_user:")
    print("   " + "-" * 70)
    for row in rows:
        username, password, is_staff, is_superuser, is_active = row
        print(
            f"   👤 {username:15} | Пароль: {password[:30]}... | Стафф: {is_staff} | Админ: {is_superuser} | Активен: {is_active}")
else:
    print("   ❌ Таблица auth_user пуста!")

conn.close()

print("\n" + "=" * 60)
print("🛠️  РЕШЕНИЕ ПРОБЛЕМЫ:")
print("=" * 60)

# Создаем хэшированный пароль для проверки
test_password = "user123"
hashed_password = make_password(test_password)
print(f"1. Хэшированный пароль для 'user123':")
print(f"   {hashed_password[:50]}...")
print()
print("2. Выйдите из Django shell и создайте пользователей:")
print("""
python manage.py shell
from django.contrib.auth.models import User

# Удаляем старых пользователей (если есть)
User.objects.filter(username__in=['user', 'manager']).delete()

# Создаем менеджера
manager = User.objects.create_user(
    username='manager',
    email='manager@gamestore.com',
    password='manager123'
)
manager.is_staff = True
manager.is_active = True
manager.save()
print("✅ Менеджер создан: manager/manager123")

# Создаем пользователя
user = User.objects.create_user(
    username='user',
    email='user@gamestore.com',
    password='user123'
)
user.is_active = True
user.save()
print("✅ Пользователь создан: user/user123")
""")

print("\n3. Или создайте через команду:")
print("   python manage.py createsuperuser --username=manager --email=manager@gamestore.com")
print("   (пароль: manager123)")
print()
print("4. Проверьте, что сервер запущен:")
print("   python manage.py runserver")
print()
print("5. Войдите по адресу:")
print("   http://127.0.0.1:8000/admin/")
print("=" * 60)