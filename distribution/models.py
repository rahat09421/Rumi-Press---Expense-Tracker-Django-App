from django.db import models
from django.conf import settings

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Categories"
    def __str__(self):
        return self.name
    
class Book(models.Model):
    source_id = models.CharField(max_length=64, null=True, blank=True, help_text="Original spreadsheet id / ISBN or source identifier")
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=500, null=True, blank=True)
    author = models.CharField(max_length=200)
    publisher = models.CharField(max_length=500, null=True, blank=True)
    publishing_date = models.DateField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='books')
    distribution_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-publishing_date', 'title']
        
    def __str__(self):
        return f'{self.title} — {self.author}'