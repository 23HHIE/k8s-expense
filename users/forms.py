from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.core import validators

# a class to define the sign up form
class NewUserForm(UserCreationForm):
    # store a css to a variable
    common_attrs = {'class': 'border-0 focus:outline-none'}
    # defines the email input by using the in-build EmailField and validators
    email = forms.EmailField(required=True,
                            validators=[validators.validate_email],
                            widget=forms.EmailInput(attrs=common_attrs))                            #  
    # define the rule of the validator
    min_length = 2
    max_length = 30
    message_lt_min = f"At least {min_length} characters."
    message_ht_max = f"At most{max_length} characters."
    name_message='The username only accepts letters!'
    
    # define the username input by using CharField method and validators for the validation
    username = forms.CharField(required=True,
                                validators=[
                                            validators.MinLengthValidator(min_length, message_lt_min),
                                            validators.MaxLengthValidator(max_length, message_ht_max),
                                            ],
                                widget=forms.TextInput(attrs=common_attrs))
    # to encrypt passwords input
    password1 = forms.CharField(required=True,
                                widget=forms.PasswordInput(attrs=common_attrs))
    password2 = forms.CharField(required=True,
                                widget=forms.PasswordInput(attrs=common_attrs))
    # define a budget that is not required for users when sign up
    budget = forms.IntegerField(required=False)

    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    # a method for hadnling save the user during sign up
    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


