from django.db import transaction
from rest_framework.exceptions import ValidationError
from api.models import Wallet, Transaction
from .payment_gateway import MockPaymentGateway


class WalletService:
    @staticmethod
    def get_locked_wallet(*, user):
        return Wallet.objects.select_for_update().get(user=user)

    @staticmethod
    @transaction.atomic
    def decrease_balance(*, wallet, amount):
        wallet.balance -= amount
        wallet.save(update_fields=["balance", "updated_at"])
        return wallet

    @staticmethod
    @transaction.atomic
    def increase_balance(*, wallet, amount):
        wallet.balance += amount
        wallet.save(update_fields=["balance", "updated_at"])
        return wallet

    @staticmethod
    @transaction.atomic
    def deposit(*, user, amount):
        wallet = WalletService.get_locked_wallet(user=user)

        transaction_record = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type="deposit"
        )

        success = MockPaymentGateway.process_deposit(amount)

        if not success:
            transaction_record.status = "failed"
            transaction_record.save(update_fields=["status"])
            return transaction_record

        WalletService.increase_balance(wallet=wallet, amount=amount)

        transaction_record.status = "completed"
        transaction_record.save(update_fields=["status"])

        return transaction_record