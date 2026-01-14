import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from store.models import Game, Review, User

print("=" * 60)
print("🔍 ПРОВЕРКА ОТЗЫВОВ В БАЗЕ ДАННЫХ")
print("=" * 60)

# 1. Проверяем всех пользователей
print("\n👥 ПОЛЬЗОВАТЕЛИ В СИСТЕМЕ:")
users = User.objects.all()
for user in users:
    print(f"  - {user.username} (email: {user.email})")

# 2. Проверяем игры
print("\n🎮 ИГРЫ В СИСТЕМЕ:")
games = Game.objects.all()
for game in games[:10]:  # первые 10 игр
    print(f"  - ID: {game.id}, '{game.title}'")

# 3. Проверяем отзывы
print("\n📝 ВСЕ ОТЗЫВЫ В СИСТЕМЕ:")
all_reviews = Review.objects.all()
if all_reviews:
    for review in all_reviews:
        status = "✅ Одобрен" if review.is_approved else "❌ Не одобрен"
        print(f"  - ID: {review.id}")
        print(f"    Игра: '{review.game.title}' (ID: {review.game.id})")
        print(f"    Пользователь: {review.user.username}")
        print(f"    Рейтинг: {review.rating}/5")
        print(f"    Статус: {status}")
        print(f"    Текст: {review.comment[:100]}...")
        print()
else:
    print("  ❌ Нет отзывов в базе данных!")

# 4. Проверяем отзывы для конкретных игр
print("\n🔎 ОТЗЫВЫ ПО ИГРАМ:")
for game in games[:5]:  # первые 5 игр
    reviews = Review.objects.filter(game=game, is_approved=True)
    print(f"\n  Игра: '{game.title}' (ID: {game.id})")
    print(f"  Всего отзывов: {reviews.count()}")

    if reviews:
        for review in reviews:
            print(f"    - {review.user.username}: {review.rating}/5 - '{review.comment[:50]}...'")

print("\n" + "=" * 60)
print("🎯 РЕКОМЕНДАЦИИ:")
print("=" * 60)

if not all_reviews:
    print("1. ❌ НЕТ ОТЗЫВОВ! Создайте тестовые отзывы:")
    print("""
from django.contrib.auth.models import User
from store.models import Game, Review

# Получаем пользователя и игру
user = User.objects.get(username='user')
game = Game.objects.first()

# Создаем отзыв
Review.objects.create(
    game=game,
    user=user,
    rating=5,
    comment='Отличная игра! Рекомендую всем.',
    is_approved=True
)
print(f"✅ Создан отзыв для '{game.title}'")
    """)

elif Review.objects.filter(is_approved=False).exists():
    print("2. ⚠️ Есть неодобренные отзывы. Проверьте is_approved=True")

print("3. 🔧 Проверьте шаблон game_detail.html:")
print("   - Используется ли game.reviews.filter(is_approved=True)")
print("   - Проверьте переменную reviews в контексте")

print("\n" + "=" * 60)

# 5. Создаем тестовый отзыв если их нет
create_test = input("\nСоздать тестовый отзыв? (y/n): ")
if create_test.lower() == 'y':
    try:
        user = User.objects.get(username='user')
        game = Game.objects.first()

        Review.objects.create(
            game=game,
            user=user,
            rating=5,
            comment='Тестовый отзыв для проверки работы системы.',
            is_approved=True
        )

        print(f"✅ Создан тестовый отзыв для '{game.title}' от пользователя '{user.username}'")

        # Проверяем
        test_review = Review.objects.filter(game=game, user=user).last()
        print(f"📝 Отзыв создан: ID={test_review.id}, Одобрен={test_review.is_approved}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")