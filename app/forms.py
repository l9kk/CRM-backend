from django import forms
from .models import Project, Attachment

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title',
            'description',
            'budget',
            'start_date',
            'end_date',
            'sender_name',
            'contact_email',
            'category',
        ]

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']
