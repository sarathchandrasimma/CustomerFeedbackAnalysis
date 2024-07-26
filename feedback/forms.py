from django import forms

class FeedbackForm(forms.Form):
    file = forms.FileField(
        label='Upload CSV File',
        max_length=100,  # You can specify a max length for the filename
        help_text='Max size: 10 MB. Accepted file type: .csv',
        required=True
    )
