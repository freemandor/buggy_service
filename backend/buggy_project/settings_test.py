"""
Test settings for buggy_project.
Inherits from base settings and overrides test-specific configurations.
"""

from .settings import *

# Override database to use test database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# Disable migrations for faster tests (optional)
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None
# MIGRATION_MODULES = DisableMigrations()

# Simpler password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Keep debug on for better error messages in test videos
DEBUG = True

# Test-specific configurations
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

