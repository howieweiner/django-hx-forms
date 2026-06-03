from django.urls import path

from .views import (
    ItemAddView,
    ItemDeleteView,
    ItemEditView,
    ItemFormUpdateView,
    ItemListView,
)

app_name = "shopping_cart"

urlpatterns = [
    path("", ItemListView.as_view(), name="item-list"),
    path("create/", ItemAddView.as_view(), name="item-add"),
    path("edit/<int:pk>/", ItemEditView.as_view(), name="item-edit"),
    path("delete/<int:pk>/", ItemDeleteView.as_view(), name="item-delete"),
    # HTMX endpoint for form updates
    path("form-update/", ItemFormUpdateView.as_view(), name="item-form-update"),
]
