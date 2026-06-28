from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "placeholder": "you@example.com",
            "class": "auth-input",
            "autocomplete": "email",
        })
    )
    display_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "How should we call you?",
            "class": "auth-input",
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "class": "auth-input",
        })
    )

    class Meta:
        model  = User
        fields = ("username", "display_name", "email", "profile_picture", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username":  "Pick a unique username",
            "password1": "Create a password",
            "password2": "Repeat the password",
        }
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "auth-input")
            field.widget.attrs["autocomplete"] = "off"
            field.help_text = ""
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username", "").lower()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email        = self.cleaned_data["email"]
        user.display_name = self.cleaned_data.get("display_name") or self.cleaned_data["username"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class":        "auth-input",
            "placeholder":  "Username",
            "autocomplete": "username",
        })
        self.fields["password"].widget.attrs.update({
            "class":        "auth-input",
            "placeholder":  "Password",
            "autocomplete": "current-password",
        })
        self.fields["username"].help_text = ""
        self.fields["password"].help_text = ""
