from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentAPI,
    TransactionAPI,
    RefundAPI, 
    UserAdminAPI, 
    RegisterAPI, 
    TransactionAdminAPI, 
    PaymentAdminAPI,
    WalletDepositAPI
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)



router = DefaultRouter()
router.register("payments", PaymentAPI, basename="payment")
router.register("transactions", TransactionAPI, basename="transaction")
router.register("admin/users", UserAdminAPI, basename="admin-user")
router.register("admin/payments", PaymentAdminAPI, basename="admin-payment")
router.register("admin/transactions", TransactionAdminAPI, basename="admin-transaction")

urlpatterns = [
    path("login/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("login/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterAPI.as_view(), name="register"),
    path("payments/<int:payment_id>/refund/", RefundAPI.as_view(), name="payment-refund"),
    path("wallet/deposit/", WalletDepositAPI.as_view(), name="wallet-deposit"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

urlpatterns += router.urls
