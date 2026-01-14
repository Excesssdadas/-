import os
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Game, Customer, Order, OrderItem, Review


def create_reviews_with_orders():
    print("=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ЗАКАЗОВ И ОТЗЫВОВ")
    print("=" * 60)

    # Получаем пользователей
    users = User.objects.filter(username__in=['user', 'gamer1', 'gamer2', 'pro_gamer'])
    games = Game.objects.all()

    if not users.exists():
        print("❌ Нет пользователей!")
        return

    print(f"✅ Найдено пользователей: {users.count()}")
    print(f"✅ Найдено игр: {games.count()}")

    # Создаем заказы и отзывы для каждого пользователя
    for user in users:
        print(f"\n👤 Работаем с пользователем: {user.username}")

        # Создаем или получаем профиль клиента
        customer, created = Customer.objects.get_or_create(user=user)

        # Создаем заказ для пользователя
        order = Order.objects.create(
            customer=customer,
            status='completed',
            total_amount=0,
            payment_status='completed',
            payment_method='card'
        )

        # Выбираем случайные игры для покупки (1-3 игры)
        games_to_buy = random.sample(list(games), min(3, len(games)))
        order_total = 0

        for game in games_to_buy:
            quantity = random.randint(1, 2)

            # Создаем элемент заказа
            OrderItem.objects.create(
                order=order,
                game=game,
                quantity=quantity,
                price=game.price
            )

            order_total += game.price * quantity

            # Создаем отзыв для игры (если еще нет)
            if not Review.objects.filter(game=game, user=user).exists():
                rating = random.randint(3, 5)
                comments = [
                    "Отличная игра! Очень понравилась графика и геймплей.",
                    "Хорошая игра, но есть над чем поработать.",
                    "Рекомендую всем любителям жанра!",
                    "Купил по акции, не пожалел.",
                    "Игра стоит своих денег, проведено уже 100+ часов.",
                    "Лучшая игра в своем жанре!",
                    "Неплохо, но ожидал большего.",
                    "Отличное времяпровождение, советую друзьям."
                ]

                Review.objects.create(
                    game=game,
                    user=user,
                    rating=rating,
                    comment=random.choice(comments),
                    is_approved=True
                )
                print(f"  ✅ Создан отзыв для '{game.title}' ({rating}/5)")

        # Обновляем сумму заказа
        order.total_amount = order_total
        order.save()

        print(f"  ✅ Создан заказ #{order.id} на сумму {order_total:.2f} руб.")

    print("\n" + "=" * 60)
    print("📊 ИТОГИ:")
    print("=" * 60)

    # Статистика
    total_orders = Order.objects.count()
    total_reviews = Review.objects.count()
    users_with_reviews = User.objects.filter(review__isnull=False).distinct().count()

    print(f"📦 Всего заказов: {total_orders}")
    print(f"📝 Всего отзывов: {total_reviews}")
    print(f"👥 Пользователей с отзывами: {users_with_reviews}")

    # Показываем отзывы по играм
    print("\n🎮 ОТЗЫВЫ ПО ИГРАМ (топ-5):")
    from django.db.models import Count, Avg

    top_games = Game.objects.annotate(
        review_count=Count('reviews'),
        avg_rating=Avg('reviews__rating')
    ).filter(review_count__gt=0).order_by('-review_count')[:5]

    for game in top_games:
        print(f"  {game.title}:")
        print(f"    - Отзывов: {game.review_count}")
        print(f"    - Средний рейтинг: {game.avg_rating:.1f}/5")

        # Показываем последние отзывы
        recent_reviews = Review.objects.filter(game=game).order_by('-created_at')[:2]
        for review in recent_reviews:
            print(f"    - {review.user.username}: {review.rating}/5 - '{review.comment[:50]}...'")

    print("\n✅ Теперь пользователи могут оставлять отзывы!")
    print("👉 Проверьте страницу любой игры с ID от 1 до 10")


if __name__ == '__main__':
    create_reviews_with_orders()