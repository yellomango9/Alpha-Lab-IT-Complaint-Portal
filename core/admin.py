from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Department, Role, UserProfile


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


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin configuration for Role model."""
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'classes': ('collapse',)
        }),
    )


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    
    fieldsets = (
        ('Profile Information', {
            'fields': ('department', 'role', 'employee_id', 'phone_number')
        }),
        ('Personal Details', {
            'fields': ('avatar', 'bio'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('email_notifications',),
            'classes': ('collapse',)
        }),
    )


class CustomUserAdmin(UserAdmin):
    """Extended UserAdmin with UserProfile inline."""
    inlines = (UserProfileInline,)
    
    list_display = UserAdmin.list_display + ('get_department', 'get_role')
    list_filter = UserAdmin.list_filter + ('profile__department', 'profile__role')
    
    def get_department(self, obj):
        return obj.profile.department if hasattr(obj, 'profile') and obj.profile.department else '-'
    get_department.short_description = 'Department'
    
    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') and obj.profile.role else '-'
    get_role.short_description = 'Role'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model."""
    list_display = ['user', 'department', 'role', 'employee_id', 'created_at']
    list_filter = ['department', 'role', 'email_notifications', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']
    ordering = ['user__username']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Profile Information', {
            'fields': ('department', 'role', 'employee_id', 'phone_number')
        }),
        ('Personal Details', {
            'fields': ('avatar', 'bio'),
            'classes': ('collapse',)
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
admin.site.site_header = 'Alpha Lab IT Complaint Portal Admin'
admin.site.site_title = 'Alpha Lab IT Portal'
admin.site.index_title = 'Administration'
