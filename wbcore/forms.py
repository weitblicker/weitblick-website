from django import forms
from wbcore.models import (
    ContactMessage, User
)


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['host', 'name', 'email', 'reason', 'subject', 'message']
        labels = {'host': 'Verein', 'name': 'Name', 'email':'E-Mail', 'reason': 'Anlass', 'subject': 'Betreff', 'message': 'Nachricht'}
        required = {'host': True, 'name': False, 'email': True, 'reason': False, 'subject': 'Betreff', 'message': 'Nachricht'}


class JoinForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'hosts']
        labels = {
            'hosts': 'Verein',
            'first_name': 'Vorname',
            'last_name': 'Nachname',
            'email': 'E-Mail',
        }
        required = {
            'hosts': True,
            'first_name': True,
            'last_name': True,
            'email': True
        }