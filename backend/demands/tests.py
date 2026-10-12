
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, UserRole
from demands.models import DeliveryDemand
from masterdata.models import CargoCategory, Outlet, Supplier


User = get_user_model()


class DeliveryDemandAPITests(APITestCase):
    def setUp(self):
        # Tạo người dùng kiểm thử.
        self.coordinator = User.objects.create_user(
            username="test_coordinator",
            password="test-password-only-for-tests",
        )
        self.purchasing_user = User.objects.create_user(
            username="test_purchasing",
            password="test-password-only-for-tests",
        )
        self.no_role_user = User.objects.create_user(
            username="test_no_role",
            password="test-password-only-for-tests",
        )

        # Tạo vai trò nghiệp vụ.
        self.coordinator_role = Role.objects.create(
            role_code="LOGISTICS_COORDINATOR",
            role_name="Logistics Coordinator",
            is_active=True,
        )
        self.purchasing_role = Role.objects.create(
            role_code="PURCHASING_STAFF",
            role_name="Purchasing Staff",
            is_active=True,
        )

        UserRole.objects.create(
            user=self.coordinator,
            role=self.coordinator_role,
        )
        UserRole.objects.create(
            user=self.purchasing_user,
            role=self.purchasing_role,
        )

        # Tạo master data tối thiểu cần thiết.
        self.supplier = Supplier.objects.create(
            supplier_code="TEST-SUP-001",
            supplier_name="Test Supplier",
        )
        self.outlet = Outlet.objects.create(
            outlet_code="TEST-OUT-001",
            outlet_name="Test Outlet",
            address="Test address",
        )
        self.category = CargoCategory.objects.create(
            category_code="TEST-CAT-001",
            category_name="Test Cargo",
        )

        self.list_url = reverse("demands:demand-list-create")

        self.valid_payload = {
            "demand_code": "TEST-DEM-001",
            "supplier": self.supplier.pk,
            "outlet": self.outlet.pk,
            "cargo_category": self.category.pk,
            "quantity_kg": "125.000",
            "requested_date": (
                date.today() + timedelta(days=2)
            ).isoformat(),
            "requested_start_time": "09:00:00",
            "requested_end_time": "10:00:00",
            "notes": "API test",
        }

    def create_demand(self, demand_code, created_by, demand_status):
        return DeliveryDemand.objects.create(
            demand_code=demand_code,
            supplier=self.supplier,
            outlet=self.outlet,
            cargo_category=self.category,
            quantity_kg=Decimal("100.000"),
            requested_date=date.today() + timedelta(days=2),
            requested_start_time=time(9, 0),
            requested_end_time=time(10, 0),
            status=demand_status,
            created_by=created_by,
        )

    def test_coordinator_can_list_demands(self):
        self.client.force_authenticate(user=self.coordinator)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_coordinator_cannot_create_demand(self):
        self.client.force_authenticate(user=self.coordinator)

        response = self.client.post(
            self.list_url,
            self.valid_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertFalse(
            DeliveryDemand.objects.filter(
                demand_code="TEST-DEM-001"
            ).exists()
        )

    def test_purchasing_staff_can_create_demand(self):
        self.client.force_authenticate(user=self.purchasing_user)

        response = self.client.post(
            self.list_url,
            self.valid_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        demand = DeliveryDemand.objects.get(
            demand_code="TEST-DEM-001"
        )
        self.assertEqual(demand.created_by, self.purchasing_user)

    def test_client_cannot_override_created_by(self):
        self.client.force_authenticate(user=self.purchasing_user)

        payload = {
            **self.valid_payload,
            "created_by": self.coordinator.pk,
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        demand = DeliveryDemand.objects.get(
            demand_code="TEST-DEM-001"
        )
        self.assertEqual(demand.created_by, self.purchasing_user)

    def test_unauthenticated_user_cannot_list_demands(self):
        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_coordinator_cannot_patch_demand(self):
        demand = self.create_demand(
            demand_code="TEST-DEM-002",
            created_by=self.purchasing_user,
            demand_status=DeliveryDemand.Status.DRAFT,
        )
        self.client.force_authenticate(user=self.coordinator)

        response = self.client.patch(
            reverse("demands:demand-detail", kwargs={"pk": demand.pk}),
            {"notes": "Attempted unauthorized update"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        demand.refresh_from_db()
        self.assertNotEqual(
            demand.notes,
            "Attempted unauthorized update",
        )

    def test_cancelled_demand_cannot_be_patched(self):
        demand = self.create_demand(
            demand_code="TEST-DEM-003",
            created_by=self.purchasing_user,
            demand_status=DeliveryDemand.Status.CANCELLED,
        )
        self.client.force_authenticate(user=self.purchasing_user)

        response = self.client.patch(
            reverse("demands:demand-detail", kwargs={"pk": demand.pk}),
            {"notes": "Should not be saved"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        demand.refresh_from_db()
        self.assertNotEqual(demand.notes, "Should not be saved")
