
from django.urls import path

from .views import (
    CargoCategoryListView,
    HubListView,
    OutletListView,
    SupplierListView,
    VehicleTypeListView,
)

app_name = "masterdata"

urlpatterns = [
    path("suppliers/", SupplierListView.as_view(), name="supplier-list"),
    path("outlets/", OutletListView.as_view(), name="outlet-list"),
    path(
        "cargo-categories/",
        CargoCategoryListView.as_view(),
        name="cargo-category-list",
    ),
    path("hubs/", HubListView.as_view(), name="hub-list"),
    path(
        "vehicle-types/",
        VehicleTypeListView.as_view(),
        name="vehicle-type-list",
    ),
]
