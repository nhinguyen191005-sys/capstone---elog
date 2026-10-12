
from rest_framework import serializers

from .models import (
    CargoCategory,
    Hub,
    Outlet,
    Supplier,
    VehicleType,
)


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "supplier_code",
            "supplier_name",
            "contact_name",
            "phone",
            "email",
            "address",
            "is_active",
        ]


class OutletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = [
            "id",
            "outlet_code",
            "outlet_name",
            "address",
            "contact_name",
            "phone",
            "is_active",
        ]


class CargoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoCategory
        fields = [
            "id",
            "category_code",
            "category_name",
            "description",
            "is_active",
        ]


class HubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hub
        fields = [
            "id",
            "hub_code",
            "hub_name",
            "address",
            "is_active",
        ]


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = [
            "id",
            "vehicle_code",
            "vehicle_name",
            "capacity_kg",
            "description",
            "is_active",
        ]
