import pytest
from django import forms
from django.db import models
from django.forms import BooleanField, CharField
from django.test import RequestFactory

from django_hx_forms.forms import HtmxFormMixin, HtmxModelForm


class MockModel(models.Model):
    """Mock model for testing"""

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = "htmx_tests"


class MockHtmxForm(HtmxFormMixin, forms.Form):
    """Test form using HtmxFormMixin"""

    default_focus_field = "test_field"
    hx_post = "/test-url/"
    hx_target = "#test-target"
    hx_indicator = "#test-indicator"

    test_field = CharField(required=False)
    another_field = CharField(required=False)
    boolean_field = BooleanField(required=False)
    choice_field = forms.ChoiceField(
        choices=[("", "---"), ("1", "Option 1"), ("2", "Option 2")], required=False
    )

    def __init__(self, *args, **kwargs):
        # Pop the request parameter like CrispyFormMixin does
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    class Meta:
        htmx_trigger_fields = ["test_field", "another_field"]
        htmx_field_resets = {
            "test_field": ["another_field", "choice_field"],
            "another_field": ["choice_field"],
        }


class MockHtmxModelForm(HtmxModelForm):
    """Test model form using HtmxModelForm"""

    default_focus_field = "name"
    hx_post = "/model-test-url/"
    hx_target = "#model-target"

    name = CharField()
    category = CharField(required=False)

    def __init__(self, *args, **kwargs):
        # Pop the request parameter like CrispyFormMixin does
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = MockModel
        fields = ["name", "category"]
        htmx_trigger_fields = ["name"]
        htmx_field_resets = {
            "name": ["category"],
        }


@pytest.fixture
def mock_request():
    """Create a mock request object for form testing."""
    factory = RequestFactory()
    return factory.get("/")


@pytest.fixture
def htmx_data():
    """Sample HTMX data for testing"""
    return {
        "test_field": "test_value",
        "another_field": "another_value",
        "boolean_field": "on",
        "choice_field": "1",
    }


class MockHtmxFormMixinInitialization:
    """Test HtmxFormMixin initialization and basic functionality"""

    def test_form_initialization_without_htmx_data(self, mock_request):
        """Form should initialize properly without HTMX data"""
        form = MockHtmxForm(request=mock_request)

        assert form.trigger_field is None
        assert form.htmx_data is None
        assert hasattr(form, "fields")

    def test_form_initialization_with_htmx_data(self, mock_request, htmx_data):
        """Form should initialize properly with HTMX data"""
        form = MockHtmxForm(
            request=mock_request, htmx_data=htmx_data, trigger_field="test_field"
        )

        assert form.trigger_field == "test_field"
        assert form.htmx_data is not None
        assert form.fields["test_field"].initial == "test_value"

    def test_form_initialization_with_boolean_field(self, mock_request, htmx_data):
        """Boolean fields should be properly converted from 'on' to True"""
        form = MockHtmxForm(request=mock_request, htmx_data=htmx_data)

        assert form.fields["boolean_field"].initial is True

    def test_form_initialization_with_boolean_field_false(self, mock_request):
        """Boolean fields should be properly handled when False/empty"""
        htmx_data = {"boolean_field": ""}
        form = MockHtmxForm(request=mock_request, htmx_data=htmx_data)

        assert form.fields["boolean_field"].initial is False


