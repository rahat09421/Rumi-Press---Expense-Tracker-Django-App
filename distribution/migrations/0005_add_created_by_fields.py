from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ('distribution', '0004_book_publisher_book_source_id_book_subtitle'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='created_by',
            field=models.ForeignKey(null=True, blank=True, on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='book',
            name='created_by',
            field=models.ForeignKey(null=True, blank=True, on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]