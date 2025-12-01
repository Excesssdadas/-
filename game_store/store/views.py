from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
import json
from .models import Game, Genre, Tag, Customer, Order, OrderItem
from django.http import HttpResponse, JsonResponse


# Вспомогательные функции
def get_cart(request):
    """Получает корзину из сессии"""
    cart = request.session.get('cart', {})
    return cart


def save_cart(request, cart):
    """Сохраняет корзину в сессию"""
    request.session['cart'] = cart
    request.session.modified = True


def calculate_cart_total(cart):
    """Рассчитывает общую сумму корзины"""
    total = 0
    for game_id, item in cart.items():
        try:
            game = Game.objects.get(id=int(game_id))
            total += game.price * item['quantity']
        except (Game.DoesNotExist, ValueError):
            continue
    return total


# Основные представления
def home(request):
    """Главная страница"""
    # Получаем несколько игр для отображения на главной
    featured_games = Game.objects.filter(quantity__gt=0)[:6]
    genres = Genre.objects.all()[:5]

    return render(request, 'store/home.html', {
        'featured_games': featured_games,
        'genres': genres,
    })


def game_list(request):
    """Страница списка игр с фильтрацией"""
    games = Game.objects.filter(quantity__gt=0)

    # Фильтрация по жанру
    genre_id = request.GET.get('genre')
    if genre_id:
        games = games.filter(genre_id=genre_id)

    # Фильтрация по тегу
    tag_id = request.GET.get('tag')
    if tag_id:
        games = games.filter(tags__id=tag_id)

    # Поиск
    search_query = request.GET.get('search')
    if search_query:
        games = games.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Сортировка
    sort_by = request.GET.get('sort', 'title')
    if sort_by == 'price_asc':
        games = games.order_by('price')
    elif sort_by == 'price_desc':
        games = games.order_by('-price')
    elif sort_by == 'title':
        games = games.order_by('title')
    elif sort_by == 'newest':
        games = games.order_by('-created_at')

    genres = Genre.objects.all()
    tags = Tag.objects.all()
    cart = get_cart(request)

    return render(request, 'store/game_list.html', {
        'games': games,
        'genres': genres,
        'tags': tags,
        'cart_count': len(cart),
        'selected_genre': genre_id,
        'selected_tag': tag_id,
        'search_query': search_query or '',
        'sort_by': sort_by,
    })


def game_detail(request, game_id):
    """Страница деталей игры"""
    game = get_object_or_404(Game, id=game_id)
    cart = get_cart(request)
    in_cart = str(game_id) in cart

    return render(request, 'store/game_detail.html', {
        'game': game,
        'in_cart': in_cart,
        'cart_count': len(cart),
    })


def cart_view(request):
    """Просмотр корзины"""
    cart = get_cart(request)
    cart_items = []
    total_price = 0

    for game_id, item_data in cart.items():
        try:
            game = Game.objects.get(id=int(game_id))
            quantity = item_data['quantity']

            # Проверяем доступное количество
            available_quantity = game.quantity
            if quantity > available_quantity:
                messages.warning(request, f'Только {available_quantity} шт. {game.title} доступно')
                quantity = min(quantity, available_quantity)
                cart[game_id]['quantity'] = quantity
                save_cart(request, cart)

            item_total = game.price * quantity
            total_price += item_total

            cart_items.append({
                'game': game,
                'quantity': quantity,
                'total': item_total,
                'game_id': game_id,
            })
        except (Game.DoesNotExist, ValueError):
            # Удаляем несуществующий товар из корзины
            cart.pop(game_id, None)

    save_cart(request, cart)

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': len(cart),
    })


def add_to_cart(request, game_id):
    """Добавление игры в корзину"""
    game = get_object_or_404(Game, id=game_id)
    cart = get_cart(request)

    game_key = str(game_id)
    quantity = int(request.POST.get('quantity', 1))

    # Проверяем доступное количество
    if quantity > game.quantity:
        messages.error(request, f'Недостаточно товара. Доступно: {game.quantity}')
        return redirect('game_detail', game_id=game_id)

    if game_key in cart:
        # Обновляем количество
        new_quantity = cart[game_key]['quantity'] + quantity
        if new_quantity > game.quantity:
            messages.error(request, f'Недостаточно товара. Доступно: {game.quantity}')
            return redirect('game_detail', game_id=game_id)
        cart[game_key]['quantity'] = new_quantity
    else:
        # Добавляем новый товар
        cart[game_key] = {
            'quantity': quantity,
            'added_at': timezone.now().isoformat(),
        }

    save_cart(request, cart)
    messages.success(request, f'"{game.title}" добавлен в корзину')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': len(cart)})

    return redirect('game_detail', game_id=game_id)


def remove_from_cart(request, item_id):
    """Удаление игры из корзины"""
    cart = get_cart(request)

    if str(item_id) in cart:
        cart.pop(str(item_id))
        save_cart(request, cart)
        messages.success(request, 'Товар удален из корзины')

    return redirect('cart')


