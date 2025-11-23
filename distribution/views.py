from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Category, Book
from .forms import CategoryForm, BookForm, UploadBooksForm
from django.http import  JsonResponse
from .importer import import_books_from_filelike
from django.db.models.functions import Coalesce
from django.db.models import Sum, Count, Value, DecimalField
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from accounts.mixins import AuditLoggingMixin, AdminReadOnlyEnforcementMixin, is_admin

class CategoryListView(LoginRequiredMixin, AuditLoggingMixin, ListView):
    model = Category
    template_name = 'distribution/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        sort = self.request.GET.get('sort', 'name')
        direction = self.request.GET.get('dir', 'asc')
        q = self.request.GET.get('q')
        qs = (
            Category.objects
            .annotate(
                books_count=Count('books', distinct=True),
                total_expense=Coalesce(
                    Sum('books__distribution_expenses', output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField()
                )
            )
        )
        if q:
            qs = qs.filter(Q(name__icontains=q))
        sort_map = {
            'name': 'name',
            'books_count': 'books_count',
            'total_expense': 'total_expense',
        }
        order_field = sort_map.get(sort, 'name')
        order_by = order_field if direction != 'desc' else f'-{order_field}'
        return qs.order_by(order_by)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.request.GET.copy()
        qs.pop('page', None)
        ctx['querystring'] = qs.urlencode()
        ctx['sort'] = self.request.GET.get('sort', 'name')
        ctx['dir'] = self.request.GET.get('dir', 'asc')
        ctx['filters'] = {
            'q': self.request.GET.get('q', ''),
        }
        return ctx
    
class CategoryCreateView(SuccessMessageMixin, LoginRequiredMixin, AdminReadOnlyEnforcementMixin, AuditLoggingMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'distribution/category_form.html'
    success_url = reverse_lazy('distribution:category_list')
    success_message = "Category created successfully."
    
class CategoryUpdateView(SuccessMessageMixin, LoginRequiredMixin, AdminReadOnlyEnforcementMixin, AuditLoggingMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'distribution/category_form.html'
    success_url = reverse_lazy('distribution:category_list')
    success_message = "Category updated successfully."
    
class CategoryDeleteView(LoginRequiredMixin, AdminReadOnlyEnforcementMixin, AuditLoggingMixin, DeleteView):
    model = Category
    template_name = 'distribution/category_confirm_delete.html'
    success_url = reverse_lazy('distribution:category_list')

@login_required
@require_POST
def bulk_delete_categories(request):
    ids = request.POST.getlist('selected')
    deleted = 0
    skipped = 0
    if ids:
        qs = Category.objects.filter(pk__in=ids)
        # Superusers can delete any categories
        if request.user.is_superuser:
            pass
        else:
            # Admins/staff can only delete categories they created; block if any belong to another admin
            if is_admin(request.user) or request.user.is_staff:
                forbidden = qs.filter(~Q(created_by_id=request.user.id), ~Q(created_by_id__isnull=True)).exists()
                if forbidden:
                    messages.error(request, "Read-only for your role: you cannot delete records created by another admin.")
                    nxt = request.POST.get('next', '')
                    url = reverse('distribution:category_list')
                    if nxt:
                        url = f"{url}?{nxt}"
                    return redirect(url)
        for c in qs:
            try:
                c.delete()
                deleted += 1
            except ProtectedError:
                skipped += 1
        if deleted:
            messages.success(request, f"Deleted {deleted} categor(y/ies)")
        if skipped:
            messages.info(request, f"Skipped {skipped} category(ies) that have related books")
    else:
        messages.info(request, "No categories selected")
    nxt = request.POST.get('next', '')
    url = reverse('distribution:category_list')
    if nxt:
        url = f"{url}?{nxt}"
    return redirect(url)
    
class BookListView(LoginRequiredMixin, AuditLoggingMixin, ListView):
    model = Book
    template_name = 'distribution/book_list.html'
    context_object_name = 'books'
    paginate_by = 20

    def get_queryset(self):
        # Determine sort field and direction
        sort = self.request.GET.get('sort', 'title')
        direction = self.request.GET.get('dir', 'asc')
        sort_map = {
            'title': 'title',
            'author': 'author',
            'publisher': 'publisher',
            'category': 'category__name',
            'distribution_expenses': 'distribution_expenses',
            'publishing_date': 'publishing_date',
        }
        order_field = sort_map.get(sort, 'title')
        order_by = order_field if direction != 'desc' else f'-{order_field}'

        qs = Book.objects.select_related('category')
        q = self.request.GET.get('q')
        cat = self.request.GET.get('category')
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(publisher__icontains=q))
        if cat:
            qs = qs.filter(category_id=cat)
        if start:
            qs = qs.filter(publishing_date__gte=start)
        if end:
            qs = qs.filter(publishing_date__lte=end)
        return qs.order_by(order_by)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.order_by('name')
        # preserve filters for pagination links
        qs = self.request.GET.copy()
        qs.pop('page', None)
        ctx['querystring'] = qs.urlencode()
        ctx['filters'] = {
            'q': self.request.GET.get('q', ''),
            'category': self.request.GET.get('category') or '',
            'start': self.request.GET.get('start', ''),
            'end': self.request.GET.get('end', ''),
        }
        # expose current sort state to template
        ctx['sort'] = self.request.GET.get('sort', 'title')
        ctx['dir'] = self.request.GET.get('dir', 'asc')
        return ctx
    
class BookCreateView(SuccessMessageMixin, LoginRequiredMixin, AdminReadOnlyEnforcementMixin, AuditLoggingMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'distribution/book_form.html'
    success_url = reverse_lazy('distribution:book_list')
    success_message = "Book added successfully."
    
class BookUpdateView(SuccessMessageMixin, LoginRequiredMixin, AdminReadOnlyEnforcementMixin, AuditLoggingMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'distribution/book_form.html'
    success_url = reverse_lazy('distribution:book_list')
    success_message = "Book updated successfully."

class BookDeleteView(LoginRequiredMixin, AdminReadOnlyEnforcementMixin, AuditLoggingMixin, DeleteView):
    model = Book
    template_name = 'distribution/book_confirm_delete.html'
    success_url = reverse_lazy('distribution:book_list')
    
class BookDetailView(LoginRequiredMixin, AuditLoggingMixin, DetailView):
    model = Book
    template_name = 'distribution/book_details.html'
    
class ExpensesReportView(LoginRequiredMixin, TemplateView):
    template_name = 'distribution/expenses_report.html'
    
@login_required
def expenses_by_category_json(request):
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    qs = Book.objects.all()
    if start:
        qs = qs.filter(publishing_date__gte=start)
    if end:
        qs = qs.filter(publishing_date__lte=end)
    agg = (
        qs.values('category__id', 'category__name')
          .annotate(total=Sum('distribution_expenses'))
          .order_by('-total')
    )
    data = [
        {
            'category': r['category__name'] or 'Uncategorized',
            'total': float(r['total'] or 0),
        }
        for r in agg
    ]
    return JsonResponse(data, safe=False)

@staff_member_required
def import_books_view(request):
    """
    Simple upload view for staff to upload Excel/CSV and import books.
    """
    
    if request.method == 'POST':
        form = UploadBooksForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data['file']
            try:
                result = import_books_from_filelike(upload, filename=upload.name, created_by=request.user)
            except ValueError as e:
                messages.error(request, f'Upload failed: {e}')
                return redirect(reverse('distribution:import_books'))
            except Exception as exc:
                messages.error(request, f'Unexpected error: {exc}')
                return redirect(reverse('distribution:import_books'))
            
            created = result.get('created', 0)
            updated = result.get('updated', 0)
            skipped = result.get('skipped', 0)
            errors = result.get('errors', [])
            
            msg = f'Import finished -- Created: {created}, Updated: {updated}, Skipped: {skipped}'
            messages.success(request, msg)
            if errors:
                messages.error(request, f'Errors: {len(errors)} rows had problems -- check servre logs for details.')
            return redirect(reverse('distribution:import_books'))
    else:
        form = UploadBooksForm()
            
    return render(request, 'distribution/import_books.html', {'form': form})

@login_required
@require_POST
def bulk_delete_books(request):
    ids = request.POST.getlist('selected')
    count = 0
    if ids:
        qs = Book.objects.filter(pk__in=ids)
        # Superusers can delete any records
        if request.user.is_superuser:
            pass
        else:
            # Admins/staff can only delete records they created; block if any belong to another admin
            if is_admin(request.user) or request.user.is_staff:
                forbidden = qs.filter(~Q(created_by_id=request.user.id), ~Q(created_by_id__isnull=True)).exists()
                if forbidden:
                    messages.error(request, "Read-only for your role: you cannot delete records created by another admin.")
                    nxt = request.POST.get('next', '')
                    url = reverse('distribution:book_list')
                    if nxt:
                        url = f"{url}?{nxt}"
                    return redirect(url)
        count = qs.count()
        qs.delete()
        messages.success(request, f"Deleted {count} book(s)")
    else:
        messages.info(request, "No books selected")
    nxt = request.POST.get('next', '')
    url = reverse('distribution:book_list')
    if nxt:
        url = f"{url}?{nxt}"
    return redirect(url)
 