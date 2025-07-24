from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ComplaintForm
from .models import FileAttachment

@login_required
def submit_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.status_id = 1  # assuming 1 = "Open"
            complaint.save()

            for f in request.FILES.getlist('attachments'):
                FileAttachment.objects.create(
                    complaint=complaint,
                    file_name=f.name,
                    file_path=f.name  # we'll improve this with actual MEDIA_PATH later
                )

            return redirect('complaints:list')
    else:
        form = ComplaintForm()

    return render(request, 'complaints/submit.html', {'form': form})
