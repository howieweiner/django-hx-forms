import pytest
from django import forms
from django.http import HttpResponse
from django.test import RequestFactory
from django.views.generic import View
from django_htmx.middleware import HtmxDetails

from django_hx_forms.views.mixins import HtmxFormUpdateViewMixin, IsHtmxRequestMixin


class MockForm(forms.Form):
    """Mock form for view testing"""

    test_field = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.htmx_data = kwargs.pop("htmx_data", None)
        self.trigger_field = kwargs.pop("trigger_field", None)
        super().__init__(*args, **kwargs)

    def check_form_state(self):
        """Mock check_form_state method"""
        pass


class MockFormWithoutCheckFormState(forms.Form):
    """Mock form without check_form_state method"""

    test_field = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.htmx_data = kwargs.pop("htmx_data", None)
        self.trigger_field = kwargs.pop("trigger_field", None)
        super().__init__(*args, **kwargs)


@pytest.fixture
def request_factory():
    """Create a RequestFactory instance"""
    return RequestFactory()


def setup_view_for_testing(view_class, request, **view_kwargs):
    """
    Helper function to properly set up a view for testing.
    This mimics what Django does during request processing.
    """
    view = view_class()
    view.setup(request, **view_kwargs)
    view.request = request
    return view


@pytest.fixture
def htmx_request(request_factory):
    """Create an HTMX request"""
    request = request_factory.post(
        "/test/",
        {"test_field": "test_value"},
        HTTP_HX_REQUEST="true",
        HTTP_HX_TRIGGER_NAME="test_field",
    )
    request.htmx = HtmxDetails(request)
    # Need to manually set this to True since we're not using middleware
    request.htmx._boosted = False
    request.htmx._current_url = None
    request.htmx._history_restore_request = False
    request.htmx._prompt = None
    request.htmx._request = True
    request.htmx._target = None
    request.htmx._trigger = None
    request.htmx._trigger_name = "test_field"
    return request


@pytest.fixture
def non_htmx_request(request_factory):
    """Create a non-HTMX request"""
    request = request_factory.post("/test/", {"test_field": "test_value"})
    request.htmx = HtmxDetails(request)
    # Default HtmxDetails should be falsy for non-HTMX requests
    return request


@pytest.fixture
def htmx_get_request(request_factory):
    """Create an HTMX GET request"""
    request = request_factory.get(
        "/test/",
        {"test_field": "test_value"},
        HTTP_HX_REQUEST="true",
        HTTP_HX_TRIGGER_NAME="test_field",
    )
    request.htmx = HtmxDetails(request)
    # Need to manually set this to True since we're not using middleware
    request.htmx._boosted = False
    request.htmx._current_url = None
    request.htmx._history_restore_request = False
    request.htmx._prompt = None
    request.htmx._request = True
    request.htmx._target = None
    request.htmx._trigger = None
    request.htmx._trigger_name = "test_field"
    return request


class TestIsHtmxRequestMixin:
    """Test IsHtmxRequestMixin functionality"""

    def test_allows_htmx_requests(self, htmx_request):
        """Should allow HTMX requests to proceed"""

        class MockView(IsHtmxRequestMixin, View):
            def post(self, request, *args, **kwargs):
                return HttpResponse("Success")

        view = MockView()
        response = view.dispatch(htmx_request)

        assert response.status_code == 200
        assert response.content == b"Success"

    def test_blocks_non_htmx_requests(self, non_htmx_request):
        """Should block non-HTMX requests with 403"""

        class MockView(IsHtmxRequestMixin, View):
            def post(self, request, *args, **kwargs):
                return HttpResponse("Should not reach here")

        view = MockView()
        response = view.dispatch(non_htmx_request)

        assert response.status_code == 403
        assert b"HTMX request" in response.content


