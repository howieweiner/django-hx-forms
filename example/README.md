# Django HX Forms - Example Project

This is a demonstration project showcasing the capabilities of `django-hx-forms` with a shopping cart product example.

## Features

This demo includes:

- **Product List View**: Display all products in a table
- **Product Create View**: Create new products with reactive form fields
- **Product Update View**: Edit existing products with the same reactive behavior
- **Product Delete View**: Delete products with confirmation

## Reactive Form Behaviour

The product form demonstrates reactive field updates based on product type:

### T-Shirts
- **Size**: S/M/L (enabled)
- **Waist Size**: Hidden/disabled
- **Colour**: Black/White

### Trousers
- **Size**: Hidden/disabled
- **Waist Size**: 28-42 (enabled)
- **Colour**: Black/Blue/Brown

When you change the product type, the form automatically:
- Enables/disables relevant fields
- Updates colour choices
- Resets previously selected values for non-applicable fields
- Updates field requirements

All of this happens without a page refresh, using HTMX!

## Running the Demo

### Prerequisites

Make sure you have Python 3.10+ installed.

### Setup

1. Navigate to the example directory:
   ```bash
   cd example
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. (Optional) Create a superuser to access the admin:
   ```bash
   python manage.py createsuperuser
   ```

5. Run the development server:
   ```bash
   python manage.py runserver
   ```

6. Open your browser and navigate to:
   - Main app: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## Project Structure

```
example/
├── config/                 # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── shopping_cart/          # Demo application
│   ├── templates/
│   │   ├── base.html
│   │   └── shopping_cart/
│   │       ├── product_list.html
│   │       ├── product_form.html
│   │       ├── product_confirm_delete.html
│   │       └── partials/
│   │           └── product_form_fields.html  # HTMX partial
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py            # ProductForm using HtmxModelForm
│   ├── models.py           # Product model
│   ├── urls.py
│   └── views.py
├── manage.py
├── requirements.txt
└── README.md
```

## How It Works

### The Form (`shopping_cart/forms.py`)

The `ProductForm` extends `HtmxModelForm` and configures:

- **HTMX trigger fields**: The `type` field triggers form updates
- **Field resets**: When type changes, size/waist_size/colour are reset
- **Dynamic state management**: The `check_form_state()` method enables/disables fields based on the selected type

### The View (`shopping_cart/views.py`)

The `product_form_update` view handles HTMX requests:

1. Receives POST data from the form
2. Identifies which field triggered the update
3. Creates a new form instance with `htmx_data` and `trigger_field`
4. Returns only the updated form fields (partial template)

### The Template

The form template uses:

- HTMX attributes configured by the form mixin
- A partial template (`product_form_fields.html`) that gets swapped on updates
- Bootstrap for styling

## Learning Points

This example demonstrates:

1. **Zero JavaScript**: All reactivity is handled by HTMX and server-side logic
2. **Clean separation**: Business logic stays in the form class
3. **Reusable patterns**: The same form works for both create and update views
4. **Progressive enhancement**: The form works without JavaScript, but enhances with HTMX

## Customization

You can extend this example by:

- Adding more product types
- Adding more dependent fields
- Implementing inline editing in the list view
- Adding real-time validation
- Implementing search and filtering with HTMX
