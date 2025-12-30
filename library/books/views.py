from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, View
from django.utils import timezone
from .models import Book, Author, Loan, Category
from .forms import LoanCreateForm
from django.db.models import Q


class BookListView(ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 8

    def get_queryset(self):
        qs = super().get_queryset().select_related('author', 'category')
        q = self.request.GET.get('q')
        category_id = self.kwargs.get('category_id') or self.request.GET.get('category')
        author_id = self.kwargs.get('author_id') or self.request.GET.get('author')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(isbn__icontains=q) | Q(author__first_name__icontains=q) | Q(author__last_name__icontains=q))
        if category_id:
            qs = qs.filter(category_id=category_id)
        if author_id:
            qs = qs.filter(author_id=author_id)
        return qs.order_by('title')


class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'


class AuthorListView(ListView):
    model = Author
    template_name = 'books/author_list.html'
    context_object_name = 'authors'
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))
        return qs.order_by('last_name', 'first_name')


class AuthorDetailView(DetailView):
    model = Author
    template_name = 'books/author_detail.html'
    context_object_name = 'author'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['books'] = self.object.books.all()
        return ctx


class ActiveLoanListView(ListView):
    model = Loan
    template_name = 'loans/active_loans.html'
    context_object_name = 'loans'
    paginate_by = 15

    def get_queryset(self):
        return Loan.objects.filter(status=Loan.STATUS_BORROWED).select_related('book')


class LateLoanListView(ListView):
    model = Loan
    template_name = 'loans/late_loans.html'
    context_object_name = 'loans'
    paginate_by = 15

    def get_queryset(self):
        return Loan.objects.filter(status=Loan.STATUS_BORROWED, due_date__lt=timezone.now()).select_related('book')


class UserLoanHistoryView(ListView):
    model = Loan
    template_name = 'loans/history.html'
    context_object_name = 'loans'
    paginate_by = 20

    def get_queryset(self):
        card = self.kwargs.get('card_number')
        return Loan.objects.filter(card_number=card).select_related('book')


class LoanCreateView(CreateView):
    model = Loan
    form_class = LoanCreateForm
    template_name = 'loans/loan_form.html'

    def get_success_url(self):
        return reverse('books:loans_active')

    def form_valid(self, form):
        # model clean() will enforce availability and max loans
        return super().form_valid(form)


class LoanReturnView(View):
    def post(self, request, pk):
        loan = get_object_or_404(Loan, pk=pk)
        loan.mark_returned()
        return redirect('books:loans_active')


# simple convenience redirect for the app root
def index_redirect(request):
    return redirect('books:book_list')
