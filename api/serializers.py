from rest_framework import serializers
from .models import Payment, Wallet, Transaction, Refund
from django.contrib.auth.models import User



class PaymentReadSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', read_only='True')
    class Meta:
        model = Payment
        fields = '__all__'

class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "amount",
            "description",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )

        return value



class WalletReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = "__all__"



class TransactionReadSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', read_only='True')
    payment = serializers.SlugRelatedField(slug_field='tracking_code', read_only='True')
    class Meta:
        model = Transaction
        fields = "__all__"



class RefundReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = "__all__"

class RefundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            "amount",
            "reason",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )

        return value



class RegisterSerializer(serializers.ModelSerializer): 
    password2 = serializers.CharField(write_only=True)

    class Meta: 
        model = User 
        fields = ( 
            "username", 
            "first_name", 
            "last_name", 
            "email", 
            "password", 
            "password2"
        ) 
        extra_kwargs = { 
            "password": { 
                "write_only": True, 
            },
            "first_name": { 
                "required": True, 
            },
            "last_name": { 
                "required": True, 
            },
            "email": { 
                "required": True, 
            }
        }

    def validate_username(self, value): 
        if User.objects.filter(username=value).exists(): 
            raise serializers.ValidationError("A user with this username already exists.") 

        return value 

    def validate_email(self, value): 
        if User.objects.filter(email=value).exists(): 
            raise serializers.ValidationError("A user with this email already exists.") 

        return value
         
    def validate(self, attrs): 
        if attrs["password"] != attrs["password2"]: 
            raise serializers.ValidationError("Passwords do not match.") 

        attrs.pop("password2")

        return attrs 



class UserAdminReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = fields
