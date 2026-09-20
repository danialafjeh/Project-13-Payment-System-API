from rest_framework import status, viewsets, filters
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from .models import Payment, Transaction, Wallet
from django.contrib.auth.models import User
from .services.payment_service import PaymentService
from .services.idempotency_service import IdempotencyService
from .services.refund_service import RefundService
from .services.wallet_service import WalletService
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from .serializers import (
    PaymentCreateSerializer,
    PaymentReadSerializer,
    TransactionReadSerializer,
    RefundCreateSerializer,
    RefundReadSerializer,
    UserAdminReadSerializer,
    RegisterSerializer
)

# Create your views here.

class PaymentAPI(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get","post"]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        else:
           return PaymentReadSerializer

    #def perform_create(self, serializer):
        #PaymentService.create_payment(
        #user=self.request.user,
        #amount=serializer.validated_data["amount"],
        #description=serializer.validated_data.get("description", ""),
        #)
    
    def create(self, request, *args, **kwargs):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response({"detail": "Idempotency-Key header is required."}, status=status.HTTP_400_BAD_REQUEST)

        key = IdempotencyService.get_payment_key(request.user, idempotency_key)
        claimed = IdempotencyService.claim(key)

        if not claimed:
            existing = IdempotencyService.get(key)
            if existing == "processing":
               return Response({"detail": "Request is already being processed."}, status=status.HTTP_409_CONFLICT)

            return Response(
                {
                    "detail": "This Idempotency-Key has already been used. A new request cannot be created with the same key.",
                    "previous_payment": existing,
                }, 
                status=status.HTTP_200_OK
            )

        try:
            payment = PaymentService.create_payment(
                user=request.user,
                amount=serializer.validated_data["amount"],
                description=serializer.validated_data.get("description", ""),
            )
        except ValidationError as exc:
            error_data = {
                "status": "failed",
                "detail": exc.detail,
            }
            IdempotencyService.set(key, error_data)
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            error_data = {
                "status": "failed",
                "detail": "An unexpected error occurred.",
            }
            IdempotencyService.set(key, error_data)
            return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response_data = PaymentReadSerializer(payment).data
        IdempotencyService.set(key, response_data)

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="process")
    def process(self, request, pk=None):
        payment = self.get_object()
        payment = PaymentService.process_payment(payment=payment)
        return Response(PaymentReadSerializer(payment).data)



class TransactionAPI(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    serializer_class = TransactionReadSerializer



class RefundAPI(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=RefundCreateSerializer, responses=RefundReadSerializer)
    def post(self, request, payment_id):
        payment = Payment.objects.filter(id=payment_id, user=request.user).first()

        if not payment:
            return Response({"detail": "Payment not found."},status=status.HTTP_404_NOT_FOUND)

        serializer = RefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response({"detail": "Idempotency-Key header is required."}, status=status.HTTP_400_BAD_REQUEST)

        key = IdempotencyService.get_refund_key(request.user, idempotency_key)
        claimed = IdempotencyService.claim(key)

        if not claimed:
            existing = IdempotencyService.get(key)
            if existing == "processing":
                return Response({"detail": "Request is already being processed."}, status=status.HTTP_409_CONFLICT)
        
            return Response(
                {
                    "detail": "This Idempotency-Key has already been used. A new request cannot be created with the same key.",
                    "previous_refund": existing,
                }, 
                status=status.HTTP_200_OK
            )

        try:
            refund = RefundService.create_refund(
               payment=payment,
               amount=serializer.validated_data["amount"],
               reason=serializer.validated_data.get("reason", ""),
            )
        except ValidationError as exc:
           error_data = {
               "status": "failed",
               "detail": exc.detail,
           }
           IdempotencyService.set(key, error_data)
           return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
           error_data = {
               "status": "failed",
               "detail": "An unexpected error occurred.",
            }
           IdempotencyService.set(key, error_data)
           return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = RefundReadSerializer(refund).data
        IdempotencyService.set(key, response_data)

        return Response(response_data, status=status.HTTP_201_CREATED)



class WalletDepositAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response(
                {
                    "detail": "Idempotency-Key header is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        key = IdempotencyService.get_deposit_key(request.user,idempotency_key)

        claimed = IdempotencyService.claim(key)

        if not claimed:
            existing = IdempotencyService.get(key)

            if existing == "processing":
                return Response(
                    {
                        "detail": "Request is already being processed."
                    },
                    status=status.HTTP_409_CONFLICT
                )

            return Response(
                {
                    "detail": "This Idempotency-Key has already been used.",
                    "previous_transaction": existing,
                },
                status=status.HTTP_409_CONFLICT
            )

        try:
            transaction_record = WalletService.deposit(
                user=request.user,
                amount=serializer.validated_data["amount"],
            )
        except Exception:
            error_data = {
                "status": "failed",
                "detail": "An unexpected error occurred.",
            }

            IdempotencyService.set(key, error_data)
            return Response(error_data,status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = TransactionReadSerializer(transaction_record).data
        IdempotencyService.set(key, response_data)

        return Response(response_data, status=status.HTTP_201_CREATED)


    
class RegisterAPI(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.create_user(**serializer.validated_data)
        Wallet.objects.create(user=user)

        return Response(
            {
                "detail": "User registered successfully.",
                "username": user.username,
            },
            status=status.HTTP_201_CREATED,
        )



class UserAdminAPI(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = UserAdminReadSerializer
    queryset = User.objects.all()

    filter_backends = [filters.SearchFilter]
    search_fields = ["username"]



class PaymentAdminAPI(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = PaymentReadSerializer
    queryset = Payment.objects.all()

    filter_backends = [filters.SearchFilter]
    search_fields = ["user__username"]



class TransactionAdminAPI(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = TransactionReadSerializer
    queryset = Transaction.objects.all()

    filter_backends = [filters.SearchFilter]
    search_fields = ["user__username"]