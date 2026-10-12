
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import HasCoLogiRole
from .models import (
    CargoCategory,
    Hub,
    Outlet,
    Supplier,
    VehicleType,
)
from .serializers import (
    CargoCategorySerializer,
    HubSerializer,
    OutletSerializer,
    SupplierSerializer,
    VehicleTypeSerializer,
)


MASTERDATA_READ_ROLES = (
    "PURCHASING_STAFF",
    "RECEIVING_STAFF",
    "LOGISTICS_COORDINATOR",
    "MANAGER",
    "ADMINISTRATOR",
)


class MasterDataReadOnlyView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, HasCoLogiRole]
    required_roles = MASTERDATA_READ_ROLES


class SupplierListView(MasterDataReadOnlyView):
    serializer_class = SupplierSerializer

    def get_queryset(self):
        return Supplier.objects.filter(is_active=True)


class OutletListView(MasterDataReadOnlyView):
    serializer_class = OutletSerializer

    def get_queryset(self):
        return Outlet.objects.filter(is_active=True)


class CargoCategoryListView(MasterDataReadOnlyView):
    serializer_class = CargoCategorySerializer

    def get_queryset(self):
        return CargoCategory.objects.filter(is_active=True)


class HubListView(MasterDataReadOnlyView):
    serializer_class = HubSerializer

    def get_queryset(self):
        return Hub.objects.filter(is_active=True)


class VehicleTypeListView(MasterDataReadOnlyView):
    serializer_class = VehicleTypeSerializer

    def get_queryset(self):
        return VehicleType.objects.filter(is_active=True)
