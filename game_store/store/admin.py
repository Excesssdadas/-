from django.contrib import admin
from .models import Genre, Tag, Game, Customer, Order, OrderItem

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
    list_display = ['title', 'genre', 'price', 'quantity']
    list_filter = ['genre', 'tags', 'created_at']
    search_fields = ['title', 'description']
    filter_horizontal = ['tags']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone']
    search_fields = ['user__username', 'phone']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]