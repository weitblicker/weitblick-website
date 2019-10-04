from django.forms import ModelForm, Select, ModelChoiceField
from django.core.exceptions import ValidationError
from localflavor.generic.forms import BICFormField, IBANFormField

from wbcore.models import (
    ContactMessage, User, BankAccount, Host
)


class ContactForm(ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['host', 'name', 'email', 'reason', 'subject', 'message']
        labels = {'host': 'Verein', 'name': 'Name', 'email':'E-Mail', 'reason': 'Anlass', 'subject': 'Betreff', 'message': 'Nachricht'}
        required = {'host': True, 'name': False, 'email': True, 'reason': False, 'subject': 'Betreff', 'message': 'Nachricht'}


class BankForm(ModelForm):
    class Meta:
        model = BankAccount
        fields = ['account_holder', 'iban', 'bic']
        labels = {
            'account_holder': 'Kontoinhaber',
            'iban': 'IBAN',
            'bic': 'BIC',
        }
        field_classes={
            'iban': IBANFormField,
            'bic': BICFormField,
        }
        required = {
            'account_holder',
            'iban',
            'bic',
        }


class UserForm(ModelForm):

    host = ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['host'].queryset = Host.objects.exclude(slug='bundesverband')

    class Meta:
        model = User

        fields = ['first_name', 'last_name', 'email', 'host']
        labels = {
            'host': 'Verein',
            'first_name': 'Vorname',
            'last_name': 'Nachname',
            'email': 'E-Mail',
        }

        #widgets = {
        #    'host': Select(attrs={'class': 'ui dropdown'}),
        #}
        required = {
            'host': True,
            'first_name': True,
            'last_name': True,
            'email': True,
        }

    def _clean_fields(self):
        print("huhu")
        super()._clean_fields()

    def clean(self):
        try:
            super().clean()
        except ValidationError as e:
            print("exception", e)
            raise e


