
from django.urls import path

from .views import (
    DeliveryDemandDetailView,
    DeliveryDemandListCreateView,
)

app_name = "demands"

urlpatterns = [
    path(
        "",
        DeliveryDemandListCreateView.as_view(),
        name="demand-list-create",
    ),
    path(
        "<int:pk>/",
        DeliveryDemandDetailView.as_view(),
        name="demand-detail",
    ),
]
