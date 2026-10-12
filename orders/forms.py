import re

from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=128, error_messages={'required': "Ism va familyangizni kiriting."})
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=20, error_messages={'required': "Telefon raqamingizni kiriting."})
    address = forms.CharField(max_length=255, required=False, error_messages={'required': "Yetkazib berish punktini tanlang."})

    def __init__(self, *args, require_address=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.require_address = require_address

    def clean_address(self):
        value = (self.cleaned_data.get('address') or '').strip()
        if self.require_address and not value:
            raise forms.ValidationError("Yetkazib berish punktini tanlang.")
        return value or "Raqamli buyurtma (yetkazib berish shart emas)"

    def clean_full_name(self):
        value = ' '.join(self.cleaned_data['full_name'].split())
        if len(value) < 3:
            raise forms.ValidationError("Ism va familyangizni to'liq kiriting.")
        return value

    def clean_phone_number(self):
        digits = re.sub(r'\D', '', self.cleaned_data['phone_number'])
        if len(digits) == 9:
            digits = '998' + digits
        if not (len(digits) == 12 and digits.startswith('998')):
            raise forms.ValidationError("Telefon raqamni to'g'ri kiriting. Masalan: +998 90 123 45 67")
        return '+' + digits


class PaymentForm(forms.Form):
    payment_receipt = forms.ImageField(
        label="Mahsulot to'lov cheki",
        error_messages={'required': "To'lov chekining rasmini yuklang."},
    )
    post_receipt = forms.ImageField(
        label="Pochta to'lov cheki",
        required=False,
    )

    def __init__(self, *args, require_post_receipt=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.require_post_receipt = require_post_receipt
        if require_post_receipt:
            self.fields['post_receipt'].required = True
            self.fields['post_receipt'].error_messages['required'] = (
                "UZPOST uchun pochta to'lovi chekini ham yuklang."
            )
