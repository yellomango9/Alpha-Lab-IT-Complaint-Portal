"""
Management command to assign groups to superusers.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction


class Command(BaseCommand):
    help = 'Assign Admin group to all superusers'

    def handle(self, *args, **options):
        """Assign Admin group to superusers."""
        
        self.stdout.write("🔧 Assigning Admin group to superusers...")
        
        # Get or create Admin group
        admin_group, created = Group.objects.get_or_create(name='Admin')
        if created:
            self.stdout.write("   ✅ Created Admin group")
        
        # Find superusers without Admin group
        superusers = User.objects.filter(is_superuser=True)
        updated_count = 0
        
        with transaction.atomic():
            for user in superusers:
                if not user.groups.filter(name='Admin').exists():
                    user.groups.add(admin_group)
                    updated_count += 1
                    self.stdout.write(f"   ✅ Added Admin group to superuser: {user.username}")
                else:
                    self.stdout.write(f"   ℹ️  Superuser {user.username} already has Admin group")
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Updated {updated_count} superusers with Admin group")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✅ All superusers already have appropriate groups")
            )
        
        # Show current superuser status
        self.stdout.write("\n👑 Superuser Status:")
        for user in superusers:
            groups = list(user.groups.values_list('name', flat=True))
            self.stdout.write(f"   {user.username}: {groups if groups else 'No groups'}")