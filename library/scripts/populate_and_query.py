import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')
django.setup()

from books.models import Author, Book

print('Creating authors...')
a1, _ = Author.objects.get_or_create(name='Alice Martin', defaults={'birth_date':'1975-03-12','nationality':'France'})
a2, _ = Author.objects.get_or_create(name='Bob Smith', defaults={'birth_date':'1980-07-01','nationality':'USA'})
a3, _ = Author.objects.get_or_create(name='Carla Ruiz', defaults={'birth_date':'1990-11-20','nationality':'Spain'})

print('Creating books...')
Book.objects.get_or_create(title='Learning Django', isbn='9780000000001', defaults={'published_date':'2020-01-01','price':Decimal('29.90'),'author':a1})
Book.objects.get_or_create(title='Advanced Python', isbn='9780000000002', defaults={'published_date':'2018-05-10','price':Decimal('39.50'),'author':a1})
Book.objects.get_or_create(title='Intro to Programming', isbn='9780000000003', defaults={'published_date':'2015-09-30','price':Decimal('19.99'),'author':a2})
Book.objects.get_or_create(title='Data Science 101', isbn='9780000000004', defaults={'published_date':'2021-06-15','price':Decimal('45.00'),'author':a3})
Book.objects.get_or_create(title='Web Dev Basics', isbn='9780000000005', defaults={'published_date':'2019-02-20','price':Decimal('24.00'),'author':a2})
Book.objects.get_or_create(title='Machine Learning', isbn='9780000000006', defaults={'published_date':'2022-08-01','price':Decimal('55.00'),'author':a1})

print('--- Sample data created (get_or_create used) ---')

print('\nBooks with price > 30:')
for b in Book.objects.filter(price__gt=30):
    print(f"- {b.title} | {b.author.name} | {b.price}")

print('\nBooks of Alice Martin:')
for b in a1.books.all():
    print(f"- {b.title} | {b.price}")

print('\nAuthors with any book price > 30:')
for a in Author.objects.filter(books__price__gt=30).distinct():
    print(f"- {a.name}")
