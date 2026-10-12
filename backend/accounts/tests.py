
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, APITestCase

from accounts.models import Role, UserRole
from accounts.permissions import HasCoLogiRole


User = get_user_model()


class HasCoLogiRoleTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = HasCoLogiRole()

        self.coordinator_role = Role.objects.create(
            role_code="LOGISTICS_COORDINATOR",
            role_name="Logistics Coordinator",
            is_active=True,
        )

        self.other_role = Role.objects.create(
            role_code="PURCHASING_STAFF",
            role_name="Purchasing Staff",
            is_active=True,
        )

        self.coordinator = User.objects.create_user(
            username="test_coordinator",
            password="test-password-only-for-tests",
        )

        self.purchasing_user = User.objects.create_user(
            username="test_purchasing",
            password="test-password-only-for-tests",
        )

        UserRole.objects.create(
            user=self.coordinator,
            role=self.coordinator_role,
        )

        UserRole.objects.create(
            user=self.purchasing_user,
            role=self.other_role,
        )

    def check_permission(self, user, required_roles):
        request = self.factory.get("/api/test/")
        request.user = user

        class TestView:
            pass

        view = TestView()
        view.required_roles = required_roles

        return self.permission.has_permission(request, view)

    def test_user_with_required_role_is_allowed(self):
        self.assertTrue(
            self.check_permission(
                self.coordinator,
                ("LOGISTICS_COORDINATOR",),
            )
        )

    def test_user_with_wrong_role_is_denied(self):
        self.assertFalse(
            self.check_permission(
                self.purchasing_user,
                ("LOGISTICS_COORDINATOR",),
            )
        )

    def test_user_without_role_is_denied(self):
        user_without_role = User.objects.create_user(
            username="test_no_role",
            password="test-password-only-for-tests",
        )

        self.assertFalse(
            self.check_permission(
                user_without_role,
                ("LOGISTICS_COORDINATOR",),
            )
        )

    def test_inactive_role_is_denied(self):
        self.coordinator_role.is_active = False
        self.coordinator_role.save()

        self.assertFalse(
            self.check_permission(
                self.coordinator,
                ("LOGISTICS_COORDINATOR",),
            )
        )

    def test_missing_required_roles_is_denied(self):
        self.assertFalse(
            self.check_permission(self.coordinator, ())
        )

    def test_anonymous_user_is_denied(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertFalse(
            self.check_permission(AnonymousUser(), ("LOGISTICS_COORDINATOR",))
        )

    def test_superuser_is_allowed(self):
        admin = User.objects.create_superuser(
            username="test_admin",
            email="test_admin@example.com",
            password="test-password-only-for-tests",
        )

        self.assertTrue(
            self.check_permission(admin, ("LOGISTICS_COORDINATOR",))
        )
