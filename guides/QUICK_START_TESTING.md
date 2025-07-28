# 🚀 Quick Start Testing Guide

## ⚡ 1-Minute Setup

### Step 1: Start the Server
```bash
cd /home/user/projects/Alpha-Lab-IT-Complaint-Portal
python manage.py runserver
```

### Step 2: Open Browser
Navigate to: **http://localhost:8000**

---

## 🧪 Instant Test Links

### 🔐 Login Portals

#### Staff Login Portal
**URL**: http://localhost:8000/login/
```
👤 Admin: demo_admin / demo123
👤 AMC Admin: demo_amc_admin / demo123  
👤 Engineer: demo_engineer1 / demo123
👤 Engineer: demo_engineer2 / demo123
```

#### Normal User Login Portal  
**URL**: http://localhost:8000/core/user/login/
```
👤 Alice Johnson - Portal ID: ALICE001
👤 Bob Smith - Portal ID: BOB002
👤 Carol Davis - Portal ID: CAROL003
```

---

## 🎯 Key Testing URLs

### Normal User Features
- **Login**: http://localhost:8000/core/user/login/
- **Dashboard**: http://localhost:8000/core/dashboard/
- **Submit Complaint**: http://localhost:8000/complaints/submit/

### Engineer Features
- **Dashboard**: http://localhost:8000/engineer/
- **All Complaints**: http://localhost:8000/engineer/
- **Assigned Complaints**: http://localhost:8000/engineer/ (Assigned tab)

### AMC Admin Features
- **Dashboard**: http://localhost:8000/amc-admin/
- **Complaint Management**: http://localhost:8000/amc-admin/
- **Issues Tab**: http://localhost:8000/amc-admin/ (Issues tab)

### Admin Analytics
- **Analytics Portal**: http://localhost:8000/admin-portal/
- **System Health**: http://localhost:8000/admin-portal/
- **Charts & Reports**: http://localhost:8000/admin-portal/

### Additional Features
- **FAQ**: http://localhost:8000/faq/
- **Feedback**: http://localhost:8000/feedback/
- **Reports**: http://localhost:8000/dashboard/

---

## ✅ 5-Minute Test Scenarios

### 🟢 Test 1: Normal User Journey (2 minutes)
1. Go to http://localhost:8000/core/user/login/
2. Login with `ALICE001`
3. Click "Submit New Complaint"
4. Fill description: "Test complaint for manual testing"
5. Upload a test file
6. Submit and verify it appears in dashboard

### 🔵 Test 2: Engineer Assignment (2 minutes)
1. Go to http://localhost:8000/login/
2. Login with `demo_engineer1` / `demo123`
3. Go to "All Complaints" tab
4. Find an unassigned complaint
5. Click "Assign to Me"
6. Verify status changes to "Assigned"

### 🟡 Test 3: AMC Admin Management (3 minutes)
1. Go to http://localhost:8000/login/
2. Login with `demo_amc_admin` / `demo123`
3. View dashboard with complaint list
4. Use filters to filter by "Hardware" type
5. Select a complaint and assign engineer
6. Update priority to "High"
7. Export data to CSV

### 🔴 Test 4: Admin Analytics (2 minutes)
1. Go to http://localhost:8000/login/
2. Login with `demo_admin` / `demo123`
3. View real-time analytics dashboard
4. Check system health score
5. Review complaint distribution charts
6. Look for issue detection alerts

---

## 🔧 Troubleshooting

### Server Won't Start
```bash
# Check Python version
python --version

# Check if port is busy
netstat -an | grep 8000

# Try different port
python manage.py runserver 8001
```

### Database Issues
```bash
# Reset and recreate
python manage.py migrate
python manage.py setup_demo_users
```

### No Demo Data
```bash
# Create demo users and complaints
python manage.py setup_demo_users

# Verify data created
python manage.py shell -c "
from django.contrib.auth.models import User
from complaints.models import Complaint
print(f'Users: {User.objects.count()}')
print(f'Complaints: {Complaint.objects.count()}')
"
```

---

## 📱 Mobile Testing

### Responsive Design Test URLs
Test these URLs on mobile/tablet:
- http://localhost:8000/core/user/login/ (Mobile login)
- http://localhost:8000/core/dashboard/ (Mobile dashboard)
- http://localhost:8000/complaints/submit/ (Mobile form)

---

## 🎯 Critical Features Checklist

### ✅ Must Test
- [ ] All 4 user roles can login
- [ ] Normal users can submit complaints
- [ ] Engineers can self-assign complaints
- [ ] AMC Admins can manage assignments
- [ ] Admin analytics dashboard loads
- [ ] File uploads work
- [ ] Status updates function
- [ ] Mobile layout responsive

### ✅ Advanced Features
- [ ] Bulk operations work
- [ ] CSV export functions
- [ ] PDF generation works
- [ ] AJAX updates real-time
- [ ] Issue detection alerts
- [ ] System health monitoring

---

## 📞 Quick Support

### Common Issues
- **Blank page**: Check console for JavaScript errors
- **Login fails**: Verify user exists with `python manage.py shell`
- **Permission denied**: Check user groups assignment
- **Slow loading**: Clear browser cache

### Get System Status
```bash
# Check system health
python manage.py check

# See migrations
python manage.py showmigrations

# List users
python manage.py shell -c "
from django.contrib.auth.models import User
for u in User.objects.all():
    print(f'{u.username} - Groups: {[g.name for g in u.groups.all()]}')
"
```

---

**🚀 Ready to test! Start with the 5-minute scenarios above.**

*For comprehensive testing, refer to the full [MANUAL_TESTING_GUIDE.md](./MANUAL_TESTING_GUIDE.md)*