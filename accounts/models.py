from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')

        # New users must be approved before they can log in.
        email = self.normalize_email(email)
        username = extra_fields.get('username')

        if self.model.objects.filter(email=email).exists():
            raise ValueError('Email already exists')
        if username and self.model.objects.filter(username=username).exists():
            raise ValueError('Username already exists')

        extra_fields.setdefault('is_active', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN   = 'admin',   'Admin'
        HEAD    = 'head',    'Head'
        MANAGER = 'manager', 'Manager'
        STAFF   = 'staff',   'Staff'
        TEACHER   = 'teacher',   'Teacher'
        PRINCIPAL = 'principal', 'Principal'

    # Email is used as the login field instead of username.
    email    = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True, blank=True, null=True)
    fullname = models.CharField(max_length=100)
    role     = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['fullname', 'username']
    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"
