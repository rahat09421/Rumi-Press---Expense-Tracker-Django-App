import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from distribution.importer import import_books_from_filelike


class Command(BaseCommand):
    help = (
        "Import books from Excel/CSV. Expected headers (case-insensitive): "
        "id, title, subtitle, authors, publisher, published_date, category, distribution_expense"
    )

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help='Path to Excel (.xlsx/.xls) or CSV file')
        parser.add_argument('--username', type=str, help='Stamp created_by with this username (optional)')

    def handle(self, *args, **options):
        path = options['filepath']
        username = options.get('username')

        if not os.path.exists(path):
            raise CommandError(f'File not found: {path}')

        created_by = None
        if username:
            User = get_user_model()
            created_by = User.objects.filter(username=username).first()
            if not created_by:
                raise CommandError(f"No user found with username '{username}'.")

        try:
            with open(path, 'rb') as f:
                result = import_books_from_filelike(f, filename=os.path.basename(path), created_by=created_by)
        except ValueError as e:
            raise CommandError(f'Upload failed: {e}')
        except Exception as exc:
            raise CommandError(f'Unexpected error: {exc}')

        created = result.get('created', 0)
        updated = result.get('updated', 0)
        skipped = result.get('skipped', 0)
        errors = result.get('errors', [])

        msg = f'Import finished — Created: {created}, Updated: {updated}, Skipped: {skipped}'
        self.stdout.write(self.style.SUCCESS(msg))
        if errors:
            self.stdout.write(self.style.WARNING(f'Errors: {len(errors)} row(s) had issues'))