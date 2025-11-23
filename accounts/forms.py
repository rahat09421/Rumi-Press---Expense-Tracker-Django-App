from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model


def validate_strong_password(value: str):
    if len(value) < 12:
        raise ValidationError("Password must be at least 12 characters long.")
    if not re.search(r"[A-Z]", value):
        raise ValidationError("Password must include an uppercase letter.")
    if not re.search(r"[a-z]", value):
        raise ValidationError("Password must include a lowercase letter.")
    if not re.search(r"\d", value):
        raise ValidationError("Password must include a digit.")
    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValidationError("Password must include a symbol.")


class AdminCreationForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, validators=[validate_strong_password])
    password2 = forms.CharField(widget=forms.PasswordInput)
    is_active = forms.ChoiceField(choices=[('true','Active'),('false','Inactive')], initial='true', widget=forms.RadioSelect, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Confirm Password'
        for name, field in self.fields.items():
            widget = field.widget
            existing = widget.attrs.get('class', '')
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs['class'] = f"{existing} form-select".strip()
            else:
                widget.attrs['class'] = f"{existing} form-control".strip()
            # placeholders for a modern look
            if name == 'username':
                widget.attrs.setdefault('placeholder', 'Username')
                widget.attrs.setdefault('autocomplete', 'username')
            elif name == 'email':
                widget.attrs.setdefault('placeholder', 'Email')
                widget.attrs.setdefault('autocomplete', 'email')
            elif name == 'password1':
                widget.attrs.setdefault('placeholder', 'Password')
                widget.attrs.setdefault('autocomplete', 'new-password')
            elif name == 'password2':
                widget.attrs.setdefault('placeholder', 'Confirm Password')
                widget.attrs.setdefault('autocomplete', 'new-password')
            elif name == 'is_active':
                # radio group shouldn't have form-control
                widget.attrs['class'] = ''

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        return cleaned

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            is_staff=True,
        )
        # set active state from form
        active_val = self.cleaned_data.get('is_active') or 'true'
        user.is_active = (active_val == 'true')
        user.save()
        group, _ = Group.objects.get_or_create(name="Admin")
        user.groups.add(group)
        return user


class SuperuserBootstrapForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, validators=[validate_strong_password])
    password2 = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Confirm Password'
        for name, field in self.fields.items():
            widget = field.widget
            existing = widget.attrs.get('class', '')
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs['class'] = f"{existing} form-select".strip()
            else:
                widget.attrs['class'] = f"{existing} form-control".strip()
            if name == 'username':
                widget.attrs.setdefault('placeholder', 'Username')
                widget.attrs.setdefault('autocomplete', 'username')
            elif name == 'email':
                widget.attrs.setdefault('placeholder', 'Email')
                widget.attrs.setdefault('autocomplete', 'email')
            elif name == 'password1':
                widget.attrs.setdefault('placeholder', 'Password')
                widget.attrs.setdefault('autocomplete', 'new-password')
            elif name == 'password2':
                widget.attrs.setdefault('placeholder', 'Confirm Password')
                widget.attrs.setdefault('autocomplete', 'new-password')

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        return cleaned

    def save(self):
        return User.objects.create_superuser(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )


class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.data.get('username') or self.cleaned_data.get('username')
        if username:
            UserModel = get_user_model()
            try:
                u = UserModel.objects.get(username=username)
                if not u.is_active:
                    raise ValidationError(
                        "Your account has been deactivated by the Superadmin.",
                        code="inactive",
                    )
            except UserModel.DoesNotExist:
                pass
        return super().clean()