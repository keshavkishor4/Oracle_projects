from django import forms

class podform(forms.Form):
    # podname = forms.CharField(label="POD NAME",widget=forms.TextInput(attrs=))
    pod_name = forms.CharField(widget=forms.TextInput(attrs={'type':'text','class':"form-control",'padding-top': "10px"}))
    start_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local','class':"form-control",'padding-top': "10px"}))
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local','class':"form-control",'padding-top': "10px"}))
    # endtimedjango = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))