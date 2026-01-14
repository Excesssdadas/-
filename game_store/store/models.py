from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Genre(models.Model):
    """Модель для жанров игр (Шутер, Стратегия, РПГ и т.д.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название жанра")
    description = models.TextField(blank=True, verbose_name="Описание жанра")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"


class Tag(models.Model):
    """Модель для тегов (Стелс, Новелла, Соус-лайк и т.д.)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Game(models.Model):
    """Модель для товаров (игр)"""
    title = models.CharField(max_length=200, verbose_name="Название игры")
    description = models.TextField(verbose_name="Описание игры")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.IntegerField(validators=[MinValueValidator(0)], verbose_name="Количество на складе")
    image = models.ImageField(upload_to='games/images/', blank=True, null=True, verbose_name="Изображение")
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name="Жанр")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Игра"
        verbose_name_plural = "Игры"

    def average_rating(self):
        """Средний рейтинг игры"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            total = sum([review.rating for review in reviews])
            return round(total / reviews.count(), 1)
        return 0

    def review_count(self):
        """Количество отзывов"""
        return self.reviews.filter(is_approved=True).count()


class Customer(models.Model):
    """Модель для клиентов (расширяет стандартную модель пользователя)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    address = models.TextField(blank=True, verbose_name="Адрес")

    def __str__(self):
        return f"{self.user.username}"

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Order(models.Model):
    """Модель для заказов (покупок)"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    # НОВЫЕ КОНСТАНТЫ ДЛЯ ПЛАТЕЖЕЙ
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Банковская карта'),
        ('email', 'Оплата по email'),
        ('none', 'Не выбран'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('completed', 'Оплачено'),
        ('failed', 'Ошибка оплаты'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Клиент")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Общая сумма")

    # НОВЫЕ ПОЛЯ ДЛЯ ПЛАТЕЖНОЙ СИСТЕМЫ
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='none',
        verbose_name="Способ оплаты"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Статус оплаты"
    )
    payment_code = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        verbose_name="Код подтверждения"
    )

    def __str__(self):
        return f"Заказ #{self.id} - {self.customer}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    """Модель для элементов заказа (связь между заказом и играми)"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Заказ")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name="Игра")
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена на момент покупки")

    def __str__(self):
        return f"{self.game.title} x {self.quantity}"

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"


class Review(models.Model):
    """Модель для отзывов на игры"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='reviews', verbose_name="Игра")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    rating = models.IntegerField(
        choices=[(1, '1 звезда'), (2, '2 звезды'), (3, '3 звезды'), (4, '4 звезды'), (5, '5 звезд')],
        verbose_name="Рейтинг"
    )
    comment = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_approved = models.BooleanField(default=True, verbose_name="Одобрен")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        unique_together = ['game', 'user']  # один отзыв на игру от пользователя
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.game.title} ({self.rating}/5)"

    def get_stars_display(self):
        """Возвращает HTML для отображения звезд"""
        filled = '★' * self.rating
        empty = '☆' * (5 - self.rating)
        return f'<span style="color: gold; font-size: 1.2rem;">{filled}</span><span style="color: #ccc;">{empty}</span>'