from django.db import transaction
from api.models import Payment, Transaction
from .payment_gateway import MockPaymentGateway
from .wallet_service import WalletService
from rest_framework.exceptions import ValidationError



class PaymentService:
    @staticmethod
    @transaction.atomic
    def create_payment(*, user, amount, description=""):
        payment = Payment.objects.create(
            user=user,
            amount=amount,
            description=description,
        )

        Transaction.objects.create(
            user=user,
            payment=payment,
            amount=amount,
            transaction_type="payment",
        )

        return payment

    @staticmethod
    @transaction.atomic
    def process_payment(*, payment):
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.status != "pending":
            raise ValidationError("Only pending payments can be processed.")

        wallet = WalletService.get_locked_wallet(user=payment.user)

        if wallet.balance < payment.amount:
           raise ValidationError("Insufficient wallet balance.")
        
        payment.status = "processing"
        payment.save(update_fields=["status", "updated_at"])

        success = MockPaymentGateway.process_payment(payment)

        transaction_record = payment.transactions.get(transaction_type="payment")

        if success:
            WalletService.decrease_balance(wallet=wallet,amount=payment.amount)
            payment.status = "success"
            transaction_record.status = "completed"
        else:
            payment.status = "failed"
            transaction_record.status = "failed"

        payment.save(update_fields=["status", "updated_at"])
        transaction_record.save(update_fields=["status"])

        return payment
    