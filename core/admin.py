from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import Department, UserProfile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin configuration for Department model."""
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
    )





class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0  # Don't show extra empty forms
    max_num = 1  # Only allow one profile per user
    
    fieldsets = (
        ('Profile Information', {
            'fields': ('department', 'phone_number', 'main_portal_id'),
            'description': 'Phone number and Main Portal ID are optional fields.'
        }),
        ('Preferences', {
            'fields': ('email_notifications',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Ensure we only get the profile for this user."""
        qs = super().get_queryset(request)
        return qs.select_related('user')


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with group selection."""
    groups = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('Groups', False),
        help_text='Select groups for portal access: Admin, AMC Admin, or Engineer'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import Group
        # Only show the portal access groups
        self.fields['groups'].queryset = Group.objects.filter(
            name__in=['Admin', 'AMC Admin', 'Engineer']
        )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Ensure profile is created
            UserProfile.objects.get_or_create(user=user)
            # Add groups
            if self.cleaned_data.get('groups'):
                user.groups.set(self.cleaned_data['groups'])
        return user


class CustomUserAdmin(UserAdmin):
    """Extended UserAdmin with enhanced group management and safe profile creation."""
    form = UserChangeForm
    add_form = CustomUserCreationForm
    # Temporarily remove inline to prevent conflicts
    # inlines = (UserProfileInline,)
    
    list_display = UserAdmin.list_display + ('get_department', 'get_groups', 'get_access_level')
    list_filter = UserAdmin.list_filter + ('profile__department', 'groups')
    
    # Customize the fieldsets to make Groups more prominent
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        ('Portal Access Control', {
            'fields': ('groups',),
            'description': 'Assign user to groups: Admin, AMC Admin, or Engineer for portal access.',
            'classes': ('wide',)
        }),
        ('Advanced Permissions', {
            'fields': ('user_permissions',),
            'classes': ('collapse',)
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Customize add form fieldsets
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Portal Access Control', {
            'classes': ('wide',),
            'fields': ('groups',),
            'description': 'Select groups for portal access: Admin, AMC Admin, or Engineer. Users without these groups cannot log in.'
        }),
    )
    
    def get_department(self, obj):
        return obj.profile.department if hasattr(obj, 'profile') and obj.profile.department else '-'
    get_department.short_description = 'Department'
    
    def get_groups(self, obj):
        groups = [group.name for group in obj.groups.all()]
        if groups:
            return ", ".join(groups)
        return '⚠️ No Groups'
    get_groups.short_description = 'Groups'
    
    def get_access_level(self, obj):
        """Show access level based on groups."""
        groups = [group.name for group in obj.groups.all()]
        if 'Admin' in groups:
            return '🔑 Admin'
        elif 'AMC Admin' in groups:
            return '🔧 AMC Admin'
        elif 'Engineer' in groups:
            return '⚙️ Engineer'
        else:
            return '🚫 No Access'
    get_access_level.short_description = 'Portal Access'
    
    def save_model(self, request, obj, form, change):
        """Custom save method to handle profile creation safely."""
        # Save the user first
        super().save_model(request, obj, form, change)
        
        # For new users, ensure profile exists
        if not change:  # This is a new user
            try:
                # Always create profile for new users (signal is disabled)
                profile, created = UserProfile.objects.get_or_create(user=obj)
                if created:
                    print(f"✅ Created profile for new user: {obj.username}")
                else:
                    print(f"ℹ️  Profile already exists for user: {obj.username}")
            except Exception as e:
                # Log error but don't break the save
                print(f"❌ Error creating profile for user {obj.username}: {e}")
                # Try to handle the error gracefully
                try:
                    # Check if profile exists without creating
                    existing_profile = UserProfile.objects.filter(user=obj).first()
                    if not existing_profile:
                        # Force create with explicit handling
                        profile = UserProfile(user=obj)
                        profile.save()
                        print(f"✅ Force-created profile for user: {obj.username}")
                except Exception as e2:
                    print(f"❌ Failed to force-create profile: {e2}")
    
    def save_formset(self, request, form, formset, change):
        """Custom save formset to handle inline profile creation."""
        # For new users, the profile should already exist from save_model
        # So this should be safe
        try:
            super().save_formset(request, form, formset, change)
        except Exception as e:
            # If there's still an error, log it but don't break
            print(f"Error saving formset: {e}")
            # The user is already saved, so this is not critical


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model."""
    list_display = ['user', 'department', 'main_portal_id', 'created_at']
    list_filter = ['department', 'email_notifications', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'main_portal_id']
    ordering = ['user__username']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Profile Information', {
            'fields': ('department', 'phone_number', 'main_portal_id'),
            'description': 'Phone number and Main Portal ID are optional fields.'
        }),
        ('Preferences', {
            'fields': ('email_notifications',),
            'classes': ('collapse',)
        }),
    )


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize admin site headers
admin.site.site_header = 'AMC Complaint Portal Admin'
admin.site.site_title = 'AMC Portal'
admin.site.index_title = 'Administration'
