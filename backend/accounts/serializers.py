
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        trim_whitespace=True,
    )
    password = serializers.CharField(
        required=True,
        trim_whitespace=False,
        write_only=True,
    )
