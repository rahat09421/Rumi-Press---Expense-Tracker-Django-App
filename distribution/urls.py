from django.urls import path
from . import views

app_name = 'distribution'

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/bulk-delete/', views.bulk_delete_categories, name='category_bulk_delete'),
    
    path("books/", views.BookListView.as_view(), name="book_list"),
    path("books/add/", views.BookCreateView.as_view(), name="book_add"),
    path("books/<int:pk>/edit/", views.BookUpdateView.as_view(), name="book_edit"),
    path("books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book_delete"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    
    path("import/", views.import_books_view, name="import_books"),
    
    # Bulk delete
    path("books/bulk-delete/", views.bulk_delete_books, name="book_bulk_delete"),
    
    # Alias to fix 404 when visiting /distribution/reports/
    path("reports/", views.ExpensesReportView.as_view(), name="reports"),
    path("reports/expenses/", views.ExpensesReportView.as_view(), name="expenses_report"),
    path("api/reports/expense_by_category/", views.expenses_by_category_json, name="expenses_by_category_json"),
    
]
