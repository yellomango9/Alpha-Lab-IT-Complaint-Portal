"""
Management command to fix UserProfile issues and clean up duplicates.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Fix UserProfile issues and clean up duplicates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        """Fix UserProfile issues."""
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        self.stdout.write("🔧 Checking UserProfile integrity...")
        
        # Find users without profiles
        users_without_profiles = User.objects.filter(profile__isnull=True)
        
        # Find duplicate profiles (shouldn't happen with OneToOne, but let's check)
        duplicate_profiles = []
        for user in User.objects.all():
            profile_count = UserProfile.objects.filter(user=user).count()
            if profile_count > 1:
                duplicate_profiles.append((user, profile_count))
        
        # Find orphaned profiles (profiles without users)
        orphaned_profiles = UserProfile.objects.filter(user__isnull=True)
        
        # Check for any integrity issues
        integrity_issues = []
        try:
            # Try to identify any potential constraint violations
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id, COUNT(*) FROM core_userprofile GROUP BY user_id HAVING COUNT(*) > 1")
                db_duplicates = cursor.fetchall()
                if db_duplicates:
                    integrity_issues.extend(db_duplicates)
        except Exception as e:
            self.stdout.write(f"Could not check database constraints: {e}")
        
        # Report findings
        self.stdout.write(f"📊 Found {users_without_profiles.count()} users without profiles")
        self.stdout.write(f"📊 Found {len(duplicate_profiles)} users with duplicate profiles")
        self.stdout.write(f"📊 Found {orphaned_profiles.count()} orphaned profiles")
        if integrity_issues:
            self.stdout.write(f"📊 Found {len(integrity_issues)} database integrity issues")
        
        if not dry_run:
            with transaction.atomic():
                # Create missing profiles
                created_count = 0
                for user in users_without_profiles:
                    UserProfile.objects.get_or_create(user=user)
                    created_count += 1
                    self.stdout.write(f"   ✅ Created profile for user: {user.username}")
                
                # Fix duplicate profiles
                fixed_count = 0
                for user, count in duplicate_profiles:
                    # Keep the first profile, delete the rest
                    profiles = UserProfile.objects.filter(user=user).order_by('id')
                    for profile in profiles[1:]:  # Skip the first one
                        profile.delete()
                        fixed_count += 1
                    self.stdout.write(f"   ✅ Fixed duplicate profiles for user: {user.username}")
                
                # Clean up orphaned profiles
                orphaned_count = 0
                for profile in orphaned_profiles:
                    profile.delete()
                    orphaned_count += 1
                    self.stdout.write(f"   ✅ Removed orphaned profile: {profile.id}")
                
                # Fix database integrity issues
                if integrity_issues:
                    for user_id, count in integrity_issues:
                        self.stdout.write(f"   ⚠️  Database shows {count} profiles for user_id {user_id}")
                        # Try to fix by removing duplicates
                        profiles = UserProfile.objects.filter(user_id=user_id).order_by('id')
                        for profile in profiles[1:]:
                            profile.delete()
                            self.stdout.write(f"   ✅ Removed duplicate profile for user_id {user_id}")
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Fixed {created_count} missing profiles, {fixed_count} duplicates, and {orphaned_count} orphaned profiles"
                    )
                )
        else:
            # Dry run - just show what would be done
            for user in users_without_profiles:
                self.stdout.write(f"   Would create profile for: {user.username}")
            
            for user, count in duplicate_profiles:
                self.stdout.write(f"   Would fix {count-1} duplicate profiles for: {user.username}")
        
        # Show current status
        self.stdout.write("\n📈 Current Status:")
        total_users = User.objects.count()
        total_profiles = UserProfile.objects.count()
        self.stdout.write(f"   Users: {total_users}")
        self.stdout.write(f"   Profiles: {total_profiles}")
        
        if total_users == total_profiles:
            self.stdout.write(self.style.SUCCESS("   ✅ All users have profiles"))
        else:
            self.stdout.write(self.style.ERROR(f"   ❌ Mismatch: {abs(total_users - total_profiles)} difference"))
        
        # Show group assignments
        self.stdout.write("\n👥 Group Assignments:")
        for group_name in ['Admin', 'AMC Admin', 'Engineer']:
            count = User.objects.filter(groups__name=group_name).count()
            self.stdout.write(f"   {group_name}: {count} users")
        
        no_groups = User.objects.filter(groups__isnull=True).count()
        self.stdout.write(f"   No Groups: {no_groups} users")
        
        if no_groups > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  {no_groups} users have no groups assigned and won't be able to log in!"
                )
            )