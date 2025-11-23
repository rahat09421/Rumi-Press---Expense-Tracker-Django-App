from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

from .forms import AdminCreationForm, SuperuserBootstrapForm
from .models import EmailVerificationToken


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@superuser_required
def create_admin(request):
    if request.method == "POST":
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            token = EmailVerificationToken.objects.create(user=user, token=get_random_string(32))
            verification_url = request.build_absolute_uri(reverse("accounts:verify_email", args=[token.token]))
            send_mail(
                subject="Verify your admin account email",
                message=f"Please verify your email by visiting: {verification_url}",
                from_email=None,
                recipient_list=[user.email],
                fail_silently=True,
            )
            messages.success(request, "Admin account created. Verification email sent.")
            return redirect("accounts:create_admin")
    else:
        form = AdminCreationForm()
    staff_admins = User.objects.filter(groups__name="Admin").order_by('username')
    return render(request, "accounts/create_admin.html", {"form": form, "staff_admins": staff_admins})


def verify_email(request, token: str):
    tok = get_object_or_404(EmailVerificationToken, token=token, is_used=False)
    user = tok.user
    # Mark verified via User profile; if not present, we can use user.is_active toggle
    user.is_active = True
    user.save()
    tok.is_used = True
    tok.save()
    messages.success(request, "Email verified. You may now sign in.")
    return redirect("distribution:book_list")


def bootstrap_superuser(request):
    from django.contrib.auth.models import User
    if User.objects.filter(is_superuser=True).exists():
        return redirect("distribution:book_list")
    if request.method == "POST":
        form = SuperuserBootstrapForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Superuser created. You can now log in.")
            return redirect("login")
    else:
        form = SuperuserBootstrapForm()
    return render(request, "accounts/bootstrap_superuser.html", {"form": form})


@superuser_required
def admin_set_status(request):
    from django.contrib.auth.models import User
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        status = request.POST.get('status')  # 'active' | 'inactive'
        try:
            target = User.objects.get(pk=user_id)
            # do not allow toggling superusers
            if target.is_superuser:
                messages.error(request, "Cannot change status of a superuser.")
                return redirect("accounts:create_admin")
            target.is_active = (status == 'active')
            target.save()
            label = 'activated' if target.is_active else 'deactivated'
            messages.success(request, f"User '{target.username}' {label} successfully.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return redirect("accounts:create_admin")