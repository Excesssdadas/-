from django.contrib import admin
from .models import Genre, Tag, Game, Customer, Order, OrderItem, Review


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'genre', 'price', 'quantity', 'average_rating_display']
    list_filter = ['genre', 'tags', 'created_at']
    search_fields = ['title', 'description']
    filter_horizontal = ['tags']

    def average_rating_display(self, obj):
        return f"{obj.average_rating()}/5"

    average_rating_display.short_description = 'Средний рейтинг'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone']
    search_fields = ['user__username', 'phone']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'payment_status', 'payment_method', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at', 'payment_method']
    search_fields = ['customer__user__username', 'id']
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['game', 'user', 'rating', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'rating', 'created_at']
    search_fields = ['game__title', 'user__username', 'comment']
    list_editable = ['is_approved']
    readonly_fields = ['created_at']

    def get_stars_display(self, obj):
        return obj.get_stars_display()

    get_stars_display.short_description = 'Рейтинг'
    get_stars_display.allow_tags = True