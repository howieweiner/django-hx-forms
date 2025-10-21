from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from django_hx_forms.views import HtmxFormUpdateViewMixin

from .forms import ProductForm
from .models import Product


class ProductListView(ListView):
    """Display a list of all products."""

    model = Product
    template_name = "shopping_cart/product_list.html"
    context_object_name = "products"


class ProductCreateView(CreateView):
    """Create a new product."""

    model = Product
    form_class = ProductForm
    template_name = "shopping_cart/product_form.html"
    success_url = reverse_lazy("shopping_cart:product-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Create"
        return context


class ProductUpdateView(UpdateView):
    """Update an existing product."""

    model = Product
    form_class = ProductForm
    template_name = "shopping_cart/product_form.html"
    success_url = reverse_lazy("shopping_cart:product-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = "Update"
        context["product"] = self.object
        return context


class ProductDeleteView(DeleteView):
    """Delete a product."""

    model = Product
    template_name = "shopping_cart/product_confirm_delete.html"
    success_url = reverse_lazy("shopping_cart:product-list")


class ProductFormUpdateView(HtmxFormUpdateViewMixin):
    """
    Handle HTMX form updates for both create and update views.

    This view is triggered when a form field with HTMX attributes changes.
    It returns an updated form fragment with the appropriate fields enabled/disabled
    and choices updated based on the trigger field.
    """

    form_class = ProductForm
    template_name = "shopping_cart/partials/product_form_fields.html"

    def get_form_instance(self):
        """Get the product instance if updating an existing product."""
        product_id = self.request.POST.get("product_id")
        if product_id:
            return get_object_or_404(Product, pk=product_id)
        return None


# Keep the original names for backward compatibility
product_list = ProductListView.as_view()
product_create = ProductCreateView.as_view()
product_update = ProductUpdateView.as_view()
product_delete = ProductDeleteView.as_view()
product_form_update = ProductFormUpdateView.as_view()
