import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

print("=" * 60)
print("🚀 ИСПРАВЛЕНИЕ СИСТЕМЫ АУТЕНТИФИКАЦИИ")
print("=" * 60)

# 1. Проверяем и обновляем пользователей
users = [
    ('admin', 'admin123', True, True),
    ('manager', 'manager123', True, False),
    ('user', 'user123', False, False),
]

for username, password, is_staff, is_superuser in users:
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.is_active = True
        user.save()
        print(f"✅ {username:15} - обновлен (пароль: {password})")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=True
        )
        print(f"✅ {username:15} - создан (пароль: {password})")

print("\n" + "=" * 60)
print("🔧 ПРОВЕРКА ДОСТУПА:")
print("=" * 60)
print("1. ДЛЯ АДМИНИСТРАТОРА (полный доступ):")
print("   URL:      http://127.0.0.1:8000/admin/")
print("   Логин:    admin")
print("   Пароль:   admin123")
print()
print("2. ДЛЯ МЕНЕДЖЕРА И ПОЛЬЗОВАТЕЛЕЙ (сайт магазина):")
print("   URL:      http://127.0.0.1:8000/login/")
print("   Логин:    manager / manager123")
print("   Логин:    user / user123")
print()
print("3. ЕСЛИ ПЕРЕКИДЫВАЕТ НА АДМИНКУ:")
print("   Просто закройте вкладку и откройте:")
print("   http://127.0.0.1:8000/login/")
print("=" * 60)