def update_cart_item(request, item_id):
    """Обновление количества товара в корзине"""
    if request.method == 'POST':
        cart = get_cart(request)
        game_key = str(item_id)

        if game_key in cart:
            try:
                quantity = int(request.POST.get('quantity', 1))
                game = Game.objects.get(id=item_id)

                if quantity <= 0:
                    cart.pop(game_key)
                    messages.success(request, 'Товар удален из корзины')
                elif quantity > game.quantity:
                    messages.error(request, f'Недостаточно товара. Доступно: {game.quantity}')
                    cart[game_key]['quantity'] = game.quantity
                else:
                    cart[game_key]['quantity'] = quantity
                    messages.success(request, 'Количество обновлено')

                save_cart(request, cart)
            except (ValueError, Game.DoesNotExist):
                messages.error(request, 'Ошибка обновления корзины')

    return redirect('cart')


@login_required
def checkout(request):
    """Оформление заказа"""
    cart = get_cart(request)

    if not cart:
        messages.error(request, 'Корзина пуста')
        return redirect('cart')

    # Проверяем, есть ли профиль клиента
    customer, created = Customer.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        try:
            # Создаем заказ
            order = Order.objects.create(
                customer=customer,
                status='pending',
                total_amount=0
            )

            total_amount = 0

            # Добавляем товары в заказ
            for game_id, item_data in cart.items():
                game = Game.objects.get(id=int(game_id))
                quantity = item_data['quantity']

                # Проверяем доступное количество
                if quantity > game.quantity:
                    messages.error(request, f'Недостаточно "{game.title}". Доступно: {game.quantity}')
                    order.delete()
                    return redirect('cart')

                # Создаем элемент заказа
                OrderItem.objects.create(
                    order=order,
                    game=game,
                    quantity=quantity,
                    price=game.price
                )

                # Обновляем количество товара
                game.quantity -= quantity
                game.save()

                total_amount += game.price * quantity

            # Обновляем общую сумму заказа
            order.total_amount = total_amount
            order.save()

            # Очищаем корзину
            request.session['cart'] = {}
            request.session.modified = True

            messages.success(request, f'Заказ #{order.id} успешно оформлен!')
            return redirect('home')

        except Exception as e:
            messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')
            return redirect('cart')

    # Подсчитываем итоги для подтверждения
    cart_items = []
    total_price = 0

    for game_id, item_data in cart.items():
        game = Game.objects.get(id=int(game_id))
        quantity = item_data['quantity']
        item_total = game.price * quantity
        total_price += item_total

        cart_items.append({
            'game': game,
            'quantity': quantity,
            'total': item_total,
        })

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'customer': customer,
        'cart_count': len(cart),
    })


# Функции для проверки ролей
def is_manager(user):
    return user.is_staff


def is_director(user):
    return user.is_superuser


@user_passes_test(is_manager)
def reports(request):
    """Страница отчетов (доступна менеджерам и директорам)"""
    return render(request, 'store/reports.html', {
        'cart_count': len(get_cart(request)),
    })


@user_passes_test(is_manager)
def top_games_report(request):
    """Отчет по 10 самым продаваемым играм"""
    # Получаем 10 самых продаваемых игр
    top_games = OrderItem.objects.values(
        'game__title', 'game__genre__name'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_sold')[:10]

    if request.GET.get('format') == 'json':
        data = list(top_games)
        return JsonResponse(data, safe=False)

    if request.GET.get('format') == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="top_games_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Игра', 'Жанр', 'Продано копий', 'Общая выручка'])

        for item in top_games:
            writer.writerow([
                item['game__title'],
                item['game__genre__name'],
                item['total_sold'],
                item['total_revenue']
            ])

        return response

    return render(request, 'store/reports/top_games.html', {
        'top_games': top_games,
        'cart_count': len(get_cart(request)),
    })


@user_passes_test(is_manager)
def weekly_sales_report(request):
    """Отчет по продажам за неделю"""
    week_ago = timezone.now() - timedelta(days=7)

    # Продажи за неделю
    weekly_sales = Order.objects.filter(
        created_at__gte=week_ago,
        status='completed'
    ).annotate(
        items_count=Count('orderitem')
    ).order_by('-created_at')

    # Статистика
    total_sales = weekly_sales.aggregate(
        total_amount=Sum('total_amount'),
        total_orders=Count('id')
    )

    if request.GET.get('format') == 'json':
        data = {
            'period': f'{week_ago.date()} - {timezone.now().date()}',
            'total_orders': total_sales['total_orders'] or 0,
            'total_amount': float(total_sales['total_amount'] or 0),
            'orders': list(weekly_sales.values('id', 'customer__user__username', 'total_amount', 'created_at'))
        }
        return JsonResponse(data)

    if request.GET.get('format') == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="weekly_sales_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Дата', 'Заказ №', 'Клиент', 'Сумма', 'Статус'])

        for order in weekly_sales:
            writer.writerow([
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                order.id,
                order.customer.user.username,
                order.total_amount,
                order.get_status_display()
            ])

        return response

    return render(request, 'store/reports/weekly_sales.html', {
        'weekly_sales': weekly_sales,
        'total_sales': total_sales,
        'week_start': week_ago.date(),
        'week_end': timezone.now().date(),
        'cart_count': len(get_cart(request)),
    })