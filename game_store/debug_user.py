import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from django.contrib.auth.models import User

print("🔍 ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ 'user'")
print("=" * 60)

try:
    user = User.objects.get(username='user')
    print(f"✅ Пользователь найден: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   is_active: {user.is_active}")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
    print(f"   Дата регистрации: {user.date_joined}")

    # Проверяем пароль
    from django.contrib.auth import authenticate

    test_user = authenticate(username='user', password='user123')
    if test_user:
        print("✅ Аутентификация успешна")
    else:
        print("❌ Аутентификация не удалась")

except User.DoesNotExist:
    print("❌ Пользователь 'user' не найден!")

print("\n" + "=" * 60)
print("👥 ВСЕ ПОЛЬЗОВАТЕЛИ:")
print("=" * 60)

for u in User.objects.all():
    print(f"👤 {u.username:15} | Active: {u.is_active} | Staff: {u.is_staff} | Superuser: {u.is_superuser}")