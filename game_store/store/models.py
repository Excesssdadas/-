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

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Клиент")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Общая сумма")

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
