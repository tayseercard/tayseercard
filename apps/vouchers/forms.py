from django import forms
from .models import VoucherRequest, Voucher, VoucherPrice

class VoucherRequestForm(forms.ModelForm):
    class Meta:
        model = VoucherRequest
        fields = ['price_template', 'quantity']
        widgets = {
            'price_template': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_price_template',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'id': 'id_quantity',
            }),
        }
        labels = {
            'price_template': 'Modèle de voucher (Valeur / Prix)',
            'quantity': 'Quantité',
            'expires_at': 'Date d\'expiration',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active price templates
        self.fields['price_template'].queryset = self.fields['price_template'].queryset.filter(is_active=True)


class VoucherFillForm(forms.ModelForm):
    class Meta:
        model = Voucher
        fields = ['customer_name', 'beneficiary_name', 'customer_phone', 'value', 'pin_code']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom complet'}),
            'beneficiary_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optionnel'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0x xx xx xx xx'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pin_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1234 (Optionnel)'}),
        }
        labels = {
            'customer_name': 'Nom de l\'acheteur',
            'beneficiary_name': 'Bénéficiaire',
            'customer_phone': 'Téléphone',
            'value': 'Montant (DA)',
            'pin_code': 'Code PIN de sécurité',
        }


class VoucherPriceForm(forms.ModelForm):
    class Meta:
        model = VoucherPrice
        fields = ['title', 'value', 'price', 'pack_quantity', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Pack Bronze'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pack_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'Titre du pack',
            'value': 'Valeur d\'un voucher (DA)',
            'price': 'Prix de vente du pack (DA)',
            'pack_quantity': 'Nombre de vouchers',
            'is_active': 'Est actif',
        }