from django.forms import ModelForm, Select, ModelChoiceField, NumberInput, CheckboxInput, BooleanField, HiddenInput
from django.core.exceptions import ValidationError
from localflavor.generic.forms import BICFormField, IBANFormField
from captcha.fields import CaptchaField

from wbcore.models import (
    ContactMessage, User, BankAccount, Host, UserRelation, Address
)


class ContactForm(ModelForm):
    # TODO customize field layout via widget and template https://django-simple-captcha.readthedocs.io/en/latest/advanced.html#rendering
    captcha = CaptchaField()
    class Meta:
        model = ContactMessage
        fields = ['host', 'name', 'email', 'reason', 'subject', 'message']
        labels = {
            'host': 'Verein',
            'name': 'Name',
            'email': 'E-Mail',
            'reason': 'Anlass',
            'subject': 'Betreff',
            'message': 'Nachricht'
        }

        required = {
            'host': True,
            'name': False,
            'email': True,
            'reason': False,
            'subject': True,
            'message': True
        }


class BankForm(ModelForm):
    agree = BooleanField(label_suffix="", label="I agree to the terms and conditions")

    class Meta:
        model = BankAccount
        fields = ['account_holder', 'iban', 'bic', 'agree']
        labels = {
            'account_holder': 'Kontoinhaber',
            'iban': 'IBAN',
            'bic': 'BIC',
            'agree': 'I agree to the terms and conditions',
        }
        field_classes={
            'iban': IBANFormField,
            'bic': BICFormField,
        }
        required = {
            'account_holder',
            'iban',
            'bic',
            'agree',
        }


class AddressForm(ModelForm):
    class Meta:
        model = Address

        fields = ['street', 'postal_code', 'city', 'country']

        labels = {
            'street': 'Straße und Hausnummer',
            'postal_code': 'Postleitzahl',
            'city': 'Ort / Stadt',
            'country': 'Land',
        }

        required = {
            'street': True,
            'postal_code': True,
            'city': True,
            'country': True,
        }


class UserRelationForm(ModelForm):

    class Meta:
        model = UserRelation

        fields = ['host', 'membership_fee']

        labels = {
            'host': 'Verein',
            'membership_fee': 'Mitgliedsbeitrag',
        }

        required = {
            'host': True,
            'membership_fee': True,
        }

        widgets = {
            'host': HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['host'].queryset = Host.objects.exclude(slug='bundesverband')


class UserForm(ModelForm):

    class Meta:
        model = User

        fields = ['first_name', 'last_name', 'email', 'date_of_birth']
        labels = {
            'first_name': 'Vorname',
            'last_name': 'Nachname',
            'email': 'E-Mail',
            'date_of_birth': 'Geburtsdatum',
        }

        required = {
            'first_name': True,
            'last_name': True,
            'email': True,
        }

