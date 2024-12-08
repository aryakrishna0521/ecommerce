"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from store import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/',views.SignUpView.as_view(),name='register'),
    path('verify/otp/',views.VerifyEmailView.as_view(),name='verify-email'),
    path('login/',views.SignInView.as_view(),name='signin'),
    path('index/',views.ProductListView.as_view(),name='product-list'),
    path('products/<int:pk>/',views.ProductDetailView.as_view(),name='product-detail'),
    path('products/<int:pk>/cart/add',views.AddToCartView.as_view(),name="addtocart"),
    path('cart/summary/',views.CartSummaryView.as_view(),name="cart-summary"),
    path('cart/<int:pk>/remove/',views.BasketItemDeleteview.as_view(),name="delete"),
    path('order/',views.PlaceOrderView.as_view(),name="place-order"),
    path('order/summary/',views.OrderSummaryView.as_view(),name="order-summary"),
    path('payment/verify/',views.PaymentVerificationView.as_view(),name="payment-verify"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
