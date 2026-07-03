# django-hx-forms

[![PyPI version](https://img.shields.io/pypi/v/django-hx-forms.svg)](https://pypi.org/project/django-hx-forms/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-hx-forms.svg)](https://pypi.org/project/django-hx-forms/)
[![License: MIT](https://img.shields.io/pypi/l/django-hx-forms.svg)](https://github.com/howieweiner/django-hx-forms/blob/main/LICENSE)

Django forms mixin for managing form updates using htmx triggers

django-hx-forms provides a mixin for Django forms to allow related form fields to be updated via HTMX events.
No javascript is required (aside from HTMX itself). All the logic surrounding related fields is handled with the Django
form. Examples:

- A choice field needs updating based on another choice field being selected
- A field needs hiding based on another field's state
- A field needs resetting based on another field's state
- A field needs disabling based on another field's state

The form allows rules to be defined to identify which fields should trigger an update, and which fields are affected
by this trigger.

## Installation

**With uv:**

```bash
uv add django-hx-forms
```

**With pip:**

```bash
pip install django-hx-forms
```

Or add it to your `pyproject.toml` dependencies directly:

```toml
dependencies = [
    "django-hx-forms",
]
```

You also need [HTMX](https://htmx.org/) loaded in your templates — see the
[HTMX installation instructions](https://htmx.org/docs/#installing) for the current options.

## Usage

A reactive form is made of three parts: a **form** that declares its trigger fields and how it reacts, a
**view** that re-renders the form when a trigger fires, and a **template partial** shared between the initial
page and the HTMX response.

The examples below use a country/region form, where choosing a country narrows the available regions.

### Form mixin

Subclass `HtmxModelForm` (a `ModelForm` with the mixin applied) or add `HtmxFormMixin` to a plain `Form`.
Point the `hx_*` attributes at your update endpoint, declare the reactive rules in `Meta`, and override
`check_form_state()` to adjust the form for the current values.

```python
from django.urls import reverse_lazy

from django_hx_forms.forms import HtmxModelForm

from .models import Address


class AddressForm(HtmxModelForm):
    hx_post = reverse_lazy("addresses:form-update")  # endpoint HTMX posts to
    hx_target = "#address-fields"                    # element swapped with the response
    hx_indicator = "#form-loading"                   # optional loading indicator
    default_focus_field = "country"                  # field autofocused on first render

    def check_form_state(self):
        """Adjust field state for the current values. Runs on every render."""
        country = self.get_field_value("country")

        if country:
            self.enable_field("region")
            self.set_field_required("region", True)
            self.set_field_queryset("region", Region.objects.filter(country=country))
        else:
            self.disable_field("region")
            self.set_field_required("region", False)

    class Meta:
        model = Address
        fields = ["country", "region"]

        # Changing `country` fires an HTMX request to re-render the form…
        htmx_trigger_fields = ["country"]

        # …and clears `region` so a stale value can't survive the change
        htmx_field_resets = {"country": ["region"]}
```

- **`hx_post` / `hx_target` / `hx_indicator`** — the mixin attaches the matching `hx-post`, `hx-target` and
  `hx-indicator` attributes to each field in `Meta.htmx_trigger_fields`; you don't write them in the template.
- **`htmx_trigger_fields`** — fields whose change re-renders the form.
- **`htmx_field_resets`** — a `{trigger_field: [fields_to_clear]}` map applied before re-rendering.
- **`check_form_state()`** — enable/disable fields, swap choices or querysets, and toggle required state here.
  The view calls it on each update; call it from `__init__` too if you want it applied on the first render.

### View mixin

`HtmxFormUpdateViewMixin` serves the re-rendered partial. It reads the trigger from the `HX-Trigger-Name`
header, applies the resets, calls `check_form_state()`, and rejects non-HTMX requests with a 403.

```python
from django.shortcuts import get_object_or_404

from django_hx_forms.views import HtmxFormUpdateViewMixin

from .forms import AddressForm
from .models import Address


class AddressFormUpdateView(HtmxFormUpdateViewMixin):
    form_class = AddressForm
    template_name = "addresses/_address_fields.html"

    def get_form_instance(self):
        """Return the instance being edited (ModelForms only), or None when adding."""
        address_id = self.request.POST.get("address_id")
        return get_object_or_404(Address, pk=address_id) if address_id else None
```

Route it at the URL named in `hx_post`:

```python
path("form-update/", AddressFormUpdateView.as_view(), name="form-update"),
```

Your ordinary `CreateView` / `UpdateView` reuse the same form and don't need this mixin — they render the
full page, and the update view only handles the reactive refresh.

### Templates

Keep the reactive fields in a partial so the initial page and the HTMX response render identically:

```html
{# addresses/_address_fields.html #}
{{ form.country.label_tag }} {{ form.country }}
{{ form.region.label_tag }} {{ form.region }}
```

The full page wraps that partial in the `hx_target` element (plus the optional `hx_indicator`):

```html
<form method="post">
    {% csrf_token %}
    {% if object %}<input type="hidden" name="address_id" value="{{ object.pk }}">{% endif %}

    <div id="form-loading" class="htmx-indicator">Updating…</div>

    <div id="address-fields">
        {% include "addresses/_address_fields.html" %}
    </div>

    <button type="submit">Save</button>
</form>
```

Changing the `country` field posts to the update view and swaps in a refreshed `#address-fields` fragment
with `region` enabled and re-populated — no page reload and no custom JavaScript. When you render fields by
hand rather than with `{{ form.region }}`, honour the widget attributes the mixin sets (`disabled`,
`autofocus`, `required`).

## What's included

### Forms (`django_hx_forms.forms`)
- **HtmxFormMixin** — trigger/reset handling plus field-state helpers: `get_field_value()`,
  `enable_field()` / `disable_field()` (and `*_fields` plurals), `set_field_required()`,
  `set_field_queryset()`, `set_field_initial()`, `remove_field()`, `add_htmx_field_error()`.
- **HtmxModelForm** — `HtmxFormMixin` combined with Django's `ModelForm`.

### Views (`django_hx_forms.views`)
- **HtmxFormUpdateViewMixin** — renders the form partial on HTMX trigger requests; override
  `get_form_instance()` for ModelForms.
- **IsHtmxRequestMixin** — returns 403 for non-HTMX requests (used by `HtmxFormUpdateViewMixin`).

## Running the demo

A complete working example lives in [`demo/`](demo/) — a shopping cart form where choosing a product type
reveals different fields, updates colour choices, and resets fields that no longer apply. It's a standalone
project that installs this package from the parent directory:

```bash
cd demo
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Then open http://127.0.0.1:8000/. See [`demo/README.md`](demo/README.md) for a fuller walkthrough.

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies (including dev extras)
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg

# Run tests
uv run pytest

# Run type checking
uv run mypy src
```
