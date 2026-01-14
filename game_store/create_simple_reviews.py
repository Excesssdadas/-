import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Game, Review


def create_simple_reviews():
    print("=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ОТЗЫВОВ (без заказов)")
    print("=" * 60)

    # Получаем пользователей
    users = User.objects.filter(username__in=['user', 'gamer1', 'gamer2', 'pro_gamer', 'manager'])
    games = Game.objects.all()[:10]  # первые 10 игр

    if not users.exists():
        print("❌ Нет пользователей!")
        return

    print(f"✅ Найдено пользователей: {users.count()}")
    print(f"✅ Найдено игр: {games.count()}")

    comments = [
        "Отличная игра! Графика на высоте, геймплей увлекательный.",
        "Очень понравилось, провел уже 50+ часов.",
        "Хорошая игра за свои деньги, рекомендую.",
        "Не ожидал такого качества, приятно удивлен!",
        "Лучшая игра в своем жанре, обязательно куплю продолжение.",
        "Неплохо, но есть небольшие баги. Разработчики обещали исправить.",
        "Игра стоит каждого рубля! Отличное времяпровождение.",
        "Купил по рекомендации друга, не пожалел.",
        "Отличный сюжет и проработанный мир.",
        "Хорошая многопользовательская составляющая."
    ]

    reviews_created = 0

    for game in games:
        # Для каждой игры создаем 2-3 отзыва от разных пользователей
        num_reviews = random.randint(2, 4)
        selected_users = random.sample(list(users), min(num_reviews, len(users)))

        for user in selected_users:
            # Проверяем, нет ли уже отзыва от этого пользователя
            if not Review.objects.filter(game=game, user=user).exists():
                rating = random.randint(3, 5)

                Review.objects.create(
                    game=game,
                    user=user,
                    rating=rating,
                    comment=random.choice(comments),
                    is_approved=True
                )
                reviews_created += 1
                print(f"  ✅ {user.username}: {game.title} ({rating}/5)")

    print("\n" + "=" * 60)
    print("📊 ИТОГИ:")
    print("=" * 60)

    print(f"✅ Создано отзывов: {reviews_created}")
    print(f"📝 Всего отзывов в системе: {Review.objects.count()}")

    # Показываем статистику
    print("\n🎮 ОТЗЫВЫ ПО ИГРАМ:")
    from django.db.models import Count, Avg

    games_with_reviews = Game.objects.annotate(
        review_count=Count('reviews')
    ).filter(review_count__gt=0).order_by('-review_count')

    for game in games_with_reviews:
        avg_rating = game.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        print(f"  {game.title}:")
        print(f"    - Отзывов: {game.review_count}")
        print(f"    - Средний рейтинг: {avg_rating:.1f}/5")

    print("\n👉 Проверьте страницу любой игры:")
    for game in games_with_reviews[:3]:
        print(f"   http://127.0.0.1:8000/games/{game.id}/")


if __name__ == '__main__':
    create_simple_reviews()