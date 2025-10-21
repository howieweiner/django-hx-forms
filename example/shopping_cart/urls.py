from django.urls import path

from . import views

app_name = "shopping_cart"

urlpatterns = [
    path("", views.product_list, name="product-list"),
    path("create/", views.product_create, name="product-create"),
    path("update/<int:pk>/", views.product_update, name="product-update"),
    path("delete/<int:pk>/", views.product_delete, name="product-delete"),
    # HTMX endpoint for form updates
    path("form-update/", views.product_form_update, name="product-form-update"),
]
