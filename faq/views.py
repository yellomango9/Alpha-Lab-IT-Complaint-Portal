from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.db.models import Q

from .models import FAQ, FAQCategory


class FAQListView(LoginRequiredMixin, ListView):
    """List view for FAQs with category filtering and search."""
    model = FAQ
    template_name = 'faq/list.html'
    context_object_name = 'faqs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = FAQ.objects.filter(is_active=True).select_related('category')
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(question__icontains=search_query) |
                Q(answer__icontains=search_query)
            )
        
        # Show featured FAQs first, then by order
        return queryset.order_by('-is_featured', 'category__order', 'order', 'question')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': FAQCategory.objects.filter(is_active=True).order_by('order'),
            'current_category': self.request.GET.get('category', ''),
            'search_query': self.request.GET.get('search', ''),
            'featured_faqs': FAQ.objects.filter(is_featured=True, is_active=True)[:5]
        })
        return context


class FAQDetailView(LoginRequiredMixin, DetailView):
    """Detail view for individual FAQ with view count tracking."""
    model = FAQ
    template_name = 'faq/detail.html'
    context_object_name = 'faq'
    
    def get_queryset(self):
        return FAQ.objects.filter(is_active=True).select_related('category')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        obj.increment_view_count()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get related FAQs from same category
        if self.object.category:
            context['related_faqs'] = FAQ.objects.filter(
                category=self.object.category,
                is_active=True
            ).exclude(id=self.object.id)[:5]
        return context


def mark_faq_helpful(request, pk):
    """AJAX endpoint to mark FAQ as helpful."""
    if request.method == 'POST':
        faq = get_object_or_404(FAQ, pk=pk, is_active=True)
        faq.mark_helpful()
        return JsonResponse({
            'success': True,
            'helpful_count': faq.helpful_count
        })
    return JsonResponse({'success': False})