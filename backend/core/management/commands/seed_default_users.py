from django.core.management.base import BaseCommand
from core.models import User


DEFAULT_USERS = [
    ("manager1", "manager1", User.Role.MANAGER),
    ("dispatcher1", "dispatcher1", User.Role.DISPATCHER),
    ("driver1", "driver1", User.Role.DRIVER),
]


class Command(BaseCommand):
    help = "Create default manager, dispatcher, and driver users if they do not exist."

    def handle(self, *args, **options):
        for username, password, role in DEFAULT_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": role,
                    "is_staff": role in {User.Role.MANAGER, User.Role.DISPATCHER},
                },
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created {role.lower()} '{username}'"))
            else:
                self.stdout.write(f"User '{username}' already exists (role={user.role})")
