import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Customer, Game, Genre, Tag
import random


def create_users():
    print("Создание пользователей с разными ролями...")

    # 1. Менеджер (staff)
    if not User.objects.filter(username='manager').exists():
        manager = User.objects.create_user(
            username='manager',
            email='manager@gamestore.com',
            password='manager123'
        )
        manager.is_staff = True  # Доступ к админке
        manager.save()

        # Создаем профиль клиента для менеджера
        Customer.objects.create(
            user=manager,
            phone='+79991112233',
            address='ул. Менеджерская, д. 1'
        )
        print("✅ Создан менеджер:")
        print("   Логин: manager")
        print("   Пароль: manager123")
        print("   Роль: Менеджер (доступ к админке и отчетам)")

    # 2. Обычный пользователь
    if not User.objects.filter(username='user').exists():
        user = User.objects.create_user(
            username='user',
            email='user@gamestore.com',
            password='user123'
        )
        user.save()

        # Создаем профиль клиента
        Customer.objects.create(
            user=user,
            phone='+79992223344',
            address='ул. Пользовательская, д. 2'
        )
        print("\n✅ Создан обычный пользователь:")
        print("   Логин: user")
        print("   Пароль: user123")
        print("   Роль: Обычный пользователь (может покупать игры)")

    # 3. Еще несколько тестовых пользователей
    test_users = [
        {'username': 'gamer1', 'email': 'gamer1@gamestore.com', 'password': 'gamer123'},
        {'username': 'gamer2', 'email': 'gamer2@gamestore.com', 'password': 'gamer123'},
        {'username': 'pro_gamer', 'email': 'pro@gamestore.com', 'password': 'pro123'},
    ]

    for user_data in test_users:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
            Customer.objects.create(
                user=user,
                phone=f'+7999{random.randint(1000000, 9999999)}',
                address=f'ул. Тестовая, д. {random.randint(1, 100)}'
            )
            print(f"   Дополнительный пользователь: {user_data['username']}/{user_data['password']}")

    # 4. Гость - это любой незалогиненный пользователь, не создаем отдельного

    print("\n" + "=" * 50)
    print("ДОСТУПНЫЕ ПОЛЬЗОВАТЕЛИ:")
    print("=" * 50)
    print("1. Администратор (у вас уже есть)")
    print("2. Менеджер: manager / manager123")
    print("3. Пользователь: user / user123")
    print("4. Гость: просто не входите в аккаунт")
    print("=" * 50)
    print("\nРазграничение прав:")
    print("- Гость: просмотр каталога, добавление в корзину, но не может оформить заказ")
    print("- Пользователь: всё, что может гость + оформление заказов")
    print("- Менеджер: всё, что может пользователь + доступ к отчетам и админке")
    print("- Администратор: полный доступ ко всему")


if __name__ == '__main__':
    create_users()

    