
from django.utils import timezone
from rest_framework import serializers

from .models import DeliveryDemand


class DeliveryDemandSerializer(serializers.ModelSerializer):
    supplier_code = serializers.CharField(
        source="supplier.supplier_code",
        read_only=True,
    )
    outlet_code = serializers.CharField(
        source="outlet.outlet_code",
        read_only=True,
    )
    cargo_category_code = serializers.CharField(
        source="cargo_category.category_code",
        read_only=True,
    )
    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = DeliveryDemand
        fields = [
            "id",
            "demand_code",
            "supplier",
            "supplier_code",
            "outlet",
            "outlet_code",
            "cargo_category",
            "cargo_category_code",
            "quantity_kg",
            "requested_date",
            "requested_start_time",
            "requested_end_time",
            "status",
            "notes",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        start_time = attrs.get(
            "requested_start_time",
            getattr(self.instance, "requested_start_time", None),
        )
        end_time = attrs.get(
            "requested_end_time",
            getattr(self.instance, "requested_end_time", None),
        )

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({
                "requested_end_time": (
                    "Giờ kết thúc phải sau giờ bắt đầu."
                )
            })

        quantity = attrs.get(
            "quantity_kg",
            getattr(self.instance, "quantity_kg", None),
        )
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({
                "quantity_kg": "Khối lượng phải lớn hơn 0."
            })

        requested_date = attrs.get(
            "requested_date",
            getattr(self.instance, "requested_date", None),
        )
        if requested_date and requested_date < timezone.localdate():
            raise serializers.ValidationError({
                "requested_date": "Ngày giao hàng không được ở quá khứ."
            })

        return attrs
