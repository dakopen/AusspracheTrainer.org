from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

class RegisterForm(UserCreationForm):
    email = forms.EmailField(label=_("E-Mail"), required=True)    
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
    