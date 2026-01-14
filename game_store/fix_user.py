import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Customer

print("🔧 ИСПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ 'user'")
print("=" * 60)

# 1. Удаляем старого пользователя (если есть)
try:
    old_user = User.objects.get(username='user')
    old_user.delete()
    print("✅ Старый пользователь 'user' удален")
except User.DoesNotExist:
    pass

# 2. Создаем нового правильного пользователя
user = User.objects.create_user(
    username='user',
    email='user@gamestore.com',
    password='user123'
)
user.is_active = True
user.is_staff = False  # ВАЖНО: обычный пользователь НЕ staff!
user.is_superuser = False  # И НЕ суперпользователь!
user.save()

# 3. Создаем профиль клиента
Customer.objects.get_or_create(
    user=user,
    defaults={
        'phone': '+79992223344',
        'address': 'ул. Пользовательская, д. 2'
    }
)

print(f"✅ Новый пользователь создан:")
print(f"   Логин: user")
print(f"   Пароль: user123")
print(f"   is_staff: {user.is_staff}")
print(f"   is_superuser: {user.is_superuser}")
print(f"   is_active: {user.is_active}")

# 4. Проверяем аутентификацию
from django.contrib.auth import authenticate
test = authenticate(username='user', password='user123')
if test:
    print("✅ Аутентификация успешна!")
else:
    print("❌ Аутентификация не удалась")

print("\n" + "=" * 60)
print("🎯 КАК ВОЙТИ:")
print("=" * 60)
print("1. Перейдите: http://127.0.0.1:8000/")
print("2. Нажмите кнопку 'Войти' в шапке")
print("3. Введите: user / user123")
print("4. Должен произойти вход на сайт (не в админку!)")
print("=" * 60)