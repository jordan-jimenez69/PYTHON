from django.http import HttpResponse


def home(request):
    return HttpResponse("Bienvenue")


def book_list(request):
    return HttpResponse("Liste des livres")