class TestHtmxFormUpdateViewMixin:
    """Test HtmxFormUpdateViewMixin functionality"""

    def test_requires_htmx_request(self, non_htmx_request):
        """Should require HTMX requests"""

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

        view = MockView()
        response = view.dispatch(non_htmx_request)

        assert response.status_code == 403

    def test_get_form_with_htmx_data_from_get_params(self, htmx_get_request):
        """GET request should use GET parameters as HTMX data"""

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                form = context["form"]
                return HttpResponse(f"Form created with: {form.htmx_data}")

        view = setup_view_for_testing(MockView, htmx_get_request)
        response = view.dispatch(htmx_get_request)

        assert b"test_field" in response.content

    def test_post_form_with_htmx_data_from_post(self, htmx_request):
        """POST request should use POST data as HTMX data"""

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                form = context["form"]
                return HttpResponse(f"Form POST data: {form.htmx_data}")

        view = setup_view_for_testing(MockView, htmx_request)
        response = view.dispatch(htmx_request)

        assert b"test_field" in response.content

    def test_form_receives_trigger_field(self, htmx_request):
        """Form should receive trigger field from HX-Trigger-Name header"""

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                form = context["form"]
                return HttpResponse(f"Trigger field: {form.trigger_field}")

        view = setup_view_for_testing(MockView, htmx_request)
        response = view.dispatch(htmx_request)

        assert response.content == b"Trigger field: test_field"

    def test_form_receives_request_object(self, htmx_request):
        """Form should receive request object"""

        class MockFormWithRequest(forms.Form):
            test_field = forms.CharField(required=False)

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                self.htmx_data = kwargs.pop("htmx_data", None)
                self.trigger_field = kwargs.pop("trigger_field", None)
                super().__init__(*args, **kwargs)

            def check_form_state(self):
                pass

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockFormWithRequest
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                form = context["form"]
                has_request = hasattr(form, "request") and form.request is not None
                return HttpResponse(f"Form has request: {has_request}")

        view = setup_view_for_testing(MockView, htmx_request)
        response = view.dispatch(htmx_request)

        assert response.content == b"Form has request: True"

    def test_calls_check_form_state_on_form(self, htmx_request):
        """Should call check_form_state on the form if available"""

        class TrackingForm(forms.Form):
            test_field = forms.CharField(required=False)
            check_form_state_called = False

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop("request", None)
                self.htmx_data = kwargs.pop("htmx_data", None)
                self.trigger_field = kwargs.pop("trigger_field", None)
                super().__init__(*args, **kwargs)

            def check_form_state(self):
                TrackingForm.check_form_state_called = True

        class MockView(HtmxFormUpdateViewMixin):
            form_class = TrackingForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                return HttpResponse("Success")

        view = setup_view_for_testing(MockView, htmx_request)
        view.dispatch(htmx_request)

        assert TrackingForm.check_form_state_called

    def test_logs_warning_for_form_without_check_form_state(self, htmx_request, caplog):
        """Should log warning if form doesn't have check_form_state method"""

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockFormWithoutCheckFormState
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                return HttpResponse("Success")

        view = setup_view_for_testing(MockView, htmx_request)
        view.dispatch(htmx_request)

        assert "does not implement check_form_state()" in caplog.text

    def test_get_request_handling(self, htmx_get_request):
        """Should handle GET requests properly"""

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                return HttpResponse("GET handled")

        view = setup_view_for_testing(MockView, htmx_get_request)
        response = view.dispatch(htmx_get_request)

        assert response.status_code == 200
        assert response.content == b"GET handled"

    def test_post_request_handling(self, htmx_request):
        """Should handle POST requests properly"""

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                return HttpResponse("POST handled")

        view = setup_view_for_testing(MockView, htmx_request)
        response = view.dispatch(htmx_request)

        assert response.status_code == 200
        assert response.content == b"POST handled"

    def test_form_class_resolution(self, htmx_request):
        """Should properly resolve form class"""

        class CustomForm(MockForm):
            custom_field = forms.CharField(required=False)

        class MockView(HtmxFormUpdateViewMixin):
            form_class = CustomForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                form = context["form"]
                has_custom_field = "custom_field" in form.fields
                return HttpResponse(f"Has custom field: {has_custom_field}")

        view = setup_view_for_testing(MockView, htmx_request)
        response = view.dispatch(htmx_request)

        assert response.content == b"Has custom field: True"

    def test_context_data_includes_form(self, htmx_request):
        """Context should include the form"""

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                has_form = "form" in context
                form_is_correct_type = isinstance(context.get("form"), MockForm)
                return HttpResponse(
                    f"Has form: {has_form}, Correct type: {form_is_correct_type}"
                )

        view = setup_view_for_testing(MockView, htmx_request)
        response = view.dispatch(htmx_request)

        assert b"Has form: True" in response.content
        assert b"Correct type: True" in response.content

    def test_private_get_form_instance_method(self, htmx_request):
        """_get_form_instance should create form with proper parameters"""

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

        view = setup_view_for_testing(MockView, htmx_request)

        # Test without htmx_data
        form = view._get_form_instance()
        assert isinstance(form, MockForm)

        # Test with htmx_data
        form = view._get_form_instance(htmx_data={"test": "value"})
        assert hasattr(form, "htmx_data")

    def test_supports_custom_form_class_via_get_form_class(self, htmx_request):
        """Should support dynamic form class resolution via get_form_class"""

        class MockView(HtmxFormUpdateViewMixin):
            template_name = "test.html"

            def get_form_class(self):
                return MockForm

            def render_to_response(self, context, **response_kwargs):
                form = context["form"]
                return HttpResponse(f"Form type: {type(form).__name__}")

        view = setup_view_for_testing(MockView, htmx_request)
        response = view.dispatch(htmx_request)

        assert response.content == b"Form type: MockForm"


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_missing_hx_trigger_name_header(self, request_factory):
        """Should handle missing HX-Trigger-Name header gracefully"""
        request = request_factory.post(
            "/test/", {"test_field": "test_value"}, HTTP_HX_REQUEST="true"
        )
        request.htmx = HtmxDetails(request)
        # Set HTMX to True but no trigger name
        request.htmx._request = True

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                form = context["form"]
                trigger = getattr(form, "trigger_field", "None")
                return HttpResponse(f"Trigger: {trigger}")

        view = setup_view_for_testing(MockView, request)
        response = view.dispatch(request)

        assert response.content == b"Trigger: None"

    def test_empty_post_data(self, request_factory):
        """Should handle empty POST data gracefully"""
        request = request_factory.post(
            "/test/", HTTP_HX_REQUEST="true", HTTP_HX_TRIGGER_NAME="test_field"
        )
        request.htmx = HtmxDetails(request)
        # Set HTMX to True
        request.htmx._request = True
        request.htmx._trigger_name = "test_field"

        class MockView(HtmxFormUpdateViewMixin):
            form_class = MockForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                return HttpResponse("Success")

        view = setup_view_for_testing(MockView, request)
        response = view.dispatch(request)

        assert response.status_code == 200

    def test_form_without_htmx_mixin(self, htmx_request, caplog):
        """Should handle forms that don't use HtmxFormMixin"""

        class PlainForm(forms.Form):
            test_field = forms.CharField(required=False)

            def __init__(self, *args, **kwargs):
                # Must handle the HTMX parameters even if not using the mixin
                kwargs.pop("request", None)
                kwargs.pop("htmx_data", None)
                kwargs.pop("trigger_field", None)
                super().__init__(*args, **kwargs)

        class MockView(HtmxFormUpdateViewMixin):
            form_class = PlainForm
            template_name = "test.html"

            def render_to_response(self, context, **response_kwargs):
                return HttpResponse("Success")

        view = setup_view_for_testing(MockView, htmx_request)
        response = view.dispatch(htmx_request)

        assert response.status_code == 200
        assert "does not implement check_form_state()" in caplog.text
