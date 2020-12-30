from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Trader
from django.contrib.auth import authenticate

class RegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=60, help_text="Required. Add a valid email address")

    class Meta:
        model = Trader
        fields = ["email", "username", "password1", "password2"]

class TraderAuthenticationForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = Trader
        fields = ["username", "password"]
    
    def clean(self):
        username = self.cleaned_data["username"]
        password = self.cleaned_data["password"]
        if not authenticate(username=username, password=password):
            raise forms.ValidationError("Invalid login")
