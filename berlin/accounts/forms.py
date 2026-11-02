from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import CustomerProfile

User = get_user_model()

FORM_CONTROL = 'w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm'


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=32, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = FORM_CONTROL

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User._default_manager.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            CustomerProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', ''),
            )
            self.save_m2m()
        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()

    class Meta:
        model = CustomerProfile
        fields = (
            'phone',
            'address_line_1',
            'address_line_2',
            'city',
            'region',
            'postal_code',
            'country',
        )
        widgets = {
            'address_line_1': forms.TextInput(attrs={'autocomplete': 'address-line1'}),
            'address_line_2': forms.TextInput(attrs={'autocomplete': 'address-line2'}),
            'city': forms.TextInput(attrs={'autocomplete': 'address-level2'}),
            'region': forms.TextInput(attrs={'autocomplete': 'address-level1'}),
            'postal_code': forms.TextInput(attrs={'autocomplete': 'postal-code'}),
            'country': forms.TextInput(attrs={'autocomplete': 'country-name'}),
            'phone': forms.TextInput(attrs={'autocomplete': 'tel'}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email
        for field in self.fields.values():
            field.widget.attrs['class'] = FORM_CONTROL

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if (
            User._default_manager.filter(email__iexact=email)
            .exclude(pk=self.user.pk)
            .exists()
        ):
            raise forms.ValidationError('An account with this email address already exists.')
        return email

    @transaction.atomic
    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            self.user.save(update_fields=['first_name', 'last_name', 'email'])
        return profile
