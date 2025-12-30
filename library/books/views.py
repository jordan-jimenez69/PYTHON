from django.shortcuts import render


def home(request):
    return render(request, 'home.html')


def book_list(request):
    return render(request, 'books/book_list.html')
