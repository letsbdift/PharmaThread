from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User

class Command(BaseCommand):
    help = 'Sets up default RBAC roles and creates an initial superuser.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting RBAC setup..."))

        # Create Groups
        roles = ['Admin', 'Pharmacist', 'Staff']
        for role in roles:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(f"Created group: {role}")
            else:
                self.stdout.write(f"Group already exists: {role}")

        # Create initial admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            # Assign admin to Admin group
            admin_group = Group.objects.get(name='Admin')
            admin_user.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS("Created default superuser: admin / admin123"))
        else:
            self.stdout.write("User 'admin' already exists.")
            
            # Ensure it is in Admin group
            admin_user = User.objects.get(username='admin')
            admin_group = Group.objects.get(name='Admin')
            if not admin_user.groups.filter(name='Admin').exists():
                admin_user.groups.add(admin_group)
                self.stdout.write("Added existing 'admin' user to Admin group.")

        self.stdout.write(self.style.SUCCESS("RBAC setup complete!"))
