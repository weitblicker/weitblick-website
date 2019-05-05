from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['host', 'name', 'email', 'reason', 'subject', 'message']
        labels = {'host': 'Stadt', 'name': 'Name', 'email':'E-Mail', 'reason': 'Anlass', 'subject': 'Betreff', 'message': 'Nachricht'}
        required = {'host': True, 'name': False, 'email': True, 'reason': False, 'subject': 'Betreff', 'message': 'Nachricht'}
