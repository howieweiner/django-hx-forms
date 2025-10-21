from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["__str__", "type", "created_at"]
    list_filter = ["type", "created_at"]
    search_fields = ["type", "colour"]
