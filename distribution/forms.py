# distribution/forms.py
from django import forms
from .models import Category, Book

# ---------- Helper to apply Bootstrap classes ----------
def add_bootstrap_classes(form):
    """
    Adds Bootstrap classes automatically to all form fields.
    """
    for field_name, field in form.fields.items():
        widget = field.widget
        # Skip checkboxes and files
        if isinstance(widget, (forms.CheckboxInput, forms.ClearableFileInput, forms.FileInput)):
            continue

        # Add Bootstrap classes
        existing_classes = widget.attrs.get('class', '')
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs['class'] = f'{existing_classes} form-select'.strip()
        else:
            widget.attrs['class'] = f'{existing_classes} form-control'.strip()

        if form.is_bound and form[field_name].errors:
            widget.attrs['class'] = f"{widget.attrs.get('class','')} is-invalid".strip()

        # For date inputs
        if isinstance(widget, forms.DateInput):
            widget.attrs.setdefault('type', 'date')


# ---------- Category Form ----------
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)


# ---------- Book Form ----------
class BookForm(forms.ModelForm):
    publishing_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
    )

    class Meta:
        model = Book
        fields = [
            'source_id',
            'title',
            'subtitle',
            'author',
            'publisher',
            'publishing_date',
            'category',
            'distribution_expenses',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)


# ---------- Upload Books Form ----------
class UploadBooksForm(forms.Form):
    file = forms.FileField(
        label='Choose an Excel (.xlsx/.xls) or CSV file',
        help_text='Expected headers: id, title, subtitle, authors, publisher, published_date, category, distribution_expense'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap_classes(self)
