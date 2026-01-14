import os
import django
from datetime import datetime, timedelta
import random

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'game_store.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Game, Customer, Order, OrderItem
from django.db.models import Sum


def create_test_orders():
    print("=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ЗАКАЗОВ ДЛЯ ОТЧЕТОВ")
    print("=" * 60)

    # Проверяем наличие пользователей
    users = User.objects.filter(username__in=['user', 'gamer1', 'gamer2', 'pro_gamer', 'manager'])

    if not users.exists():
        print("❌ Нет тестовых пользователей!")
        print("   Сначала создайте пользователей через create_users.py")
        return

    games = Game.objects.all()

    if not games.exists():
        print("❌ Нет игр в базе данных!")
        print("   Добавьте игры через админку")
        return

    print(f"✅ Найдено пользователей: {users.count()}")
    print(f"✅ Найдено игр: {games.count()}")

    # Удаляем старые тестовые заказы (опционально)
    # Order.objects.all().delete()
    # print("🗑️  Удалены старые заказы")

    print("\n📦 Создание новых заказов...")

    # Создаем заказы за последние 2 недели
    orders_created = 0
    for i in range(25):  # Создаем 25 заказов
        try:
            user = random.choice(list(users))
            customer, created = Customer.objects.get_or_create(user=user)

            # Случайная дата за последние 2 недели
            days_ago = random.randint(0, 14)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            order_date = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

            # Создаем заказ
            order = Order.objects.create(
                customer=customer,
                status=random.choice(['completed', 'completed', 'completed', 'pending', 'processing']),
                total_amount=0,
                created_at=order_date
            )

            # Добавляем товары в заказ
            order_total = 0
            num_items = random.randint(1, 4)
            selected_games = random.sample(list(games), min(num_items, len(games)))

            for game in selected_games:
                quantity = random.randint(1, 3)
                price = game.price

                # Создаем элемент заказа
                OrderItem.objects.create(
                    order=order,
                    game=game,
                    quantity=quantity,
                    price=price
                )

                order_total += float(price) * quantity

            # Обновляем общую сумму
            order.total_amount = order_total
            order.save()

            orders_created += 1
            print(
                f"   ✅ Заказ #{order.id:3d} | {user.username:10s} | {order_total:8.2f}₽ | {order.get_status_display():15s} | {order.created_at.strftime('%d.%m.%Y')}")

        except Exception as e:
            print(f"   ❌ Ошибка при создании заказа: {e}")

    print("\n" + "=" * 60)
    print("📊 СТАТИСТИКА ПОСЛЕ СОЗДАНИЯ ЗАКАЗОВ")
    print("=" * 60)

    # Общая статистика
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='completed').count()
    pending_orders = Order.objects.filter(status='pending').count()

    # Суммарная статистика
    total_amount_result = Order.objects.aggregate(total=Sum('total_amount'))
    total_amount = total_amount_result['total'] or 0

    # Статистика по недельным продажам
    week_ago = datetime.now() - timedelta(days=7)
    weekly_orders = Order.objects.filter(created_at__gte=week_ago, status='completed')
    weekly_total = weekly_orders.aggregate(total=Sum('total_amount'))['total'] or 0

    print(f"📈 Всего заказов в системе: {total_orders}")
    print(f"✅ Завершенных заказов: {completed_orders}")
    print(f"⏳ Ожидающих обработки: {pending_orders}")
    print(f"💰 Общая сумма всех заказов: {total_amount:.2f}₽")
    print(f"📅 Продажи за последнюю неделю: {weekly_total:.2f}₽")

    # Статистика по популярным играм
    print("\n🎮 ТОП-5 САМЫХ ПРОДАВАЕМЫХ ИГР:")
    from django.db.models import Sum
    top_games = OrderItem.objects.values('game__title').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_sold')[:5]

    for i, game in enumerate(top_games, 1):
        print(
            f"   {i}. {game['game__title'][:30]:30s} | Продано: {game['total_sold']:3d} | Выручка: {game['total_revenue'] or 0:.2f}₽")

    print("\n" + "=" * 60)
    print("🔧 КАК ПРОВЕРИТЬ ОТЧЕТЫ:")
    print("=" * 60)
    print("1. Войдите как менеджер (manager/manager123)")
    print("2. Нажмите 'Администрирование' → 'Отчеты' в меню")
    print("3. Выберите нужный отчет:")
    print("   - 'Топ 10 самых продаваемых игр'")
    print("   - 'Продажи за неделю'")
    print("4. Можно экспортировать в JSON или CSV")
    print("=" * 60)

    print("\n👤 ДЛЯ ТЕСТИРОВАНИЯ РАЗНЫХ РОЛЕЙ:")
    print("- Гость: просто не входите в аккаунт")
    print("- Пользователь: user/user123")
    print("- Менеджер: manager/manager123")
    print("- Администратор: ваш суперпользователь")


if __name__ == '__main__':
    create_test_orders()