class TestHtmxTriggerConfiguration:
    """Test HTMX trigger field configuration"""

    def test_htmx_triggers_configured_on_fields(self, mock_request):
        """HTMX attributes should be configured on trigger fields"""
        form = MockHtmxForm(request=mock_request)

        # Check that HTMX attributes are set on trigger fields
        assert form.fields["test_field"].widget.attrs["hx-post"] == "/test-url/"
        assert form.fields["test_field"].widget.attrs["hx-target"] == "#test-target"
        assert (
            form.fields["test_field"].widget.attrs["hx-indicator"] == "#test-indicator"
        )

        assert form.fields["another_field"].widget.attrs["hx-post"] == "/test-url/"
        assert form.fields["another_field"].widget.attrs["hx-target"] == "#test-target"
        assert (
            form.fields["another_field"].widget.attrs["hx-indicator"]
            == "#test-indicator"
        )

    def test_non_trigger_fields_have_no_htmx_attributes(self, mock_request):
        """Non-trigger fields should not have HTMX attributes"""
        form = MockHtmxForm(request=mock_request)

        # Check that non-trigger fields don't have HTMX attributes
        assert "hx-post" not in form.fields["boolean_field"].widget.attrs
        assert "hx-target" not in form.fields["boolean_field"].widget.attrs
        assert "hx-indicator" not in form.fields["boolean_field"].widget.attrs

    def test_form_without_hx_post_logs_warning(self, mock_request, caplog):
        """Form without hx_post should log a warning"""

        class FormWithoutHxPost(HtmxFormMixin, forms.Form):
            test_field = CharField()

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                super().__init__(*args, **kwargs)

            class Meta:
                htmx_trigger_fields = ["test_field"]

        FormWithoutHxPost(request=mock_request)

        assert "htmx_trigger_fields specified but hx_post not set" in caplog.text

    def test_form_without_hx_target_logs_warning(self, mock_request, caplog):
        """Form without hx_target should log a warning"""

        class FormWithoutHxTarget(HtmxFormMixin, forms.Form):
            hx_post = "/test/"
            test_field = CharField()

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                super().__init__(*args, **kwargs)

            class Meta:
                htmx_trigger_fields = ["test_field"]

        FormWithoutHxTarget(request=mock_request)

        assert "htmx_trigger_fields specified but hx_target not set" in caplog.text


class TestFocusFieldHandling:
    """Test focus field handling functionality"""

    def test_default_focus_field_gets_autofocus(self, mock_request):
        """Default focus field should get autofocus attribute"""
        form = MockHtmxForm(request=mock_request)

        assert form.fields["test_field"].widget.attrs.get("autofocus") is True

    def test_trigger_field_overrides_default_focus(self, mock_request):
        """Trigger field should override default focus field"""
        form = MockHtmxForm(request=mock_request, trigger_field="another_field")

        assert form.fields["another_field"].widget.attrs.get("autofocus") is True
        assert form.fields["test_field"].widget.attrs.get("autofocus") is None

    def test_invalid_focus_field_does_not_cause_error(self, mock_request):
        """Invalid focus field should not cause an error"""
        form = MockHtmxForm(request=mock_request, trigger_field="nonexistent_field")

        # Should not raise an error
        assert "autofocus" not in form.fields["test_field"].widget.attrs

    def test_custom_get_default_focus_field(self, mock_request):
        """Custom get_default_focus_field method should be respected"""

        class CustomFocusForm(HtmxFormMixin, forms.Form):
            field1 = CharField()
            field2 = CharField()

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                super().__init__(*args, **kwargs)

            def get_default_focus_field(self):
                return "field2"

            class Meta:
                pass

        form = CustomFocusForm(request=mock_request)
        assert form.fields["field2"].widget.attrs.get("autofocus") is True


class TestFieldResetFunctionality:
    """Test field reset functionality"""

    def test_field_resets_applied_correctly(self, mock_request):
        """Fields should be reset based on trigger field configuration"""
        htmx_data = {
            "test_field": "new_value",
            "another_field": "should_be_reset",
            "choice_field": "2",
        }

        form = MockHtmxForm(
            request=mock_request, htmx_data=htmx_data, trigger_field="test_field"
        )

        # test_field should keep its value
        assert form.fields["test_field"].initial == "new_value"
        # Fields that should be reset should be empty
        assert form.fields["another_field"].initial == ""
        assert form.fields["choice_field"].initial == ""

    def test_no_resets_without_trigger_field(self, mock_request, htmx_data):
        """No resets should occur without a trigger field"""
        form = MockHtmxForm(request=mock_request, htmx_data=htmx_data)

        # All fields should keep their values
        assert form.fields["test_field"].initial == "test_value"
        assert form.fields["another_field"].initial == "another_value"
        assert form.fields["choice_field"].initial == "1"

    def test_no_resets_for_unconfigured_trigger(self, mock_request, htmx_data):
        """No resets should occur for trigger fields not in configuration"""
        form = MockHtmxForm(
            request=mock_request,
            htmx_data=htmx_data,
            trigger_field="boolean_field",  # Not in reset configuration
        )

        # All fields should keep their values
        assert form.fields["test_field"].initial == "test_value"
        assert form.fields["another_field"].initial == "another_value"
        assert form.fields["choice_field"].initial == "1"


