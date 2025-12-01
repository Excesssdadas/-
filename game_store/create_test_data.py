import os
import django
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Genre, Tag, Game, Customer, Order, OrderItem


def create_test_data():
    print("Создание тестовых данных...")

    # Создаем суперпользователя если нет
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Создан суперпользователь: admin/admin")

    # Создаем менеджера
    if not User.objects.filter(username='manager').exists():
        manager = User.objects.create_user('manager', 'manager@example.com', 'manager')
        manager.is_staff = True
        manager.save()
        Customer.objects.create(user=manager, phone='+79991112233')
        print("Создан менеджер: manager/manager")

    # Создаем обычного пользователя
    if not User.objects.filter(username='user').exists():
        user = User.objects.create_user('user', 'user@example.com', 'user')
        Customer.objects.create(user=user, phone='+79992223344', address='ул. Примерная, д. 1')
        print("Создан пользователь: user/user")

    # Жанры
    genres = ['Шутер', 'Стратегия', 'RPG', 'Приключения', 'Гонки', 'Спорт']
    genre_objs = []
    for genre_name in genres:
        genre, created = Genre.objects.get_or_create(name=genre_name)
        genre_objs.append(genre)
        if created:
            print(f"Создан жанр: {genre_name}")

    # Теги
    tags = ['Стелс', 'Новелла', 'Соус-лайк', 'Открытый мир', 'Мультиплеер', 'Однопользовательская']
    tag_objs = []
    for tag_name in tags:
        tag, created = Tag.objects.get_or_create(name=tag_name)
        tag_objs.append(tag)
        if created:
            print(f"Создан тег: {tag_name}")

    # Игры
    games_data = [
        {'title': 'Cyberpunk 2077', 'price': 1999.99, 'genre': 'RPG', 'tags': ['Открытый мир', 'Ролевая']},
        {'title': 'Counter-Strike 2', 'price': 1499.99, 'genre': 'Шутер', 'tags': ['Мультиплеер']},
        {'title': 'Civilization VI', 'price': 1299.99, 'genre': 'Стратегия', 'tags': ['Пошаговая']},
        {'title': 'The Witcher 3', 'price': 899.99, 'genre': 'RPG', 'tags': ['Открытый мир', 'Приключения']},
        {'title': 'Forza Horizon 5', 'price': 2499.99, 'genre': 'Гонки', 'tags': ['Открытый мир']},
        {'title': 'FIFA 24', 'price': 2999.99, 'genre': 'Спорт', 'tags': ['Мультиплеер']},
        {'title': 'Portal 2', 'price': 499.99, 'genre': 'Приключения', 'tags': ['Головоломка']},
        {'title': 'Stardew Valley', 'price': 399.99, 'genre': 'Приключения', 'tags': ['Симулятор']},
        {'title': 'Doom Eternal', 'price': 1799.99, 'genre': 'Шутер', 'tags': ['Экшен']},
        {'title': 'Age of Empires IV', 'price': 1699.99, 'genre': 'Стратегия', 'tags': ['Историческая']},
    ]

    for game_data in games_data:
        game, created = Game.objects.get_or_create(
            title=game_data['title'],
            defaults={
                'description': f'Описание для игры {game_data["title"]}. Это отличная игра в жанре {game_data["genre"]}.',
                'price': Decimal(game_data['price']),
                'quantity': random.randint(5, 50),
                'genre': Genre.objects.get(name=game_data['genre']),
            }
        )

        if created:
            for tag_name in game_data['tags']:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                game.tags.add(tag)

            print(f"Создана игра: {game_data['title']}")

    print("\nТестовые данные созданы успешно!")
    print("\nДоступные пользователи:")
    print("1. admin / admin (суперпользователь)")
    print("2. manager / manager (менеджер)")
    print("3. user / user (обычный пользователь)")


if __name__ == '__main__':
    create_test_data()