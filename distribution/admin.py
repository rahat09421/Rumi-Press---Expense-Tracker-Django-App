from django.contrib import admin
from .models import Category, Book

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_by')
    search_fields = ('name',)
    
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'publishing_date', 'distribution_expenses', 'created_by')
    list_filter = ('category',)
    search_fields = ('title', 'author')
    date_hierarchy = 'publishing_date'
    