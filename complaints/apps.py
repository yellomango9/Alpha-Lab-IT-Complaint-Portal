from django.apps import AppConfig


class ComplaintsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'complaints'
    verbose_name = 'Complaint Management'
    
    def ready(self):
        """Import signals when the app is ready."""
        import complaints.signals