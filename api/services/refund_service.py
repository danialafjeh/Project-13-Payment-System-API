from django.db import models, transaction
from rest_framework.exceptions import ValidationError
from api.models import Payment, Refund, Transaction
from .payment_gateway import MockPaymentGateway
from .wallet_service import WalletService


class RefundService:
    @staticmethod
    @transaction.atomic
    def create_refund(*, payment, amount, reason=""):
        payment = Payment.objects.select_for_update().get(pk=payment.pk)

        if payment.status != "success":
            raise ValidationError("Only successful payments can be refunded.")

        refunded_amount = payment.refunds.filter(status="success").aggregate(total=models.Sum("amount"))["total"] or 0

        if refunded_amount + amount > payment.amount:
            raise ValidationError("Refund amount exceeds the remaining payment amount.")

        refund = Refund.objects.create(
            payment=payment,
            amount=amount,
            reason=reason,
            status="processing",
        )

        transaction_record = Transaction.objects.create(
            user=payment.user,
            payment=payment,
            amount=amount,
            transaction_type="refund",
        )

        success = MockPaymentGateway.process_refund(refund)

        if success:
            wallet = WalletService.get_locked_wallet(user=payment.user)
            WalletService.increase_balance(wallet=wallet, amount=amount)
            refund.status = "success"
            transaction_record.status = "completed"

            refund.save(update_fields=["status", "updated_at"])
            transaction_record.save( update_fields=["status"])

            if refunded_amount + amount == payment.amount:
                payment.status = "refunded"
                payment.save(update_fields=["status", "updated_at"])

        else:
            refund.status = "failed"
            transaction_record.status = "failed"

            refund.save(update_fields=["status", "updated_at"])
            transaction_record.save(update_fields=["status"])

        return refund