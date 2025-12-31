from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView

from django_hx_forms.views import HtmxFormUpdateViewMixin

from .forms import ProductForm
from .models import Product


class ItemListView(ListView):
    """Display all items in the shopping cart."""

    model = Product
    template_name = "shopping_cart/item_list.html"
    context_object_name = "items"


class ItemAddView(CreateView):
    """Add a new item to the shopping cart."""

    model = Product
    form_class = ProductForm
    template_name = "shopping_cart/item_form.html"
    success_url = reverse_lazy("shopping_cart:item-list")


class ItemDeleteView(DeleteView):
    """Remove an item from the shopping cart."""

    model = Product
    template_name = "shopping_cart/item_confirm_delete.html"
    success_url = reverse_lazy("shopping_cart:item-list")


class ItemFormUpdateView(HtmxFormUpdateViewMixin):
    """
    Handle HTMX form updates for the add to cart form.

    This view is triggered when a form field with HTMX attributes changes.
    It returns an updated form fragment with the appropriate fields enabled/disabled
    and choices updated based on the trigger field.
    """

    form_class = ProductForm
    template_name = "shopping_cart/partials/item_form_fields.html"
