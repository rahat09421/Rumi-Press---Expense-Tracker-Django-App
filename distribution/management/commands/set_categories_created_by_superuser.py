from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from distribution.models import Category


class Command(BaseCommand):
    help = "Set created_by on existing Category records to the main superuser (or specified username)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Assign to this superuser username instead of the default first superuser.',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options.get('username')

        if username:
            user = User.objects.filter(username=username, is_superuser=True).first()
            if not user:
                raise CommandError(f"No superuser found with username '{username}'.")
        else:
            user = User.objects.filter(is_superuser=True).order_by('id').first()
            if not user:
                raise CommandError("No superuser exists. Create one before running this command.")

        qs = Category.objects.filter(created_by__isnull=True)
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("No categories with null created_by found; nothing to update."))
            return

        updated = qs.update(created_by=user)
        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated} category(ies); assigned created_by to superuser '{user.username}'."
        ))