from django import forms
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    """Form for submitting feedback on resolved complaints."""
    
    class Meta:
        model = Feedback
        fields = [
            'rating', 'comment', 'resolution_quality', 'response_time', 
            'staff_helpfulness', 'would_recommend', 'suggestions', 
            'is_anonymous', 'is_public'
        ]
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'resolution_quality': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'response_time': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'staff_helpfulness': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'would_recommend': forms.Select(
                choices=[(True, 'Yes'), (False, 'No')],
                attrs={'class': 'form-select'}
            ),
            'suggestions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'rating': 'Overall satisfaction with the complaint resolution',
            'comment': 'Please share your experience with our IT support',
            'resolution_quality': 'How satisfied are you with the quality of the resolution?',
            'response_time': 'How satisfied are you with how quickly we responded?',
            'staff_helpfulness': 'How helpful was our IT staff?',
            'would_recommend': 'Would you recommend our IT support to others?',
            'suggestions': 'Any suggestions for how we can improve our service?',
            'is_anonymous': 'Keep your identity private in this feedback',
            'is_public': 'Allow this feedback to be displayed publicly (testimonials)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make rating required
        self.fields['rating'].required = True
        
        # Add empty labels for optional rating fields
        for field in ['resolution_quality', 'response_time', 'staff_helpfulness']:
            self.fields[field].widget.choices = [('', 'Not rated')] + [
                (i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)
            ]
        
        # Add empty label for would_recommend
        self.fields['would_recommend'].widget.choices = [('', 'No preference')] + [
            (True, 'Yes'), (False, 'No')
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        
        # If making feedback public, it cannot be anonymous
        if cleaned_data.get('is_public') and cleaned_data.get('is_anonymous'):
            raise forms.ValidationError(
                "Feedback cannot be both public and anonymous. "
                "Please choose one option."
            )
        
        return cleaned_data