from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta, datetime
from django.template.loader import get_template
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

from .models import UserProfile
from complaints.models import Complaint, Status, ComplaintType, ComplaintClosing
from complaints.forms import ComplaintUpdateForm


def engineer_required(view_func):
    """Decorator to check if user is an engineer or admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user is engineer, AMC admin, or admin
        if not (request.user.groups.filter(name__in=['ENGINEER', 'AMC ADMIN', 'ADMIN']).exists() or 
                request.user.is_staff):
            messages.error(request, 'Access denied. You need engineer or admin privileges.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


@engineer_required
def engineer_dashboard(request):
    """Simple dashboard for engineers showing all complaints and assigned complaints."""
    user = request.user
    
    # Get all open complaints
    all_complaints = Complaint.objects.filter(
        status__is_closed=False
    ).select_related('user', 'type', 'status', 'assigned_to').order_by('-created_at')
    
    # Get complaints assigned to this engineer
    assigned_complaints = Complaint.objects.filter(
        assigned_to=user,
        status__is_closed=False
    ).select_related('user', 'type', 'status').order_by('-created_at')
    
    # Get closed complaints from last 5 days
    five_days_ago = timezone.now() - timedelta(days=5)
    closed_complaints = Complaint.objects.filter(
        status__is_closed=True,
        resolved_at__gte=five_days_ago
    ).select_related('user', 'type', 'status', 'assigned_to').order_by('-resolved_at')
    
    context = {
        'all_complaints': all_complaints,
        'assigned_complaints': assigned_complaints,
        'closed_complaints': closed_complaints,
        'all_count': all_complaints.count(),
        'assigned_count': assigned_complaints.count(),
        'closed_count': closed_complaints.count(),
    }
    
    return render(request, 'core/engineer_dashboard.html', context)


@engineer_required
def assign_to_self(request, complaint_id):
    """Allow engineer to assign an unassigned complaint to themselves."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Check if complaint is already assigned
    if complaint.assigned_to is not None:
        return JsonResponse({'success': False, 'error': 'Complaint is already assigned'})
    
    # Assign to current user
    complaint.assigned_to = request.user
    
    # Change status to 'Assigned'
    assigned_status = Status.objects.filter(name='Assigned', is_active=True).first()
    if assigned_status:
        complaint.status = assigned_status
    
    complaint.save()
    
    # Create a remark about the assignment
    from complaints.models import Remark
    Remark.objects.create(
        complaint=complaint,
        user=request.user,
        text=f"Complaint self-assigned by {request.user.get_full_name() or request.user.username}",
        is_internal_note=True
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Complaint assigned to you successfully',
        'assigned_to': request.user.get_full_name() or request.user.username,
        'status': complaint.status.name
    })


@engineer_required
def complaint_detail(request, complaint_id):
    """Detailed view of a complaint for engineers."""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Get complaint history
    status_history = complaint.status_history.all().order_by('-changed_at')
    remarks = complaint.remarks.all().order_by('-created_at')  # Show all remarks, newest first
    attachments = complaint.attachments.all().order_by('-uploaded_at')
    
    # Check if complaint has closing details
    closing_details = getattr(complaint, 'closing_details', None)
    
    # Get available status options for updates
    status_options = Status.objects.filter(is_active=True).order_by('order')
    
    context = {
        'complaint': complaint,
        'status_history': status_history,
        'remarks': remarks,
        'attachments': attachments,
        'closing_details': closing_details,
        'status_options': status_options,
    }
    
    return render(request, 'core/complaint_detail.html', context)