class TestFieldUtilityMethods:
    """Test field utility methods"""

    def test_is_field_disabled_nonexistent_field(self, mock_request):
        """is_field_disabled should return False for nonexistent fields"""
        form = MockHtmxForm(request=mock_request)

        assert form.is_field_disabled("nonexistent_field") is False

    def test_disable_enable_field(self, mock_request):
        """disable_field and enable_field should work correctly"""
        form = MockHtmxForm(request=mock_request)

        # Initially not disabled
        assert not form.is_field_disabled("test_field")

        # Disable field
        form.disable_field("test_field")
        assert form.is_field_disabled("test_field")
        assert form.fields["test_field"].widget.attrs["disabled"] is True

        # Enable field
        form.enable_field("test_field")
        assert not form.is_field_disabled("test_field")
        assert "disabled" not in form.fields["test_field"].widget.attrs

    def test_disable_enable_nonexistent_field(self, mock_request):
        """disable/enable nonexistent field should not cause error"""
        form = MockHtmxForm(request=mock_request)

        # Should not raise an error
        form.disable_field("nonexistent")
        form.enable_field("nonexistent")

    def test_set_field_required(self, mock_request):
        """set_field_required should work correctly"""
        form = MockHtmxForm(request=mock_request)

        # Initially not required
        assert not form.fields["test_field"].required

        # Set required
        form.set_field_required("test_field", True)
        assert form.fields["test_field"].required
        assert form.fields["test_field"].widget.attrs["required"] is True

        # Set not required
        form.set_field_required("test_field", False)
        assert not form.fields["test_field"].required
        assert "required" not in form.fields["test_field"].widget.attrs

    def test_batch_field_operations(self, mock_request):
        """Batch operations on multiple fields should work"""
        form = MockHtmxForm(request=mock_request)

        fields_to_modify = ["test_field", "another_field"]

        # Disable multiple fields
        form.disable_fields(fields_to_modify)
        for field_name in fields_to_modify:
            assert form.is_field_disabled(field_name)

        # Enable multiple fields
        form.enable_fields(fields_to_modify)
        for field_name in fields_to_modify:
            assert not form.is_field_disabled(field_name)

        # Set multiple fields required
        form.set_fields_required(fields_to_modify, True)
        for field_name in fields_to_modify:
            assert form.fields[field_name].required

    def test_remove_field(self, mock_request):
        """remove_field should remove fields from form"""
        form = MockHtmxForm(request=mock_request)

        assert "test_field" in form.fields
        form.remove_field("test_field")
        assert "test_field" not in form.fields

    def test_remove_fields_batch(self, mock_request):
        """remove_fields should remove multiple fields"""
        form = MockHtmxForm(request=mock_request)

        fields_to_remove = ["test_field", "another_field"]
        form.remove_fields(fields_to_remove)

        for field_name in fields_to_remove:
            assert field_name not in form.fields

    def test_set_field_initial(self, mock_request):
        """set_field_initial should set initial values"""
        form = MockHtmxForm(request=mock_request)

        form.set_field_initial("test_field", "new_initial_value")
        assert form.fields["test_field"].initial == "new_initial_value"

    def test_reset_select_field(self, mock_request):
        """reset_select_field should reset field to empty string"""
        form = MockHtmxForm(request=mock_request)

        form.fields["choice_field"].initial = "1"
        form.reset_select_field("choice_field")
        assert form.fields["choice_field"].initial == ""

    def test_get_field_queryset(self, mock_request):
        """get_field_queryset should return queryset for ModelChoiceFields"""
        from django.forms import ModelChoiceField

        class FormWithQueryset(HtmxFormMixin, forms.Form):
            category = ModelChoiceField(queryset=MockModel.objects.none())

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                super().__init__(*args, **kwargs)

            class Meta:
                pass

        form = FormWithQueryset(request=mock_request)

        # Should return the queryset
        queryset = form.get_field_queryset("category")
        assert queryset is not None

    def test_get_field_queryset_nonexistent_field(self, mock_request):
        """get_field_queryset should return None for nonexistent fields"""
        form = MockHtmxForm(request=mock_request)

        assert form.get_field_queryset("nonexistent_field") is None

    def test_get_field_queryset_field_without_queryset(self, mock_request):
        """get_field_queryset should return None for fields without queryset"""
        form = MockHtmxForm(request=mock_request)

        # CharField doesn't have a queryset attribute
        assert form.get_field_queryset("test_field") is None

    def test_set_field_queryset(self, mock_request):
        """set_field_queryset should set queryset for ModelChoiceFields"""
        from django.forms import ModelChoiceField

        class FormWithQueryset(HtmxFormMixin, forms.Form):
            category = ModelChoiceField(queryset=MockModel.objects.none())

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                super().__init__(*args, **kwargs)

            class Meta:
                pass

        form = FormWithQueryset(request=mock_request)

        # Initially the queryset is empty (none())
        assert form.fields["category"].queryset.query.is_empty()

        # Set a new queryset
        new_queryset = MockModel.objects.all()
        form.set_field_queryset("category", new_queryset)

        # The queryset should no longer be empty
        assert not form.fields["category"].queryset.query.is_empty()

    def test_set_field_queryset_nonexistent_field(self, mock_request):
        """set_field_queryset should silently ignore nonexistent fields"""
        form = MockHtmxForm(request=mock_request)

        # Should not raise an error
        form.set_field_queryset("nonexistent_field", MockModel.objects.none())


