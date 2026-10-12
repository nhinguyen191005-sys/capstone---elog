
from rest_framework.permissions import BasePermission


class HasCoLogiRole(BasePermission):
    """
    Cho phép truy cập nếu người dùng có ít nhất một vai trò CoLogi
    được yêu cầu bởi view thông qua thuộc tính required_roles.
    """

    message = "Bạn không có quyền thực hiện thao tác này."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Django superuser được phép vượt qua kiểm tra vai trò.
        if user.is_superuser:
            return True

        required_roles = getattr(view, "required_roles", ())

        if not required_roles:
            return False

        return user.cologi_role_assignments.filter(
            role__role_code__in=required_roles,
            role__is_active=True,
        ).exists()
