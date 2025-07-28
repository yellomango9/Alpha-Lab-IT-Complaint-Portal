from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from .models import UserProfile, Department


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information."""
    
    # User fields
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'department', 'phone_number', 'main_portal_id', 'email_notifications'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'main_portal_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate user fields if instance exists
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        # Filter active departments
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update user fields
        if profile.user:
            profile.user.first_name = self.cleaned_data.get('first_name', '')
            profile.user.last_name = self.cleaned_data.get('last_name', '')
            profile.user.email = self.cleaned_data.get('email', '')
            if commit:
                profile.user.save()
        
        if commit:
            profile.save()
        
        return profile


class UserRegistrationForm(forms.ModelForm):
    """Form for user registration with profile information."""
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    main_portal_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Unique ID from the main Alpha Labs portal for SSO"
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return password2
    
    def clean_main_portal_id(self):
        main_portal_id = self.cleaned_data.get('main_portal_id')
        if main_portal_id and UserProfile.objects.filter(main_portal_id=main_portal_id).exists():
            raise forms.ValidationError("This portal ID is already in use.")
        return main_portal_id
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        
        if commit:
            user.save()
            # Create profile
            UserProfile.objects.create(
                user=user,
                department=self.cleaned_data['department'],
                main_portal_id=self.cleaned_data.get('main_portal_id', '')
            )
        
        return user


class NormalUserLoginForm(forms.Form):
    """Form for normal user login using name and main_portal_id."""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'required': True
        }),
        help_text="Your full name as registered in the main portal"
    )
    
    main_portal_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your portal ID',
            'required': True
        }),
        help_text="Your unique ID from the main Alpha Labs portal"
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        help_text="Select your department"
    )
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError("Name is required.")
        if len(name) < 2:
            raise ValidationError("Name must be at least 2 characters long.")
        return name
    
    def clean_main_portal_id(self):
        portal_id = self.cleaned_data.get('main_portal_id', '').strip()
        
        if not portal_id:
            raise ValidationError("Portal ID is required.")
        
        # Simple format validation: alphanumeric characters only
        if not re.match(r'^[a-zA-Z0-9]+$', portal_id):
            raise ValidationError("Portal ID can only contain letters and numbers.")
        
        if len(portal_id) < 3:
            raise ValidationError("Portal ID must be at least 3 characters long.")
        
        return portal_id