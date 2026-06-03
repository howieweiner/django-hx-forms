from django.urls import reverse_lazy

from django_hx_forms.forms import HtmxModelForm

from .models import Product


class ProductForm(HtmxModelForm):
    """
    Form for adding cart items with reactive HTMX behavior.

    When the product type changes:
    - Size field is shown/enabled for t-shirts only
    - Waist size field is shown/enabled for trousers only
    - Colour choices update based on the product type
    - Non-applicable fields are reset when type changes
    """

    # HTMX configuration
    hx_post = reverse_lazy("shopping_cart:item-form-update")
    hx_target = "#item-form"
    hx_indicator = "#form-loading"
    default_focus_field = "type"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Tailwind CSS classes for styling
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            )

        # Set up the form based on current state
        self.check_form_state()

    def check_form_state(self):
        """
        Update form field state based on the selected product type.
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

        elif product_type == Product.TYPE_TROUSERS:
            # Trousers selected: disable size, enable waist_size
            self.disable_field("size")
            self.set_field_required("size", False)
            self.enable_field("waist_size")
            self.set_field_required("waist_size", True)

            # Update colour choices for trousers
            self.fields["colour"].choices = Product.TROUSERS_COLOUR_CHOICES
        else:
            # No type selected: disable all type-specific fields
            self.disable_field("size")
            self.set_field_required("size", False)
            self.disable_field("waist_size")
            self.set_field_required("waist_size", False)

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
