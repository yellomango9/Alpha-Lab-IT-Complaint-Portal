from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView
from django.contrib import messages
from django.http import HttpResponseForbidden

from .models import Feedback, FeedbackTemplate
from .forms import FeedbackForm
from complaints.models import Complaint


class FeedbackCreateView(LoginRequiredMixin, CreateView):
    """Create feedback for a resolved complaint."""
    model = Feedback
    form_class = FeedbackForm
    template_name = 'feedback/create.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.complaint = get_object_or_404(Complaint, pk=kwargs['complaint_pk'])
        
        # Check if user can provide feedback for this complaint
        if self.complaint.user != request.user:
            return HttpResponseForbidden("You can only provide feedback for your own complaints.")
        
        # Check if complaint is resolved
        if not self.complaint.is_resolved:
            messages.error(request, "You can only provide feedback for resolved complaints.")
            return redirect('complaints:detail', pk=self.complaint.pk)
        
        # Check if feedback already exists
        if hasattr(self.complaint, 'feedback'):
            messages.info(request, "You have already provided feedback for this complaint.")
            return redirect('feedback:detail', pk=self.complaint.feedback.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['complaint'] = self.complaint
        return context
    
    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.complaint = self.complaint
        feedback.user = self.request.user
        feedback.save()
        
        messages.success(self.request, 'Thank you for your feedback!')
        return redirect('feedback:detail', pk=feedback.pk)


class FeedbackDetailView(LoginRequiredMixin, DetailView):
    """Detail view for feedback."""
    model = Feedback
    template_name = 'feedback/detail.html'
    context_object_name = 'feedback'
    
    def get_queryset(self):
        # Users can only view their own feedback unless they're engineers/admins
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.is_engineer:
            return Feedback.objects.select_related('complaint', 'user')
        else:
            return Feedback.objects.filter(user=user).select_related('complaint')


class FeedbackListView(LoginRequiredMixin, ListView):
    """List view for feedback (admin/engineer only)."""
    model = Feedback
    template_name = 'feedback/list.html'
    context_object_name = 'feedbacks'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        # Only engineers/admins can view feedback list
        if not (hasattr(request.user, 'profile') and request.user.profile.is_engineer):
            return HttpResponseForbidden("You don't have permission to view this page.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Feedback.objects.select_related('complaint', 'user').order_by('-submitted_at')
        
        # Filter by rating
        rating_filter = self.request.GET.get('rating')
        if rating_filter:
            queryset = queryset.filter(rating=rating_filter)
        
        # Filter by public feedback
        if self.request.GET.get('public_only'):
            queryset = queryset.filter(is_public=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'rating_choices': range(1, 6),
            'current_filters': {
                'rating': self.request.GET.get('rating', ''),
                'public_only': self.request.GET.get('public_only', ''),
            }
        })
        return context


@login_required
def feedback_stats(request):
    """View for feedback statistics (admin/engineer only)."""
    if not (hasattr(request.user, 'profile') and request.user.profile.is_engineer):
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    from django.db.models import Avg, Count
    
    # Calculate statistics
    total_feedback = Feedback.objects.count()
    avg_rating = Feedback.objects.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    rating_distribution = Feedback.objects.values('rating').annotate(count=Count('rating')).order_by('rating')
    
    # Recent feedback
    recent_feedback = Feedback.objects.select_related('complaint', 'user').order_by('-submitted_at')[:10]
    
    context = {
        'total_feedback': total_feedback,
        'avg_rating': round(avg_rating, 2),
        'rating_distribution': rating_distribution,
        'recent_feedback': recent_feedback,
    }
    
    return render(request, 'feedback/stats.html', context)