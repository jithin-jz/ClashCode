import django
from django.urls import get_resolver
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

def dump_urls(patterns, prefix=''):
    for p in patterns:
        if hasattr(p, 'url_patterns'):
            dump_urls(p.url_patterns, prefix + str(p.pattern))
        else:
            print(f'{prefix}{str(p.pattern)}')

dump_urls(get_resolver().url_patterns)
