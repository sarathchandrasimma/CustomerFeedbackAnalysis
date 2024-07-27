from django import forms

class FeedbackForm(forms.Form):
    file = forms.FileField(label='Upload CSV', help_text='Upload a CSV file containing feedback.')
