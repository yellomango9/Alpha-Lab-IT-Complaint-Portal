# 👥 Admin User Management Guide

## Overview

This guide explains how to properly manage users in the Alpha Lab IT Portal admin interface, including group assignments for portal access control.

## ✅ **ISSUES FIXED**

### 1. **IntegrityError with UserProfile**

- **Problem**: Duplicate UserProfile creation causing database errors
- **Solution**: Fixed signal handlers to use `get_or_create()` instead of `create()`
- **Status**: ✅ **RESOLVED**

### 2. **Missing Groups Field in Admin**

- **Problem**: Groups field not prominently displayed in user admin
- **Solution**: Enhanced CustomUserAdmin with dedicated "Portal Access Control" section
- **Status**: ✅ **RESOLVED**

## 🔐 **Portal Access Control**

### **Required Groups for Login**

Only users assigned to these groups can log into the portal:

| Group         | Access Level      | Description                        |
| ------------- | ----------------- | ---------------------------------- |
| **Admin**     | 🔑 Full Access    | Complete system administration     |
| **AMC Admin** | 🔧 Administrative | AMC-specific administrative access |
| **Engineer**  | ⚙️ Engineering    | Technical complaint handling       |

### **⚠️ IMPORTANT**

Users **WITHOUT** these groups **CANNOT** log into the portal!

## 📋 **How to Add Users with Groups**

### **Method 1: Django Admin Interface**

1. **Access Admin**: Go to `http://127.0.0.1:8000/admin/`
2. **Navigate to Users**: Click "Users" under "Authentication and Authorization"
3. **Add User**: Click "Add User" button
4. **Fill Basic Info**:
   - Username (required)
   - Password (required)
5. **Save and Continue**: Click "Save and continue editing"
6. **Assign Groups**:
   - Scroll to "Portal Access Control" section
   - Select appropriate group(s): Admin, AMC Admin, or Engineer
   - **This step is CRITICAL for portal access**
7. **Fill Additional Info** (optional):
   - First name, Last name, Email
   - Department (in Profile section)
8. **Save**: Click "Save"

### **Method 2: Management Commands**

```bash
# Create groups (if not already created)
python manage.py setup_groups

# Create test users with groups
python manage.py setup_groups --create-test-users

# Fix any profile issues
python manage.py fix_user_profiles

# Assign Admin group to superusers
python manage.py assign_superuser_groups
```

## 🎯 **Admin Interface Enhancements**

### **Enhanced User List View**

- **Department**: Shows user's department
- **Groups**: Shows assigned groups
- **Portal Access**: Visual indicator of access level
  - 🔑 Admin
  - 🔧 AMC Admin
  - ⚙️ Engineer
  - 🚫 No Access

### **Enhanced User Edit Form**

- **Portal Access Control Section**: Prominently displays group assignment
- **Visual Status Indicators**: Shows current access level with badges
- **Helpful Descriptions**: Explains what each group provides
- **Warning Messages**: Alerts when users have no portal access

### **Group Assignment Interface**

- **Clear Labeling**: "Portal Access Control" section
- **Group Descriptions**: Explains each group's purpose
- **Visual Feedback**: Color-coded badges for different access levels

## 🔧 **Troubleshooting**

### **User Cannot Log In**

1. **Check Groups**: Ensure user has Admin, AMC Admin, or Engineer group
2. **Check Active Status**: User must be active (`is_active = True`)
3. **Check Password**: Verify password is set correctly

### **IntegrityError When Adding Users**

1. **Run Fix Command**: `python manage.py fix_user_profiles`
2. **Check for Duplicates**: The command will identify and fix issues
3. **Try Again**: Add user after running the fix

### **Groups Not Visible**

1. **Check Admin Config**: Ensure CustomUserAdmin is properly registered
2. **Clear Cache**: Restart Django server
3. **Check Permissions**: Ensure you have superuser access

## 📊 **Monitoring User Access**

### **Check Current Status**

```bash
# View all users and their groups
python manage.py fix_user_profiles

# This will show:
# - Users without profiles
# - Group assignments
# - Users without portal access
```

### **Admin Dashboard Indicators**

- **User List**: Shows group assignments and access levels
- **Color Coding**: Visual indicators for different access types
- **Warning Badges**: Highlights users without portal access

## 🚀 **Best Practices**

### **When Adding New Users**

1. ✅ **Always assign a group** (Admin, AMC Admin, or Engineer)
2. ✅ **Set appropriate department** in profile
3. ✅ **Verify email address** for notifications
4. ✅ **Test login** after creation

### **Security Considerations**

1. 🔒 **Principle of Least Privilege**: Assign minimum required access
2. 🔒 **Regular Review**: Periodically review user access levels
3. 🔒 **Remove Unused Accounts**: Deactivate accounts for departed staff
4. 🔒 **Strong Passwords**: Enforce password policies

### **Group Assignment Guidelines**

- **Admin**: Only for system administrators
- **AMC Admin**: For AMC department administrators
- **Engineer**: For technical staff handling complaints
- **Multiple Groups**: Users can have multiple groups if needed

## 📋 **Quick Reference Commands**

```bash
# Setup initial groups and test users
python manage.py setup_groups --create-test-users

# Fix any UserProfile issues
python manage.py fix_user_profiles

# Assign groups to superusers
python manage.py assign_superuser_groups

# Check system status
python manage.py fix_user_profiles --dry-run
```

## ✅ **Verification Checklist**

After adding a new user, verify:

- [ ] User has appropriate group assigned
- [ ] User can log in at `/login/`
- [ ] User sees appropriate dashboard
- [ ] UserProfile exists without errors
- [ ] Department is set (if applicable)

---

## 🎉 **SUMMARY**

The user management system now provides:

- ✅ **Clear group assignment interface** in Django Admin
- ✅ **Visual indicators** for portal access levels
- ✅ **Robust error handling** for UserProfile creation
- ✅ **Comprehensive management commands** for maintenance
- ✅ **Enhanced admin interface** with helpful guidance

Users can now be easily added with proper group assignments, ensuring secure and controlled access to the Alpha Lab IT Portal.
