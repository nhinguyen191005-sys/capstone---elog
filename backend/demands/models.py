
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal


class DeliveryDemand(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        PLANNING = "PLANNING", "Planning"
        PLANNED = "PLANNED", "Planned"
        CANCELLED = "CANCELLED", "Cancelled"

    demand_code = models.CharField(max_length=30, unique=True)

    supplier = models.ForeignKey(
        "masterdata.Supplier",
        on_delete=models.PROTECT,
        related_name="delivery_demands",
    )
    outlet = models.ForeignKey(
        "masterdata.Outlet",
        on_delete=models.PROTECT,
        related_name="delivery_demands",
    )
    cargo_category = models.ForeignKey(
        "masterdata.CargoCategory",
        on_delete=models.PROTECT,
        related_name="delivery_demands",
    )

    quantity_kg = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )

    requested_date = models.DateField()
    requested_start_time = models.TimeField()
    requested_end_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    notes = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_delivery_demands",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "delivery_demands"
        ordering = ["-created_at", "demand_code"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_kg__gt=0),
                name="ck_delivery_demand_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    requested_end_time__gt=models.F("requested_start_time")
                ),
                name="ck_delivery_demand_time_order",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "DRAFT",
                        "SUBMITTED",
                        "PLANNING",
                        "PLANNED",
                        "CANCELLED",
                    ]
                ),
                name="ck_delivery_demand_status_valid",
            ),
        ]

    def __str__(self):
        return self.demand_code
