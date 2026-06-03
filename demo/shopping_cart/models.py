from django.db import models


class Product(models.Model):
    """
    Product model demonstrating reactive form fields with HTMX.

    The form will dynamically show/hide fields based on the product type:
    - T-shirts have sizes (S/M/L) and colours (Black/White)
    - Trousers have waist sizes (28-32) and colours (Black/Blue/Brown)
    """

    TYPE_TSHIRT = "tshirt"
    TYPE_TROUSERS = "trousers"

    TYPE_CHOICES = [
        ("", "Select type..."),
        (TYPE_TSHIRT, "T-Shirt"),
        (TYPE_TROUSERS, "Trousers"),
    ]

    SIZE_CHOICES = [
        ("", "Select size..."),
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
    ]

    # Waist sizes from 28 to 42
    WAIST_SIZE_CHOICES = [("", "Select waist size...")] + [
        (str(i), str(i)) for i in range(28, 33)
    ]

    TSHIRT_COLOUR_CHOICES = [
        ("", "Select colour..."),
        ("black", "Black"),
        ("white", "White"),
    ]

    TROUSERS_COLOUR_CHOICES = [
        ("", "Select colour..."),
        ("black", "Black"),
        ("blue", "Blue"),
        ("brown", "Brown"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True)
    size = models.CharField(
        max_length=1, choices=SIZE_CHOICES, blank=True, help_text="For T-Shirts only"
    )
    waist_size = models.CharField(
        max_length=2,
        choices=WAIST_SIZE_CHOICES,
        blank=True,
        help_text="For Trousers only",
    )
    colour = models.CharField(max_length=20)

    def __str__(self):
        if self.type == self.TYPE_TSHIRT:
            return f"T-Shirt - Size {self.size} - {self.colour.title()}"
        elif self.type == self.TYPE_TROUSERS:
            return f"Trousers - Waist {self.waist_size} - {self.colour.title()}"
        return "Product (Type not set)"
