from django import forms
from django.contrib.auth.models import User
from .models import Complaint, FileAttachment, Status, ComplaintType
from core.models import UserProfile


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget for multiple file uploads."""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Custom field for multiple file uploads."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ComplaintForm(forms.ModelForm):
    """Form for creating and editing complaints by regular users."""
    
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif'
        }),
        help_text="You can upload multiple files (PDF, DOC, images). Max 10MB per file."
    )
    
    class Meta:
        model = Complaint
        fields = ['type', 'title', 'description', 'urgency', 'location', 'contact_number']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'title': 'Brief, descriptive title of your issue',
            'description': 'Provide detailed information about the problem',
            'urgency': 'How urgent is this issue?',
            'location': 'Where is the issue occurring? (e.g., Room 101, Lab A)',
            'contact_number': 'Alternative contact number (optional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active complaint types
        self.fields['type'].queryset = ComplaintType.objects.filter(is_active=True)
        
        # Make certain fields required
        self.fields['type'].required = True
        self.fields['title'].required = True
        self.fields['description'].required = True
    
    def clean_attachments(self):
        files = self.files.getlist('attachments')
        
        if files:
            for file in files:
                # Check file size (10MB limit)
                if file.size > 10 * 1024 * 1024:
                    raise forms.ValidationError(f"File '{file.name}' is too large. Maximum size is 10MB.")
                
                # Check file type
                allowed_types = [
                    'application/pdf', 'application/msword', 
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'text/plain', 'image/jpeg', 'image/png', 'image/gif'
                ]
                if file.content_type not in allowed_types:
                    raise forms.ValidationError(f"File type '{file.content_type}' is not allowed.")
        
        return files


class ComplaintUpdateForm(ComplaintForm):
    """Extended form for engineers/admins to update complaints."""
    
    status = forms.ModelChoiceField(
        queryset=Status.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),  # Will be populated in __init__
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label="Unassigned"
    )
    resolution_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False,
        help_text="Notes about the resolution or current progress"
    )
    
    class Meta(ComplaintForm.Meta):
        fields = ComplaintForm.Meta.fields + ['status', 'assigned_to', 'resolution_notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate engineers for assignment
        engineer_profiles = UserProfile.objects.filter(
            role__name__icontains='engineer'
        ).select_related('user')
        
        self.fields['assigned_to'].queryset = User.objects.filter(
            id__in=[p.user.id for p in engineer_profiles]
        )
        
        # Order statuses by their order field
        self.fields['status'].queryset = Status.objects.filter(is_active=True).order_by('order')


class FileAttachmentForm(forms.ModelForm):
    """Form for uploading additional file attachments."""
    
    class Meta:
        model = FileAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File is too large. Maximum size is 10MB.")
            
            # Check file type
            allowed_types = [
                'application/pdf', 'application/msword', 
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain', 'image/jpeg', 'image/png', 'image/gif'
            ]
            if file.content_type not in allowed_types:
                raise forms.ValidationError(f"File type '{file.content_type}' is not allowed.")
        
        return file


class ComplaintFilterForm(forms.Form):
    """Form for filtering complaints in list view."""
    
    status = forms.ModelChoiceField(
        queryset=Status.objects.filter(is_active=True),
        required=False,
        empty_label="All Statuses",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    type = forms.ModelChoiceField(
        queryset=ComplaintType.objects.filter(is_active=True),
        required=False,
        empty_label="All Types",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    urgency = forms.ChoiceField(
        choices=[('', 'All Urgencies')] + Complaint.URGENCY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, description, or ID...'
        })
    )
