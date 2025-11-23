from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from distribution.models import Book, Category


class RBACPermissionsTests(TestCase):
    def setUp(self):
        # Create roles
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        # Users
        self.superuser = User.objects.create_superuser("super", "super@example.com", "SuperPass123!")
        self.admin1 = User.objects.create_user("admin1", "a1@example.com", "AdminPass123!")
        self.admin2 = User.objects.create_user("admin2", "a2@example.com", "AdminPass123!")
        self.admin1.groups.add(self.admin_group)
        self.admin2.groups.add(self.admin_group)
        # Data
        self.category = Category.objects.create(name="Poetry")
        self.book_by_admin1 = Book.objects.create(title="A", author="X", category=self.category, created_by=self.admin1)
        self.book_by_admin2 = Book.objects.create(title="B", author="Y", category=self.category, created_by=self.admin2)

    def test_admin_can_view_lists(self):
        self.client.login(username="admin1", password="AdminPass123!")
        resp = self.client.get(reverse("distribution:book_list"))
        self.assertEqual(resp.status_code, 200)

    def test_admin_can_create_book(self):
        self.client.login(username="admin1", password="AdminPass123!")
        resp = self.client.post(reverse("distribution:book_add"), {
            "title": "New Book",
            "author": "Auth",
            "category": self.category.id,
            "distribution_expenses": 0,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Book.objects.filter(title="New Book", created_by=self.admin1).exists())

    def test_admin_cannot_delete(self):
        self.client.login(username="admin1", password="AdminPass123!")
        resp = self.client.post(reverse("distribution:book_delete", args=[self.book_by_admin2.id]))
        # DeleteView will be forbidden via mixin; check redirect or 403
        self.assertIn(resp.status_code, [302, 403])

    def test_admin_cannot_edit_others(self):
        self.client.login(username="admin1", password="AdminPass123!")
        resp = self.client.post(reverse("distribution:book_edit", args=[self.book_by_admin2.id]), {
            "title": "Changed",
            "author": "Y",
            "category": self.category.id,
            "distribution_expenses": 0,
        })
        self.assertIn(resp.status_code, [403, 200])
        self.book_by_admin2.refresh_from_db()
        self.assertNotEqual(self.book_by_admin2.title, "Changed")

    def test_superuser_create_admin(self):
        self.client.login(username="super", password="SuperPass123!")
        resp = self.client.post(reverse("accounts:create_admin"), {
            "username": "newadmin",
            "email": "na@example.com",
            "password1": "StrongPass123!@#",
            "password2": "StrongPass123!@#",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username="newadmin").exists())

    def test_inactive_admin_cannot_login(self):
        self.admin1.is_active = False
        self.admin1.save()
        ok = self.client.login(username="admin1", password="AdminPass123!")
        self.assertFalse(ok)

    def test_inactive_login_shows_custom_message(self):
        self.admin1.is_active = False
        self.admin1.save()
        resp = self.client.post(reverse("login"), {
            "username": "admin1",
            "password": "AdminPass123!",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"deactivated by the Superadmin", resp.content)