@engineer_required
def update_complaint_status(request, complaint_id):
    """Update complaint status and add remarks."""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'resolve':
            # Resolve complaint with staff remark
            staff_remark = request.POST.get('staff_remark', '').strip()
            if not staff_remark:
                messages.error(request, 'Please provide a closing remark.')
                return redirect('engineer:complaint_detail', complaint_id=complaint_id)
            
            # Set complaint to resolved status
            resolved_status = Status.objects.filter(is_closed=True, name__icontains='resolved').first()
            if not resolved_status:
                resolved_status = Status.objects.filter(is_closed=True).first()
            
            if resolved_status:
                complaint.status = resolved_status
                complaint.resolved_at = timezone.now()
                complaint.save()
                
                # Create closing details
                ComplaintClosing.objects.create(
                    complaint=complaint,
                    closed_by_staff=request.user,
                    staff_closing_remark=staff_remark
                )
                
                messages.success(request, f'Complaint #{complaint.id} has been marked as resolved.')
            else:
                messages.error(request, 'No resolved status found in the system.')
        
        elif action == 'update_status':
            # Engineers can only change status to 'In Progress' or add remarks
            new_status_id = request.POST.get('status')
            remark_text = request.POST.get('remark', '').strip()
            
            if new_status_id:
                try:
                    new_status = Status.objects.get(id=new_status_id)
                    
                    # Restrict engineers to only set to 'In Progress' status
                    allowed_statuses = ['In Progress', 'Waiting for User']
                    if new_status.name not in allowed_statuses:
                        messages.error(request, 'Engineers can only change status to "In Progress" or "Waiting for User". Use the resolve button to complete the complaint.')
                        return redirect('engineer:complaint_detail', complaint_id=complaint_id)
                    
                    old_status = complaint.status
                    complaint.status = new_status
                    complaint.save()
                    
                    # Create status history entry
                    from complaints.models import StatusHistory
                    StatusHistory.objects.create(
                        complaint=complaint,
                        previous_status=old_status,
                        new_status=new_status,
                        changed_by=request.user,
                        notes=remark_text
                    )
                    
                    # Add remark if provided
                    if remark_text:
                        from complaints.models import Remark
                        Remark.objects.create(
                            complaint=complaint,
                            user=request.user,
                            text=remark_text,
                            is_internal_note=False
                        )
                    
                    messages.success(request, f'Complaint status updated to {new_status.name}.')
                except Status.DoesNotExist:
                    messages.error(request, 'Invalid status selected.')
        
        return redirect('engineer:complaint_detail', complaint_id=complaint_id)
    
    return redirect('engineer:complaint_detail', complaint_id=complaint_id)


@engineer_required
def download_complaint_pdf(request, complaint_id):
    """Generate and download PDF report for a complaint."""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"<b>Complaint Report - #{complaint.id}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Complaint details
    details_data = [
        ['Complaint ID:', f"#{complaint.id}"],
        ['Complaint Type:', complaint.type.name],
        ['Description:', complaint.description],
        ['User:', complaint.user.get_full_name() or complaint.user.username],
        ['Department:', complaint.user.profile.department.name if complaint.user.profile.department else 'N/A'],
        ['Status:', complaint.status.name],
        ['Priority:', complaint.get_urgency_display()],
        ['Assigned Engineer:', complaint.assigned_to.get_full_name() if complaint.assigned_to else 'Unassigned'],
        ['Created Date/Time:', complaint.created_at.strftime('%Y-%m-%d %H:%M:%S')],
        ['Resolved Date/Time:', complaint.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if complaint.resolved_at else 'Not resolved'],
    ]
    
    # Add closing details if available
    closing_details = getattr(complaint, 'closing_details', None)
    if closing_details:
        details_data.extend([
            ['Staff Closing Remark:', closing_details.staff_closing_remark],
            ['Staff Closed Date/Time:', closing_details.staff_closed_at.strftime('%Y-%m-%d %H:%M:%S')],
            ['User Closed Date/Time:', closing_details.user_closed_at.strftime('%Y-%m-%d %H:%M:%S') if closing_details.user_closed_at else 'Not closed by user'],
        ])
    
    details_table = Table(details_data, colWidths=[150, 350])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, 0), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(details_table)
    story.append(Spacer(1, 20))
    
    # Remarks section
    remarks = complaint.remarks.all().order_by('created_at')
    if remarks:
        story.append(Paragraph("<b>Remarks History:</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        for remark in remarks:
            remark_text = f"<b>{remark.created_at.strftime('%Y-%m-%d %H:%M')} - {remark.user.get_full_name() if remark.user else 'System'}:</b><br/>{remark.text}"
            story.append(Paragraph(remark_text, styles['Normal']))
            story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="complaint_{complaint.id}_report.pdf"'
    response.write(pdf)
    
    return response