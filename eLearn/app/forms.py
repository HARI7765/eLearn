from django import forms
from .models import Contact
from .models import Course

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'message']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'price', 'image', 'rating', 'instructor']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'border p-2 rounded-full w-full'}),
            'description': forms.Textarea(attrs={'class': 'border p-2 rounded-lg w-full', 'rows': 5}),
            'category': forms.Select(attrs={'class \'1': 'border p-2 rounded-full w-full'}),
            'price': forms.NumberInput(attrs={'class': 'border p-2 rounded-full w-full'}),
            'image': forms.ClearableFileInput(attrs={'class': 'border p-2 rounded w-full'}),
            'rating': forms.NumberInput(attrs={'class': 'border p-2 rounded-full w-full', 'min': 1, 'max': 5}),
            'instructor': forms.TextInput(attrs={'class': 'border p-2 rounded-full w-full'}),
        }