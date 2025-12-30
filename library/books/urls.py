from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.BookListView.as_view(), name='book_list'),
    path('search/', views.BookListView.as_view(), name='book_search'),
    path('category/<int:category_id>/', views.BookListView.as_view(), name='book_by_category'),
    path('author/<int:author_id>/', views.BookListView.as_view(), name='book_by_author'),
    path('<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),

    # authors
    path('authors/', views.AuthorListView.as_view(), name='author_list'),
    path('authors/search/', views.AuthorListView.as_view(), name='author_search'),
    path('authors/<int:pk>/', views.AuthorDetailView.as_view(), name='author_detail'),

    # loans
    path('loans/active/', views.ActiveLoanListView.as_view(), name='loans_active'),
    path('loans/late/', views.LateLoanListView.as_view(), name='loans_late'),
    path('loans/history/<str:card_number>/', views.UserLoanHistoryView.as_view(), name='loan_history'),
    path('loans/create/', views.LoanCreateView.as_view(), name='loan_create'),
    path('loans/<int:pk>/return/', views.LoanReturnView.as_view(), name='loan_return'),
]