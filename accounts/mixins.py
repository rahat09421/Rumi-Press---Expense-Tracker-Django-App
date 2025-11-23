from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db.models import QuerySet

from .models import AuditLog


def is_admin(user) -> bool:
    return user.is_authenticated and user.groups.filter(name="Admin").exists()


class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class AuditLoggingMixin:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        try:
            if request.user.is_authenticated and is_admin(request.user):
                action = "read" if request.method == "GET" else "update"
                model = self.model.__name__ if hasattr(self, "model") else self.__class__.__name__
                obj_id = ""
                if hasattr(self, "object") and getattr(self, "object", None):
                    obj_id = str(self.object.pk)
                AuditLog.objects.create(
                    actor=request.user,
                    action=action,
                    model=model,
                    object_id=obj_id,
                    details=f"path={request.path} method={request.method}",
                )
        except Exception:
            # Fail-safe: never break application due to logging
            pass
        return response


class AdminReadOnlyEnforcementMixin:
    """
    For Admin group:
    - Allow GET/HEAD
    - Allow POST only for create views
    - Disallow DELETE
    - On update, allow only if object.created_by == request.user
    """

    def dispatch(self, request, *args, **kwargs):
        # Friendly handling for delete attempts
        if request.method in ["DELETE", "POST"] and self.__class__.__name__.endswith('DeleteView'):
            # For superusers, allow deletion
            if request.user.is_superuser:
                return super().dispatch(request, *args, **kwargs)
            # For Admin group and staff, only allow deleting records they created
            if is_admin(request.user) or request.user.is_staff:
                try:
                    obj = self.get_object()
                    if hasattr(obj, "created_by") and obj.created_by_id and obj.created_by_id != request.user.id:
                        messages.error(request, "Read-only for your role: you cannot delete records created by another admin.")
                        return redirect(reverse('distribution:book_list'))
                except Exception:
                    messages.error(request, "Read-only for your role: you cannot delete records created by another admin.")
                    return redirect(reverse('distribution:book_list'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # For create: stamp created_by if model has the field
        instance = getattr(form, 'instance', None)
        if instance is not None and hasattr(instance, "created_by") and not instance.pk:
            if self.request.user.is_authenticated:
                instance.created_by = self.request.user
        return super().form_valid(form)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        self.object = obj
        if is_admin(self.request.user) and self.request.method in ["POST", "PUT", "PATCH"] and not self.__class__.__name__.endswith('DeleteView'):
            # Only allow editing own records (exclude DeleteView; handled in dispatch)
            if hasattr(obj, "created_by") and obj.created_by_id != self.request.user.id:
                raise PermissionDenied("Admins may only edit records they created.")
        return obj

    def get_queryset(self):
        qs = super().get_queryset()
        # Row-level security: admins can see all but we can tailor if needed
        if is_admin(self.request.user):
            if isinstance(qs, QuerySet):
                return qs
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        read_only = False
        if is_admin(self.request.user):
            obj = getattr(self, 'object', None)
            if obj and hasattr(obj, 'created_by') and obj.created_by_id != self.request.user.id:
                read_only = True
        ctx['read_only'] = read_only
        return ctx