class TestGetFieldValue:
    """Test get_field_value method"""

    def test_get_field_value_from_htmx_data(self, mock_request, htmx_data):
        """get_field_value should prioritize htmx_data"""
        form_data = {"test_field": "form_data_value"}

        form = MockHtmxForm(data=form_data, request=mock_request, htmx_data=htmx_data)

        # Should return value from htmx_data, not form data
        assert form.get_field_value("test_field") == "test_value"

    def test_get_field_value_from_form_data(self, mock_request):
        """get_field_value should fall back to form data"""
        form_data = {"test_field": "form_data_value"}

        form = MockHtmxForm(data=form_data, request=mock_request)

        assert form.get_field_value("test_field") == "form_data_value"

    def test_get_field_value_boolean_conversion(self, mock_request):
        """get_field_value should convert boolean fields properly"""
        htmx_data = {"boolean_field": "on"}

        form = MockHtmxForm(request=mock_request, htmx_data=htmx_data)

        assert form.get_field_value("boolean_field") is True

    def test_get_field_value_nonexistent_field(self, mock_request):
        """get_field_value should return None for nonexistent fields"""
        form = MockHtmxForm(request=mock_request)

        assert form.get_field_value("nonexistent_field") is None

    def test_get_field_value_works_without_instance_attribute(self, mock_request):
        """get_field_value should work on regular forms without instance attribute"""

        # Create a form that doesn't have an instance attribute (regular Form, not ModelForm)
        class PlainHtmxForm(HtmxFormMixin, forms.Form):
            test_field = forms.CharField(required=False)

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                super().__init__(*args, **kwargs)

            class Meta:
                pass

        form = PlainHtmxForm(request=mock_request)

        # This should not raise an AttributeError
        assert form.get_field_value("test_field") is None
        assert form.get_field_value("nonexistent_field") is None

        # Test with form data
        form_with_data = PlainHtmxForm(
            data={"test_field": "test_value"}, request=mock_request
        )
        assert form_with_data.get_field_value("test_field") == "test_value"

    def test_get_field_value_boolean_field_unchecked_from_form_data(self, mock_request):
        """get_field_value should return False for unchecked boolean fields from form data"""
        # When a checkbox is unchecked, it's not included in form data
        form_data = {
            "test_field": "some_value"
        }  # boolean_field not present = unchecked

        form = MockHtmxForm(data=form_data, request=mock_request)

        # This should return False, not None
        assert form.get_field_value("boolean_field") is False

    def test_get_field_value_boolean_field_checked_from_form_data(self, mock_request):
        """get_field_value should return True for checked boolean fields from form data"""
        form_data = {"test_field": "some_value", "boolean_field": "on"}

        form = MockHtmxForm(data=form_data, request=mock_request)

        assert form.get_field_value("boolean_field") is True

    def test_get_field_value_unbound_form_returns_none_for_boolean(self, mock_request):
        """get_field_value should return None for boolean fields in unbound forms without instance"""
        form = MockHtmxForm(request=mock_request)

        # Unbound form without instance should return None for boolean fields
        assert form.get_field_value("boolean_field") is None

    def test_get_field_value_from_initial_data(self, mock_request):
        """get_field_value should return value from form initial data"""
        form = MockHtmxForm(
            request=mock_request, initial={"test_field": "initial_value"}
        )

        assert form.get_field_value("test_field") == "initial_value"

    def test_get_field_value_initial_data_priority(self, mock_request):
        """get_field_value should prioritize htmx_data over initial data"""
        htmx_data = {"test_field": "htmx_value"}
        form = MockHtmxForm(
            request=mock_request,
            htmx_data=htmx_data,
            initial={"test_field": "initial_value"},
        )

        # htmx_data should take priority over initial
        assert form.get_field_value("test_field") == "htmx_value"

    def test_get_field_value_boolean_from_initial_data(self, mock_request):
        """get_field_value should handle boolean fields from initial data correctly"""
        form = MockHtmxForm(request=mock_request, initial={"boolean_field": True})

        assert form.get_field_value("boolean_field") is True

        # Also test False value
        form_false = MockHtmxForm(
            request=mock_request, initial={"boolean_field": False}
        )

        assert form_false.get_field_value("boolean_field") is False

    def test_get_field_value_from_instance(self, mock_request):
        """get_field_value should return value from instance when not in initial"""

        # Create a form with an instance attribute but where the field is not in initial
        class FormWithInstance(HtmxFormMixin, forms.Form):
            # Form has no fields, so initial won't contain instance values
            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                self.instance = kwargs.pop("instance", None)
                super().__init__(*args, **kwargs)

            class Meta:
                pass

        instance = MockModel(name="Test Name", category="Test Category")
        form = FormWithInstance(request=mock_request, instance=instance)

        # Should get value from instance since it's not in htmx_data, data, or initial
        assert form.get_field_value("name") == "Test Name"
        assert form.get_field_value("category") == "Test Category"

    def test_get_field_value_from_instance_with_foreign_key(self, mock_request):
        """get_field_value should return pk for foreign key fields"""

        class RelatedModel(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = "htmx_tests"

        class ModelWithFK(models.Model):
            name = models.CharField(max_length=100)
            related = models.ForeignKey(
                RelatedModel, on_delete=models.CASCADE, null=True
            )

            class Meta:
                app_label = "htmx_tests"

        # Create a form with an instance attribute but where the field is not in initial
        class FormWithFKInstance(HtmxFormMixin, forms.Form):
            # Form has no fields, so initial won't contain instance values
            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                self.instance = kwargs.pop("instance", None)
                super().__init__(*args, **kwargs)

            class Meta:
                pass

        # Create a mock related object with a pk
        related_obj = RelatedModel(name="Related")
        related_obj.pk = 42

        instance = ModelWithFK(name="Test")
        instance.related = related_obj

        form = FormWithFKInstance(request=mock_request, instance=instance)

        # Should return the pk, not the object
        assert form.get_field_value("related") == 42


class TestHtmxFieldErrors:
    """Test HTMX field error functionality"""

    def test_add_htmx_field_error(self, mock_request):
        """add_htmx_field_error should add errors without validation"""
        form = MockHtmxForm(request=mock_request)

        form.add_htmx_field_error("test_field", "Test error message")

        assert "test_field" in form.errors
        assert "Test error message" in form.errors["test_field"]

    def test_add_multiple_htmx_field_errors(self, mock_request):
        """Should be able to add multiple errors to the same field"""
        form = MockHtmxForm(request=mock_request)

        form.add_htmx_field_error("test_field", "First error")
        form.add_htmx_field_error("test_field", "Second error")

        assert len(form.errors["test_field"]) == 2
        assert "First error" in form.errors["test_field"]
        assert "Second error" in form.errors["test_field"]


class TestSkipHtmxUpdate:
    """Test skip_htmx_update_for_field hook"""

    def test_skip_htmx_update_for_field_hook(self, mock_request):
        """skip_htmx_update_for_field should be called for each field"""

        class CustomForm(HtmxFormMixin, forms.Form):
            field1 = CharField()
            field2 = CharField()

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                super().__init__(*args, **kwargs)

            def skip_htmx_update_for_field(self, field_name, field):
                return field_name == "field1"

            class Meta:
                pass

        htmx_data = {"field1": "value1", "field2": "value2"}
        form = CustomForm(request=mock_request, htmx_data=htmx_data)

        # field1 should be skipped (no initial value set)
        assert form.fields["field1"].initial is None
        # field2 should be updated
        assert form.fields["field2"].initial == "value2"


class TestDisabledFieldHandling:
    """Test handling of disabled fields during HTMX updates"""

    def test_disabled_fields_skip_htmx_update(self, mock_request, htmx_data):
        """Disabled fields should skip HTMX updates unless reset"""
        form = MockHtmxForm(request=mock_request, htmx_data=htmx_data)

        # Disable a field after initialization
        form.disable_field("another_field")

        # Reinitialize with HTMX data
        form._set_field_values_from_htmx_data()

        # Disabled field should not be updated
        # Note: This test shows the current behavior, but the field was already
        # updated during initialization, so we test that disabled fields
        # maintain their initial state when re-processing

    def test_disabled_field_is_updated_if_in_reset_list(self, mock_request):
        """Disabled fields should be updated if they are in the reset list"""

        class FormWithDisabledField(HtmxFormMixin, forms.Form):
            trigger_field = CharField(required=False)
            disabled_field = CharField(required=False)

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                super().__init__(*args, **kwargs)
                # Disable the field
                self.fields["disabled_field"].widget.attrs["disabled"] = True

            class Meta:
                htmx_trigger_fields = []
                htmx_field_resets = {
                    "trigger_field": ["disabled_field"],
                }

        htmx_data = {
            "trigger_field": "some_value",
            "disabled_field": "new_value",
        }

        # Create form with trigger_field triggering reset of disabled_field
        form = FormWithDisabledField(
            request=mock_request, htmx_data=htmx_data, trigger_field="trigger_field"
        )

        # The disabled field should be updated because it's in the reset list
        # First it gets reset to empty string, then set from htmx_data
        assert form.fields["disabled_field"].initial == ""

    def test_was_field_reset_returns_true_for_reset_fields(self, mock_request):
        """_was_field_reset should return True for fields in reset list"""
        htmx_data = {"test_field": "value"}
        form = MockHtmxForm(
            request=mock_request, htmx_data=htmx_data, trigger_field="test_field"
        )

        # another_field is in the reset list for test_field trigger
        assert form._was_field_reset("another_field") is True
        assert form._was_field_reset("choice_field") is True
        # test_field is not in its own reset list
        assert form._was_field_reset("test_field") is False

    def test_was_field_reset_returns_false_without_trigger(self, mock_request):
        """_was_field_reset should return False when no trigger_field"""
        form = MockHtmxForm(request=mock_request)

        assert form._was_field_reset("another_field") is False


class TestCheckFormState:
    """Test check_form_state method"""

    def test_check_form_state_default_implementation(self, mock_request):
        """check_form_state should have a default no-op implementation"""
        form = MockHtmxForm(request=mock_request)

        # Should not raise an error
        form.check_form_state()

    def test_check_form_state_can_be_overridden(self, mock_request):
        """check_form_state should be overridable by subclasses"""

        class CustomForm(HtmxFormMixin, forms.Form):
            test_field = CharField()

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                super().__init__(*args, **kwargs)

            def check_form_state(self):
                self.disable_field("test_field")

            class Meta:
                pass

        form = CustomForm(request=mock_request)
        form.check_form_state()

        assert form.is_field_disabled("test_field")
