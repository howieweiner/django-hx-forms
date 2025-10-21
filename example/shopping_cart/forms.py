from django import forms
from django.urls import reverse_lazy

from django_hx_forms.forms import HtmxModelForm

from .models import Product


class ProductForm(HtmxModelForm):
    """
    Form for creating/updating products with reactive HTMX behavior.

    When the product type changes:
    - Size field is shown/enabled for t-shirts only
    - Waist size field is shown/enabled for trousers only
    - Colour choices update based on the product type
    - Non-applicable fields are reset when type changes
    """

    # HTMX configuration
    hx_post = reverse_lazy("shopping_cart:product-form-update")
    hx_target = "#product-form"
    hx_indicator = "#form-loading"
    default_focus_field = "type"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

        # Set up the form based on current state
        self.check_form_state()

    def check_form_state(self):
        """
        Update form field state based on the selected product type.
        This method is called during initialization and after HTMX triggers.
        """
        product_type = self.get_field_value("type")

        if product_type == Product.TYPE_TSHIRT:
            # T-shirt selected: enable size, disable waist_size
            self.enable_field("size")
            self.set_field_required("size", True)
            self.disable_field("waist_size")
            self.set_field_required("waist_size", False)

            # Update colour choices for t-shirts
            self.fields["colour"].choices = Product.TSHIRT_COLOUR_CHOICES
            self.enable_field("colour")
            self.set_field_required("colour", True)

        elif product_type == Product.TYPE_TROUSERS:
            # Trousers selected: disable size, enable waist_size
            self.disable_field("size")
            self.set_field_required("size", False)
            self.enable_field("waist_size")
            self.set_field_required("waist_size", True)

            # Update colour choices for trousers
            self.fields["colour"].choices = Product.TROUSERS_COLOUR_CHOICES
            self.enable_field("colour")
            self.set_field_required("colour", True)

        else:
            # No type selected: disable all type-specific fields
            self.disable_field("size")
            self.set_field_required("size", False)
            self.disable_field("waist_size")
            self.set_field_required("waist_size", False)
            self.disable_field("colour")
            self.set_field_required("colour", False)

            # Set a placeholder colour choice
            self.fields["colour"].choices = [("", "Select product type first...")]

    class Meta:
        model = Product
        fields = ["type", "size", "waist_size", "colour"]

        # Configure HTMX triggers: when type changes, trigger form update
        htmx_trigger_fields = ["type"]

        # When type changes, reset the dependent fields
        htmx_field_resets = {
            "type": ["size", "waist_size", "colour"],
        }

        widgets = {
            "type": forms.Select(attrs={"class": "form-control"}),
            "size": forms.Select(attrs={"class": "form-control"}),
            "waist_size": forms.Select(attrs={"class": "form-control"}),
            "colour": forms.Select(attrs={"class": "form-control"}),
        }
