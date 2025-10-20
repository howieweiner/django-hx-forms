# django-hx-forms

[![PyPI version](https://badge.fury.io/py/django-htmx-tools.svg)](https://badge.fury.io/py/django-htmx-tools)
[![Python versions](https://img.shields.io/pypi/pyversions/django-htmx-tools.svg)](https://pypi.org/project/django-hx-forms/)
[![Django versions](https://img.shields.io/pypi/djversions/django-htmx-tools.svg)](https://pypi.org/project/django-hx-forms/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/django-htmx-tools/badge/?version=latest)](https://django-hx-forms.readthedocs.io/en/latest/?badge=latest)

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

## Documentation

Please visit [https://django-hx-forms.readthedocs.io](https://django-hx-forms.readthedocs.io)
