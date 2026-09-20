

class MockPaymentGateway:
    @staticmethod
    def process_payment(payment):
        return True

    @staticmethod
    def process_refund(refund):
        return True

    @staticmethod
    def process_deposit(amount):
        return True
    