
from django.conf import settings
from django.db import models


class Role(models.Model):
    role_code = models.CharField(max_length=50, unique=True)
    role_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "roles"
        ordering = ["role_code"]

    def __str__(self):
        return f"{self.role_code} - {self.role_name}"


class UserRole(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cologi_role_assignments",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="user_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cologi_role_assignments_created",
    )

    class Meta:
        db_table = "user_roles"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="uq_user_roles_user_role",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.role.role_code}"
