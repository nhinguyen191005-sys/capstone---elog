
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import HasCoLogiRole
from .models import DeliveryDemand
from .serializers import DeliveryDemandSerializer


READ_ROLES = (
    "PURCHASING_STAFF",
    "RECEIVING_STAFF",
    "LOGISTICS_COORDINATOR",
    "MANAGER",
    "ADMINISTRATOR",
)

WRITE_ROLES = (
    "PURCHASING_STAFF",
    "ADMINISTRATOR",
)


class DeliveryDemandListCreateView(generics.ListCreateAPIView):
    queryset = DeliveryDemand.objects.select_related(
        "supplier",
        "outlet",
        "cargo_category",
        "created_by",
    ).all()

    serializer_class = DeliveryDemandSerializer
    permission_classes = [IsAuthenticated, HasCoLogiRole]

    def get_required_roles(self):
        if self.request.method == "POST":
            return WRITE_ROLES
        return READ_ROLES

    @property
    def required_roles(self):
        return self.get_required_roles()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DeliveryDemandDetailView(generics.RetrieveUpdateAPIView):
    queryset = DeliveryDemand.objects.select_related(
        "supplier",
        "outlet",
        "cargo_category",
        "created_by",
    ).all()

    serializer_class = DeliveryDemandSerializer
    permission_classes = [IsAuthenticated, HasCoLogiRole]

    http_method_names = ["get", "patch", "head", "options"]

    @property
    def required_roles(self):
        if self.request.method == "PATCH":
            return WRITE_ROLES
        return READ_ROLES

    def get_queryset(self):
        queryset = super().get_queryset()

        # Không cho chỉnh sửa yêu cầu đã bị hủy.
        if self.request.method == "PATCH":
            return queryset.exclude(
                status=DeliveryDemand.Status.CANCELLED
            )

        return queryset
