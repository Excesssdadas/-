from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
import json
import uuid
from django.core.mail import send_mail
from django.conf import settings
from .models import Game, Genre, Tag, Customer, Order, OrderItem, Review
from django.http import HttpResponse, JsonResponse


# Вспомогательные функции
def get_cart(request):
    """Получает корзину из сессии"""
    cart = request.session.get('cart', {})
    return cart


def save_cart(request, cart):
    """Сохраняет корзину в сессии"""
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


# Вспомогательная функция для проверки роли менеджера
def is_manager(user):
    return user.is_staff


# ==================== ФУНКЦИИ АУТЕНТИФИКАЦИИ ====================

def custom_login(request):
    """Кастомная страница входа для магазина"""
    # Если пользователь уже авторизован, перенаправляем на главную
    if request.user.is_authenticated:
        return redirect('home')

    # Обработка POST-запроса (попытка входа)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"🔐 Попытка входа: {username}")

        # Аутентифицируем пользователя
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Проверяем, активен ли пользователь
            if user.is_active:
                # Выполняем вход
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                print(f"✅ Успешный вход: {username} (staff: {user.is_staff}, superuser: {user.is_superuser})")

                # ВАЖНО: Проверяем, не пытается ли пользователь зайти в админку
                next_url = request.POST.get('next', '')

                # Если обычный пользователь пытается зайти в админку, игнорируем next
                if not user.is_staff and ('/admin/' in next_url or next_url == '/admin/login/'):
                    print(f"⚠️  Обычный пользователь {username} пытается зайти в админку, перенаправляем на главную")
                    return redirect('home')

                # Если есть next URL и он валидный, используем его
                if next_url and next_url != '' and not next_url.startswith('/admin/'):
                    return redirect(next_url)

                # Иначе на главную
                return redirect('home')
            else:
                messages.error(request, 'Ваш аккаунт деактивирован.')
                print(f"❌ Аккаунт {username} не активен")
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
            print(f"❌ Ошибка аутентификации для {username}")

    # Получаем URL для перенаправления после входа
    next_url = request.GET.get('next', '')

    # Убираем редиректы на админку для не-стафф пользователей
    if '/admin/' in next_url:
        print(f"⚠️  Запрос на вход в админку: {next_url}")

    return render(request, 'store/login.html', {
        'next': next_url,
        'cart_count': len(get_cart(request))
    })


def custom_logout(request):
    """Кастомный выход из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home')


# ==================== ОСНОВНЫЕ ПРЕДСТАВЛЕНИЯ ====================

def home(request):
    """Главная страница"""
    # Получаем несколько игр для отображения на главной
    featured_games = Game.objects.filter(quantity__gt=0)[:6]
    genres = Genre.objects.all()[:8]

    return render(request, 'store/home.html', {
        'featured_games': featured_games,
        'genres': genres,
        'cart_count': len(get_cart(request)),
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

    return render(request, 'store/game_list.html', {
        'games': games,
        'genres': genres,
        'tags': tags,
        'cart_count': len(get_cart(request)),
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

    # Получаем отзывы для этой игры
    reviews = Review.objects.filter(game=game, is_approved=True).order_by('-created_at')

    # Проверяем, может ли пользователь оставить отзыв
    can_review = False
    user_review = None

    if request.user.is_authenticated:
        # ВРЕМЕННО: разрешаем всем авторизованным оставлять отзывы для теста
        # В реальном магазине раскомментируйте проверку через has_purchased
        can_review = True  # Всем можно

        # Реальная проверка покупки (закомментирована для теста)
        # has_purchased = OrderItem.objects.filter(
        #     order__customer__user=request.user,
        #     order__status='completed',
        #     game=game
        # ).exists()
        # can_review = has_purchased

        # Получаем отзыв пользователя, если есть
        user_review = Review.objects.filter(game=game, user=request.user).first()

    return render(request, 'store/game_detail.html', {
        'game': game,
        'in_cart': in_cart,
        'cart_count': len(cart),
        'reviews': reviews,
        'can_review': can_review,
        'user_review': user_review,
        'average_rating': game.average_rating(),
        'review_count': game.review_count(),
    })


@login_required
def add_review(request, game_id):
    """Добавление отзыва к игре"""
    game = get_object_or_404(Game, id=game_id)

    # ВРЕМЕННО: пропускаем проверку покупки для теста
    # has_purchased = OrderItem.objects.filter(
    #     order__customer__user=request.user,
    #     order__status='completed',
    #     game=game
    # ).exists()

    # if not has_purchased:
    #     messages.error(request, 'Вы можете оставить отзыв только на купленные игры.')
    #     return redirect('game_detail', game_id=game_id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if not rating or not comment:
            messages.error(request, 'Пожалуйста, заполните все поля.')
            return redirect('game_detail', game_id=game_id)

        try:
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                raise ValueError
        except ValueError:
            messages.error(request, 'Рейтинг должен быть от 1 до 5.')
            return redirect('game_detail', game_id=game_id)

        # Создаем или обновляем отзыв
        Review.objects.update_or_create(
            game=game,
            user=request.user,
            defaults={
                'rating': rating_int,
                'comment': comment.strip(),
                'is_approved': True  # Автоматически одобряем
            }
        )

        messages.success(request, 'Спасибо за ваш отзыв!')

    return redirect('game_detail', game_id=game_id)


@login_required
def delete_review(request, review_id):
    """Удаление отзыва"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    game_id = review.game.id
    review.delete()
    messages.success(request, 'Отзыв удален.')
    return redirect('game_detail', game_id=game_id)


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
    """Оформление заказа (только для авторизованных пользователей)"""
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
                total_amount=0,
                payment_method='none',
                payment_status='pending'
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

            # Перенаправляем на страницу оплаты
            messages.success(request, f'Заказ #{order.id} создан! Перейдите к оплате.')
            return redirect('payment', order_id=order.id)

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


