from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # ==================== АУТЕНТИФИКАЦИЯ ====================
    path('site-login/', views.custom_login, name='site_login'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # ==================== ОСНОВНЫЕ СТРАНИЦЫ ====================
    path('', views.home, name='home'),
    path('games/', views.game_list, name='game_list'),
    path('games/<int:game_id>/', views.game_detail, name='game_detail'),

    # ==================== ОТЗЫВЫ ====================
    path('games/<int:game_id>/review/', views.add_review, name='add_review'),
    path('reviews/delete/<int:review_id>/', views.delete_review, name='delete_review'),

    # ==================== КОРЗИНА ====================
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:game_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),

    # ==================== ЗАКАЗЫ И ПЛАТЕЖИ ====================
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<int:order_id>/', views.payment_view, name='payment'),
    path('payment/pending/<int:order_id>/', views.payment_pending_view, name='payment_pending'),
    path('order/success/<int:order_id>/', views.order_success_view, name='order_success'),
    path('orders/history/', views.order_history_view, name='order_history'),
    path('confirm-payment/<int:order_id>/<str:payment_code>/',
         views.confirm_payment_view, name='confirm_payment'),

    # ==================== ОТЧЕТЫ ====================
    path('reports/', views.reports, name='reports'),
    path('reports/top-games/', views.top_games_report, name='top_games_report'),
    path('reports/weekly-sales/', views.weekly_sales_report, name='weekly_sales_report'),
]