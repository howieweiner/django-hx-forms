import logging
from typing import Any

from django.db.models import Model
from django.forms import BaseForm
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, QueryDict
from django.views.generic import FormView


class IsHtmxRequestMixin:
    """
    Mixin that ensures the request is an HTMX request.
    Returns 403 Forbidden if the request is not from HTMX.

    Detects HTMX requests by checking for the HX-Request header.
    """

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # HTMX sends HX-Request: true header with all requests
        if not request.headers.get("HX-Request"):
            return HttpResponseForbidden("This view requires an HTMX request")
        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]


class HtmxFormUpdateViewMixin(IsHtmxRequestMixin, FormView):
    """
    Mixin for handling HTMX form updates.
    It overrides get_form to pass HTMX-specific data and trigger fields to the form.
    The post method instantiates the form, calls check_form_state, and renders the response.

    For ModelForms, override get_form_instance() to provide the model instance.
    """

    def get_form_instance(self) -> Model | None:
        """
        Get the model instance for the form (for ModelForms).
        Override this method to provide the instance based on URL parameters, etc.

        Returns:
            Model instance or None

        Example::

            def get_form_instance(self):
                product_id = self.request.POST.get("product_id")
                if product_id:
                    return get_object_or_404(Product, pk=product_id)
                return None
        """
        return None

    def _get_form_instance(
        self,
        form_class: type[BaseForm] | None = None,
        htmx_data: QueryDict | None = None,
    ) -> BaseForm:
        if form_class is None:
            form_class = self.get_form_class()
        trigger_field = self.request.headers.get("HX-Trigger-Name")

        # Get model instance if this is a ModelForm
        instance = self.get_form_instance()

        form_kwargs: dict[str, Any] = {
            "request": self.request,
            "htmx_data": htmx_data,
            "trigger_field": trigger_field,
        }

        if instance is not None:
            form_kwargs["instance"] = instance

        return form_class(**form_kwargs)

    def get_form(self, form_class: type[BaseForm] | None = None) -> BaseForm:
        # For GET requests, htmx_data is typically not present in request.POST
        return self._get_form_instance(
            form_class=form_class, htmx_data=self.request.GET
        )

    def _check_form_state_and_log_warning(self, form: BaseForm) -> None:
        if hasattr(form, "check_form_state"):
            form.check_form_state()
        else:
            logging.warning(
                f"Form {form.__class__.__name__} does not implement check_form_state()."
            )

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        self._check_form_state_and_log_warning(form)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self._get_form_instance(htmx_data=self.request.POST)
        self._check_form_state_and_log_warning(form)
        return self.render_to_response(self.get_context_data(form=form))