# ==================== ПЛАТЕЖНАЯ СИСТЕМА ====================

@login_required
def payment_view(request, order_id):
    """Страница оплаты заказа"""
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)

    if order.status != 'pending':
        messages.error(request, 'Этот заказ уже обработан.')
        return redirect('order_history')

    # Генерируем уникальный код оплаты, если его нет
    if not order.payment_code:
        order.payment_code = str(uuid.uuid4())[:8].upper()
        order.save()

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', '')

        if payment_method == 'card':
            # Эмуляция успешной оплаты картой
            order.status = 'processing'
            order.payment_method = 'card'
            order.payment_status = 'completed'
            order.save()

            # Отправляем email подтверждения
            send_order_confirmation_email(request.user, order)

            messages.success(request, f'✅ Оплата заказа #{order.id} прошла успешно! На почту отправлено подтверждение.')
            return redirect('order_success', order_id=order.id)

        elif payment_method == 'email':
            # Оплата по email (подтверждение через почту)
            order.payment_method = 'email'
            order.payment_status = 'pending'
            order.save()

            # Отправляем ссылку для подтверждения оплаты на email
            send_payment_link_email(request.user, order)

            messages.success(request, f'📧 На вашу почту отправлена ссылка для подтверждения оплаты.')
            return redirect('payment_pending', order_id=order.id)

        else:
            messages.error(request, 'Выберите способ оплаты.')

    return render(request, 'store/payment.html', {
        'order': order,
        'cart_count': len(get_cart(request)),
    })


@login_required
def confirm_payment_view(request, order_id, payment_code):
    """Подтверждение оплаты по ссылке из email"""
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)

    if order.payment_code != payment_code:
        messages.error(request, 'Неверный код подтверждения.')
        return redirect('home')

    if order.payment_status == 'completed':
        messages.info(request, 'Этот заказ уже оплачен.')
        return redirect('order_success', order_id=order.id)

    # Подтверждаем оплату
    order.status = 'processing'
    order.payment_status = 'completed'
    order.save()

    # Отправляем подтверждение
    send_order_confirmation_email(request.user, order)

    messages.success(request, f'✅ Оплата заказа #{order.id} подтверждена!')
    return redirect('order_success', order_id=order.id)


@login_required
def order_success_view(request, order_id):
    """Страница успешной оплаты"""
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    return render(request, 'store/order_success.html', {
        'order': order,
        'cart_count': len(get_cart(request)),
    })


@login_required
def payment_pending_view(request, order_id):
    """Страница ожидания подтверждения оплаты"""
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    return render(request, 'store/payment_pending.html', {
        'order': order,
        'cart_count': len(get_cart(request)),
    })


@login_required
def order_history_view(request):
    """История заказов пользователя"""
    customer = get_object_or_404(Customer, user=request.user)
    orders = Order.objects.filter(customer=customer).order_by('-created_at')

    return render(request, 'store/order_history.html', {
        'orders': orders,
        'cart_count': len(get_cart(request)),
    })


# ==================== EMAIL ФУНКЦИИ ====================

def send_order_confirmation_email(user, order):
    """Отправка email с подтверждением заказа"""
    subject = f'Game Store - Подтверждение заказа #{order.id}'

    message = f"""
    🎉 Спасибо за покупку в Game Store!

    Детали вашего заказа:
    --------------------------
    Номер заказа: #{order.id}
    Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}
    Общая сумма: {order.total_amount} руб.
    Статус: {order.get_status_display()}

    Товары в заказе:
    --------------------------
    """

    for item in order.orderitem_set.all():
        message += f"- {item.game.title} x {item.quantity} = {item.price * item.quantity} руб.\n"

    message += f"""
    --------------------------
    Итого: {order.total_amount} руб.

    Статус вашего заказа вы можете отслеживать в личном кабинете.

    Спасибо, что выбрали Game Store!

    С уважением,
    Команда Game Store
    📧 support@gamestore.com
    🌐 http://127.0.0.1:8000
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_payment_link_email(user, order):
    """Отправка ссылки для подтверждения оплаты по email"""
    payment_url = f"http://127.0.0.1:8000/confirm-payment/{order.id}/{order.payment_code}/"

    subject = f'Game Store - Подтверждение оплаты заказа #{order.id}'

    message = f"""
    🔐 Подтвердите оплату заказа #{order.id}

    Для завершения оплаты перейдите по ссылке:
    {payment_url}

    Или введите код подтверждения на сайте:
    Код: {order.payment_code}

    Детали заказа:
    --------------------------
    Сумма: {order.total_amount} руб.
    Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}

    Ссылка действительна 24 часа.

    Если вы не совершали эту покупку, проигнорируйте это письмо.

    С уважением,
    Команда Game Store
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


# ==================== ОТЧЕТЫ (только для менеджеров) ====================

@user_passes_test(is_manager)
def reports(request):
    """Страница отчетов (доступна только менеджерам)"""
    return render(request, 'store/reports.html', {
        'cart_count': len(get_cart(request)),
    })


@user_passes_test(is_manager)
def top_games_report(request):
    """Отчет по 10 самым продаваемым играм (только для менеджеров)"""
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
    """Отчет по продажам за неделю (только для менеджеров)"""
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