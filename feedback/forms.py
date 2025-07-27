from django import forms
from .models import Feedback, FeedbackTemplate


class FeedbackForm(forms.ModelForm):
    """
    Dynamic form for submitting feedback on resolved complaints.
    
    This form adapts based on the selected FeedbackTemplate, allowing for
    flexible feedback collection without hardcoded fields.
    """
    
    class Meta:
        model = Feedback
        fields = ['template', 'comment']
        widgets = {
            'template': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Please share your experience with our IT support...'
            }),
        }
        help_texts = {
            'template': 'Select the type of feedback you want to provide',
            'comment': 'General comments about your experience',
        }
    
    def __init__(self, *args, **kwargs):
        self.complaint = kwargs.pop('complaint', None)
        super().__init__(*args, **kwargs)
        
        # Filter active templates
        self.fields['template'].queryset = FeedbackTemplate.objects.filter(is_active=True)
        
        # Add dynamic fields based on template
        if self.instance and self.instance.template:
            self._add_template_fields(self.instance.template)
        elif 'template' in self.data:
            try:
                template_id = int(self.data['template'])
                template = FeedbackTemplate.objects.get(id=template_id, is_active=True)
                self._add_template_fields(template)
            except (ValueError, FeedbackTemplate.DoesNotExist):
                pass
    
    def _add_template_fields(self, template):
        """Add dynamic fields based on the feedback template."""
        if not isinstance(template.questions, list):
            return
        
        for question in template.questions:
            field_name = question.get('key', '')
            field_type = question.get('type', 'text')
            field_label = question.get('label', '')
            field_required = question.get('required', False)
            
            if not field_name or not field_label:
                continue
            
            if field_type == 'rating':
                self.fields[field_name] = forms.ChoiceField(
                    label=field_label,
                    choices=[('', 'Not rated')] + [(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                    required=field_required,
                    widget=forms.Select(attrs={'class': 'form-select'})
                )
            elif field_type == 'boolean':
                self.fields[field_name] = forms.ChoiceField(
                    label=field_label,
                    choices=[('', 'No preference'), ('true', 'Yes'), ('false', 'No')],
                    required=field_required,
                    widget=forms.Select(attrs={'class': 'form-select'})
                )
            elif field_type == 'textarea':
                self.fields[field_name] = forms.CharField(
                    label=field_label,
                    required=field_required,
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                )
            else:  # text
                self.fields[field_name] = forms.CharField(
                    label=field_label,
                    required=field_required,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                )
    
    def save(self, commit=True):
        feedback = super().save(commit=False)
        
        # Set the complaint if provided
        if self.complaint:
            feedback.complaint = self.complaint
        
        # Build responses dictionary from dynamic fields
        responses = {}
        if feedback.template and isinstance(feedback.template.questions, list):
            for question in feedback.template.questions:
                field_name = question.get('key', '')
                if field_name in self.cleaned_data:
                    value = self.cleaned_data[field_name]
                    # Convert string values to appropriate types
                    if question.get('type') == 'rating' and value:
                        try:
                            responses[field_name] = int(value)
                        except ValueError:
                            pass
                    elif question.get('type') == 'boolean' and value:
                        responses[field_name] = value == 'true'
                    elif value:
                        responses[field_name] = value
        
        feedback.responses = responses
        
        if commit:
            feedback.save()
        
        return feedback


class FeedbackTemplateForm(forms.ModelForm):
    """Form for creating and editing feedback templates."""
    
    class Meta:
        model = FeedbackTemplate
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True