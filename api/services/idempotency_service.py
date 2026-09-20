from django.core.cache import cache



class IdempotencyService:
    @staticmethod
    def get_payment_key(user, idempotency_key):
        return f"idempotency:payment:{user.id}:{idempotency_key}"

    @staticmethod
    def get_refund_key(user, idempotency_key):
        return f"idempotency:refund:{user.id}:{idempotency_key}"

    @staticmethod
    def get_deposit_key(user, idempotency_key):
        return f"idempotency:deposit:{user.id}:{idempotency_key}"
    
    @staticmethod
    def claim(key, value="processing", timeout=86400):
        return cache.add(key,value,timeout)

    @staticmethod
    def get(key):
        return cache.get(key)

    @staticmethod
    def set(key, value, timeout=86400):
        return cache.set(key, value, timeout)
    