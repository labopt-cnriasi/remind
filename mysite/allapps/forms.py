import datetime
from .models import Mission, Mix_unloading
from django import forms

#
# class App1_outputForm(forms.Form):
#     horizon_LB = forms.DateField(label='Data inizio della programmazione')
#     horizon_UB = forms.DateField(label='Data fine della programmazione')


class MissionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields= '__all__'
        
    def clean(self):
        self._validate_unique = True
        cleaned_data = self.cleaned_data
        date = cleaned_data['date']
        today = date.today()
        if date < today:
            raise forms.ValidationError(
                ('data prevista non ammissibile'),
                params={'valore': date},)
        
        
        
        
class MissionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields= '__all__'
        
        def clean(self):
            self._validate_unique = True
            cleaned_data = self.cleaned_data
            date = cleaned_data['date']
            today = date.today()
            if date < today:
                raise forms.ValidationError(
                    ('data prevista non ammissibile'),
                    params={'valore': date},)