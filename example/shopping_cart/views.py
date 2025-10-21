from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import ProductForm
from .models import Product


def product_list(request):
    """Display a list of all products."""
    products = Product.objects.all()
    return render(
        request, "shopping_cart/product_list.html", {"products": products}
    )


def product_create(request):
    """Create a new product."""
    if request.method == "POST":
        form = ProductForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect("shopping_cart:product-list")
    else:
        form = ProductForm()

    return render(
        request,
        "shopping_cart/product_form.html",
        {"form": form, "action": "Create"},
    )


def product_update(request, pk):
    """Update an existing product."""
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(data=request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("shopping_cart:product-list")
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "shopping_cart/product_form.html",
        {"form": form, "action": "Update", "product": product},
    )


def product_delete(request, pk):
    """Delete a product."""
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        product.delete()
        return redirect("shopping_cart:product-list")

    return render(
        request, "shopping_cart/product_confirm_delete.html", {"product": product}
    )


@require_http_methods(["POST"])
def product_form_update(request):
    """
    Handle HTMX form updates for both create and update views.

    This view is triggered when a form field with HTMX attributes changes.
    It returns an updated form fragment with the appropriate fields enabled/disabled
    and choices updated based on the trigger field.
    """
    # Get the trigger field from HTMX headers
    trigger_field = request.POST.get("hx-trigger-name") or request.headers.get(
        "HX-Trigger-Name"
    )

    # Check if we're updating an existing product
    product_id = request.POST.get("product_id")
    instance = None
    if product_id:
        instance = get_object_or_404(Product, pk=product_id)

    # Create form with HTMX data and trigger field
    form = ProductForm(
        htmx_data=request.POST,
        trigger_field=trigger_field,
        instance=instance,
    )

    # Call check_form_state to update field states based on current values
    form.check_form_state()

    # Return only the form HTML for HTMX to swap
    return render(
        request,
        "shopping_cart/partials/product_form_fields.html",
        {"form": form},
    )
