from django.test import TestCase
from .models import Category, Book
from decimal import Decimal

# Create your tests here.

class BookModelTest(TestCase):
    def test_sum_expense_by_category(self):
        c = Category.objects.create(name = 'Python')
        Book.objects.create(title='A', author='X', category=c, distribution_expenses=Decimal('100'))
        Book.objects.create(title='B', author='Y', category=c, distribution_expenses=Decimal('150'))
        from django.db.models import Sum
        total = Book.objects.filter(Category=c).aaggregate(total=Sum('distribution_expenses'))['total']
        self.assertEqual(total, Decimal('250'))