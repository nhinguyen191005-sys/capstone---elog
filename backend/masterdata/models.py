import json
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Supplier(models.Model):
    supplier_code = models.CharField(max_length=30, unique=True)
    supplier_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suppliers"
        ordering = ["supplier_code"]

    def __str__(self):
        return f"{self.supplier_code} - {self.supplier_name}"


class Outlet(models.Model):
    outlet_code = models.CharField(max_length=30, unique=True)
    outlet_name = models.CharField(max_length=200)
    address = models.TextField()
    contact_name = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "outlets"
        ordering = ["outlet_code"]

    def __str__(self):
        return f"{self.outlet_code} - {self.outlet_name}"


class Hub(models.Model):
    hub_code = models.CharField(max_length=30, unique=True)
    hub_name = models.CharField(max_length=150)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hubs"
        ordering = ["hub_code"]

    def __str__(self):
        return f"{self.hub_code} - {self.hub_name}"


class CargoCategory(models.Model):
    category_code = models.CharField(max_length=30, unique=True)
    category_name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cargo_categories"
        ordering = ["category_code"]

    def __str__(self):
        return f"{self.category_code} - {self.category_name}"


class VehicleType(models.Model):
    vehicle_code = models.CharField(max_length=30, unique=True)
    vehicle_name = models.CharField(max_length=100)
    capacity_kg = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))]
    )
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "vehicle_types"
        ordering = ["vehicle_code"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity_kg__gt=0),
                name="ck_vehicle_capacity_positive",
            ),
        ]

    def __str__(self):
        return f"{self.vehicle_code} - {self.vehicle_name}"


class RuleSet(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        RETIRED = "RETIRED", "Retired"

    rule_set_code = models.CharField(max_length=40)
    rule_set_name = models.CharField(max_length=150)
    version_no = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    effective_from = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_rule_sets",
    )

    class Meta:
        db_table = "rule_sets"
        ordering = ["rule_set_code", "version_no"]

        constraints = [
            models.UniqueConstraint(
                fields=["rule_set_code", "version_no"],
                name="uq_rule_set_code_version",
            ),
            models.CheckConstraint(
                condition=models.Q(version_no__gte=1),
                name="ck_rule_set_version_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=["DRAFT", "ACTIVE", "RETIRED"]
                ),
                name="ck_rule_set_status_valid",
            ),
        ]


    def __str__(self):
        return f"{self.rule_set_code} v{self.version_no}"


class BusinessRule(models.Model):
    class ModuleCode(models.TextChoices):
        F1 = "F1", "F1 - Candidate Generation"
        F2 = "F2", "F2 - Consolidation"
        F3 = "F3", "F3 - Capacity and Waves"
        F4 = "F4", "F4 - Receiving Validation"
        F5 = "F5", "F5 - Economic Evaluation"

    rule_set = models.ForeignKey(
        RuleSet,
        on_delete=models.PROTECT,
        related_name="business_rules",
    )
    rule_code = models.CharField(max_length=50)
    module_code = models.CharField(
        max_length=5,
        choices=ModuleCode.choices,
    )
    rule_name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    rule_definition = models.JSONField()
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "business_rules"
        ordering = ["module_code", "priority", "rule_code"]

        constraints = [
            models.UniqueConstraint(
                fields=["rule_set", "rule_code"],
                name="uq_business_rule_set_code",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    module_code__in=["F1", "F2", "F3", "F4", "F5"]
                ),
                name="ck_business_rule_module_valid",
            ),
        ]


    def __str__(self):
        return f"{self.rule_set.rule_set_code} - {self.rule_code}"


class PlanningParameter(models.Model):
    parameter_key = models.CharField(max_length=100, unique=True)
    parameter_value = models.JSONField()
    data_type = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_planning_parameters",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "planning_parameters"
        ordering = ["parameter_key"]

    def __str__(self):
        return self.parameter_key


class CostProfile(models.Model):
    profile_code = models.CharField(max_length=40, unique=True)
    profile_name = models.CharField(max_length=150)
    currency_code = models.CharField(max_length=3, default="VND")
    fixed_transport_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    cost_per_km = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    additional_handling_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cost_profiles"
        ordering = ["profile_code"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fixed_transport_cost__gte=0),
                name="ck_cost_profile_fixed_nonnegative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(cost_per_km__isnull=True)
                    | models.Q(cost_per_km__gte=0)
                ),
                name="ck_cost_profile_km_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(additional_handling_cost__gte=0),
                name="ck_cost_profile_handling_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.profile_code} - {self.profile_name}"
