from django import forms
from django.contrib.auth import get_user_model
from .models import StorePartnerRequest

User = get_user_model()


class StorePartnerRequestForm(forms.ModelForm):
    class Meta:
        model = StorePartnerRequest
        fields = ['first_name', 'last_name', 'store_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'store_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du magasin'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone (optionnel)'}),
        }


class StoreSignupForm(forms.Form):
    store_name = forms.CharField(
        label='Nom du magasin',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du magasin'}),
    )
    address = forms.CharField(
        label='Adresse',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adresse complète'}),
    )
    phone = forms.CharField(
        label='Téléphone',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
    )
    description = forms.CharField(
        label='Description du magasin',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Courte description du magasin'}),
    )
    manager_first_name = forms.CharField(
        label='Prénom du gérant',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
    )
    manager_last_name = forms.CharField(
        label='Nom du gérant',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email professionnel'}),
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}),
    )
    password_confirm = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmez le mot de passe'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', "Cette adresse email est déjà utilisée.")

        return cleaned_data
