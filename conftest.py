"""Configuration globale pour pytest"""
import os
import django


def pytest_configure():
    """Configure Django pour pytest"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'epicevents.settings')
    django.setup()
