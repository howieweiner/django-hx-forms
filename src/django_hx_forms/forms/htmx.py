from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from django.forms import BooleanField, ModelForm
from django.forms.fields import Field
from django.forms.utils import ErrorList


class HtmxFormMixin:
    """
    Mixin for Django forms to handle HTMX functionality.

    This mixin provides functionality to:
    - Handle trigger field identification from HTMX requests
    - Manage focus field setting based on trigger or default
    - Process HTMX data and handle field resets
    - Set field values from HTMX data
    - Configure HTMX trigger attributes on specified fields
    - Provide utility functions to manage field state

    The mixin accepts and pops the following kwargs before passing to the parent form:
    - trigger_field: The name of the field that triggered the HTMX request
    - htmx_data: The QueryDict containing HTMX form data
    """

    # Type hints for attributes provided by Django Form classes
    # Note: fields, data, initial, is_bound are inherited from BaseForm
    fields: dict[str, Field]
    data: Mapping[str, Any]
    is_bound: bool
    error_class: type[ErrorList]
    _errors: dict[str, ErrorList] | None

    # Type hint for Meta class (used via getattr with defaults)
    Meta: type

    default_focus_field: str | None = None

    # HTMX trigger configuration
    hx_post: str | None = None
    hx_target: str | None = None
    hx_indicator: str | None = None

    def __init__(self, *args, **kwargs):
        # Pop HTMX-specific parameters
        self.trigger_field = kwargs.pop("trigger_field", None)
        self.htmx_data = kwargs.pop("htmx_data", None)

        super().__init__(*args, **kwargs)

        # Configure HTMX trigger fields
        self._setup_htmx_triggers()

        # Handle HTMX-specific processing
        if self.htmx_data:
            self.reset_fields()

        # Set focus field based on trigger field or default
        self._set_focus_field()

        # Set field values from HTMX data if provided
        if self.htmx_data:
            self._set_field_values_from_htmx_data()

    def _set_focus_field(self):
        """
        Set the focus field based on trigger field or default focus field.
        Adds autofocus attribute to the appropriate field widget.
        """
        focus_field = self.get_focus_field()

        if focus_field and focus_field in self.fields:
            self.fields[focus_field].widget.attrs["autofocus"] = True

    def get_focus_field(self):
        """
        Determine which field should receive focus.

        Priority order:
        1. Trigger field (if present and valid)
        2. Default focus field from get_default_focus_field()

        Returns:
            str: Name of field to focus, or None if no focus should be set
        """
        if self.trigger_field:
            return self.trigger_field

        return self.get_default_focus_field()

    def get_default_focus_field(self):
        """
        Get the default field to focus when no trigger field is present.

        Override this method to provide custom default focus logic.

        Returns:
            str: Name of default field to focus, or None
        """
        return self.default_focus_field

    def _setup_htmx_triggers(self):
        """
        Configure HTMX attributes on trigger fields based on Meta configuration.
        """
        # Get trigger fields from Meta configuration
        trigger_fields = getattr(self.Meta, "htmx_trigger_fields", [])

        if not trigger_fields:
            return

        # Validate required attributes are set
        if not self.hx_post:
            logging.warning(
                f"{self.__class__.__name__}: htmx_trigger_fields specified but hx_post not set"
            )
            return

        if not self.hx_target:
            logging.warning(
                f"{self.__class__.__name__}: htmx_trigger_fields specified but hx_target not set"
            )
            return

        # Apply HTMX attributes to specified fields
        for field_name in trigger_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["hx-post"] = self.hx_post
                self.fields[field_name].widget.attrs["hx-target"] = self.hx_target

                # Add indicator if specified
                if self.hx_indicator:
                    self.fields[field_name].widget.attrs["hx-indicator"] = (
                        self.hx_indicator
                    )

    def reset_fields(self):
        """
        Handle field resets based on HTMX trigger field and Meta configuration.
        Updates self.htmx_data with reset field values.
        """
        if not self.htmx_data or not self.trigger_field:
            return

        # Get field reset configuration from Meta class
        field_resets = getattr(self.Meta, "htmx_field_resets", {})

        # Get fields to reset for the current trigger field
        fields_to_reset = field_resets.get(self.trigger_field, [])

        # Always create a copy to ensure we can modify the data
        self.htmx_data = self.htmx_data.copy()

        # Reset specified fields
        for field_name in fields_to_reset:
            self.htmx_data[field_name] = ""

    def _set_field_values_from_htmx_data(self):
        """
        Set field initial values from processed HTMX data.
        """
        for field_name, field in self.fields.items():
            # Skip disabled fields unless they were reset
            if field.widget.attrs.get("disabled") and not self._was_field_reset(
                field_name
            ):
                continue

            # Allow subclasses to override field value setting for specific fields
            if self.skip_htmx_update_for_field(field_name, field):
                continue

            # Handle boolean fields
            if isinstance(field, BooleanField):
                field.initial = self.htmx_data.get(field_name) == "on"
            else:
                value = self.htmx_data.get(field_name)
                field.initial = value

    def skip_htmx_update_for_field(self, field_name, field):
        """
        Hook for subclasses to skip field value setting for specific cases.

        Args:
            field_name (str): Name of the field
            field: The field instance

        Returns:
            bool: True if field value setting should be skipped
        """
        return False

    def _was_field_reset(self, field_name):
        """Check if a field was reset by the current trigger."""
        if not self.trigger_field:
            return False

        # Get field reset configuration from Meta class
        field_resets = getattr(self.Meta, "htmx_field_resets", {})

        # Get fields to reset for the current trigger field
        fields_to_reset = field_resets.get(self.trigger_field, [])

        return field_name in fields_to_reset

    def disable_field(self, field_name):
        """
        Disable a form field by setting the disabled attribute.

        Args:
            field_name (str): Name of the field to disable
        """
        if field_name in self.fields:
            self.fields[field_name].widget.attrs["disabled"] = True

    def enable_field(self, field_name):
        """
        Enable a form field by removing the disabled attribute.

        Args:
            field_name (str): Name of the field to enable
        """
        if field_name in self.fields:
            self.fields[field_name].widget.attrs.pop("disabled", None)

    def set_field_required(self, field_name, required=True):
        """
        Set a field's required status.

        Args:
            field_name (str): Name of the field
            required (bool): Whether the field should be required
        """
        if field_name in self.fields:
            self.fields[field_name].required = required
            if required:
                self.fields[field_name].widget.attrs["required"] = True
            else:
                self.fields[field_name].widget.attrs.pop("required", None)

    def disable_fields(self, field_names):
        """
        Disable multiple fields at once.

        Args:
            field_names (list): List of field names to disable
        """
        for field_name in field_names:
            self.disable_field(field_name)

    def enable_fields(self, field_names):
        """
        Enable multiple fields at once.

        Args:
            field_names (list): List of field names to enable
        """
        for field_name in field_names:
            self.enable_field(field_name)

    def set_fields_required(self, field_names, required=True):
        """
        Set required status for multiple fields at once.

        Args:
            field_names (list): List of field names
            required (bool): Whether the fields should be required
        """
        for field_name in field_names:
            self.set_field_required(field_name, required)

    # Field value utility methods
    def remove_field(self, field_name):
        """
        Remove a field from the form.

        Args:
            field_name (str): Name of the field to remove
        """
        self.fields.pop(field_name, None)

    def remove_fields(self, field_names):
        """
        Remove multiple fields from the form.

        Args:
            field_names (list): List of field names to remove
        """
        for field_name in field_names:
            self.remove_field(field_name)

    def is_field_disabled(self, field_name):
        """
        Check if a form field is disabled.

        Args:
            field_name (str): Name of the field to check

        Returns:
            bool: True if the field is disabled, False otherwise
        """
        if field_name in self.fields:
            return self.fields[field_name].widget.attrs.get("disabled", False)
        return False

    def reset_select_field(self, field_name):
        """
        Reset a select field's initial value to an empty string.

        Args:
            field_name (str): Name of the select field to reset
        """
        if field_name in self.fields:
            self.fields[field_name].initial = ""

    def get_field_queryset(self, field_name):
        """
        Get the queryset for a specified field.

        Args:
            field_name (str): Name of the field

        Returns:
            QuerySet: The queryset for the field, or None if the field does not exist or has no queryset.
        """
        if field_name in self.fields:
            return getattr(self.fields[field_name], "queryset", None)
        return None

    def set_field_initial(self, field_name, value):
        """
        Set a field's initial value.

        Args:
            field_name (str): Name of the select field
            value: The value to set as initial
        """
        if field_name in self.fields:
            self.fields[field_name].initial = value

    def set_field_queryset(self, field_name, queryset: Any) -> None:
        """
        Set the queryset for a specified field.

        Args:
            field_name (str): Name of the field
            queryset: The queryset to set for the field
        """
        if field_name in self.fields:
            self.fields[field_name].queryset = queryset  # type: ignore[attr-defined]

    # Field value utility methods
    def get_field_value(self, field_name):
        """
        Get current field value from HTMX data, form data, initial, or instance.
        Handles boolean field conversion automatically.

        Args:
            field_name (str): Name of the field

        Returns:
            The field value, with boolean fields converted from "on" to True
        """
        # Check if this is a boolean field first
        is_boolean_field = field_name in self.fields and isinstance(
            self.fields[field_name], BooleanField
        )

        # Priority: htmx_data -> initial -> data -> instance
        if self.htmx_data and field_name in self.htmx_data:
            value = self.htmx_data[field_name]
        elif self.data and field_name in self.data:
            value = self.data[field_name]
        elif self.is_bound and is_boolean_field:
            # For boolean fields in bound forms, if the field is absent from form data,
            # it means the checkbox was unchecked, so return False
            return False
        elif hasattr(self, "initial") and field_name in self.initial:
            # Check form initial data (for form-only fields not on the model)
            value = self.initial[field_name]
            # Boolean values from initial may already be True/False, not "on"
            if is_boolean_field:
                return bool(value)
            return value
        elif (
            hasattr(self, "instance")
            and self.instance
            and hasattr(self.instance, field_name)
        ):
            value = getattr(self.instance, field_name)
            # Handle foreign key fields - return the ID, not the object
            if hasattr(value, "pk"):
                return value.pk
            return value
        else:
            return None

        # Handle boolean fields (convert "on" -> True)
        if is_boolean_field:
            return value == "on"

        return value

    def add_htmx_field_error(self, field_name, message):
        """
        Add an error to a form field without requiring cleaned_data.
        Useful for HTMX updates where we want to show validation messages
        without calling is_valid().

        Args:
            field_name (str): The name of the field to add the error to
            message (str): The error message to display
        """
        if not hasattr(self, "_errors") or self._errors is None:
            self._errors = {}

        if field_name not in self._errors:
            self._errors[field_name] = self.error_class()

        self._errors[field_name].append(message)

    def check_form_state(self):
        """
        No-op method to be overridden by subclasses.
        This method is intended to be called by HtmxFormUpdateViewMixin or explicitly
        in a functional view to allow forms to update their state
        (e.g. enable/disable fields) based on HTMX triggers without full validation.
        """
        pass


class HtmxModelForm(HtmxFormMixin, ModelForm):
    """
    A ModelForm that includes HTMX functionality.

    This is a convenience class that combines HtmxFormMixin with Django's ModelForm.
    Use this as a base class for model forms that need HTMX functionality.

    Example:
        class MyForm(HtmxModelForm):
            default_focus_field = "name"
            hx_post = reverse_lazy("my_app:form-update")
            hx_target = "#form-container"
            hx_indicator = "#loading"

            class Meta:
                model = MyModel
                fields = ["name", "email", "category"]
                htmx_trigger_fields = ["category"]
                htmx_field_resets = {
                    "category": ["subcategory", "item"],
                }
    """

    pass
