# forms.py
from django import forms
from .models import Oci_questionnaire, Dass_questionnaire, Aaq_questionnaire
import pdb
from django.db.models.signals import post_save
from django.dispatch import receiver

class Oci_questionnaire_form(forms.ModelForm):
    class Meta:
        model = Oci_questionnaire
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        handle_fields(self.fields, self.Meta.model)                        
class Dass_questionnaire_form(forms.ModelForm):
    class Meta:
        model = Dass_questionnaire
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        handle_fields(self.fields, self.Meta.model)

class Aaq_questionnaire_form(forms.ModelForm):
    class Meta:
        model = Aaq_questionnaire
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        handle_fields(self.fields, self.Meta.model)
                
def handle_fields(fields, model):    
    for field_name, field in fields.items():        
        if field_name.startswith('question_'):
            field.widget = forms.RadioSelect(attrs={'class':'some_class'})
            field.choices = model.STATEMENT_CHOICES
            field.label = model.questions[field_name]
            field.initial = 0
            field.required = True
        elif field_name in ['subject_id', 'subject_uuid']:
            field.widget = forms.HiddenInput()
            field.label = ""
            field.initial="defaultUser"
            field.required = True

