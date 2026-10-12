
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, UserRole
from masterdata.models import (
    CargoCategory,
    Hub,
    Outlet,
    Supplier,
    VehicleType,
)

User = get_user_model()


class MasterDataAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="masterdata_test_user",
            password="test-password-only",
        )

        role = Role.objects.create(
            role_code="PURCHASING_STAFF",
            role_name="Purchasing Staff",
            is_active=True,
        )
        UserRole.objects.create(user=self.user, role=role)

        self.supplier = Supplier.objects.create(
            supplier_code="SUP-TEST",
            supplier_name="Test Supplier",
            is_active=True,
        )
        self.inactive_supplier = Supplier.objects.create(
            supplier_code="SUP-INACTIVE",
            supplier_name="Inactive Supplier",
            is_active=False,
        )

        self.outlet = Outlet.objects.create(
            outlet_code="OUT-TEST",
            outlet_name="Test Outlet",
            address="Test address",
            is_active=True,
        )
        self.category = CargoCategory.objects.create(
            category_code="CAT-TEST",
            category_name="Test Category",
            is_active=True,
        )
        self.hub = Hub.objects.create(
            hub_code="HUB-TEST",
            hub_name="Test Hub",
            address="Test address",
            is_active=True,
        )
        self.vehicle_type = VehicleType.objects.create(
            vehicle_code="VEH-TEST",
            vehicle_name="Test Vehicle",
            capacity_kg="1000.000",
            is_active=True,
        )

        self.endpoints = [
            reverse("masterdata:supplier-list"),
            reverse("masterdata:outlet-list"),
            reverse("masterdata:cargo-category-list"),
            reverse("masterdata:hub-list"),
            reverse("masterdata:vehicle-type-list"),
        ]

    def test_authenticated_user_with_role_can_access_all_lists(self):
        self.client.force_authenticate(user=self.user)

        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                )

    def test_unauthenticated_user_cannot_access_masterdata(self):
        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

    def test_supplier_list_excludes_inactive_records(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("masterdata:supplier-list")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        supplier_codes = [
            item["supplier_code"]
            for item in response.data
        ]
        self.assertIn("SUP-TEST", supplier_codes)
        self.assertNotIn("SUP-INACTIVE", supplier_codes)

    def test_masterdata_endpoints_are_read_only(self):
        self.client.force_authenticate(user=self.user)

        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.post(
                    endpoint,
                    {},
                    format="json",
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                )
