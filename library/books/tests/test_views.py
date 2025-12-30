from django.test import TestCase
from django.urls import reverse
from books.models import Book, Loan, Author


class BookViewsTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name='Jean', last_name='Dupont')
        for i in range(15):
            isbn = '978' + str(1000000000 + i)  # ensure unique 13-digit ISBNs
            Book.objects.create(title=f'Book {i}', isbn=isbn, author=self.author, copies_available=1, copies_total=1)

    def test_book_list_pagination(self):
        url = reverse('books:book_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('books', resp.context)
        # paginate_by = 8, so should have 8 on first page
        self.assertEqual(len(resp.context['books']), 8)

    def test_book_detail(self):
        book = Book.objects.first()
        url = reverse('books:book_detail', args=[book.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, book.title)


class LoanViewsTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name='Alice', last_name='Martin')
        self.book = Book.objects.create(title='LoanBook', isbn='9780000000001', author=self.author, copies_available=2, copies_total=2)

    def test_create_loan_fbv(self):
        url = reverse('books:loan_create_fbv')
        data = {
            'book': self.book.pk,
            'borrower_name': 'John Doe',
            'borrower_email': 'john@example.com',
            'card_number': 'CARD123',
            'comments': ''
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, 1)
        self.assertTrue(Loan.objects.filter(card_number='CARD123').exists())

    def test_return_loan_fbv(self):
        loan = Loan.objects.create(book=self.book, borrower_name='A', borrower_email='a@b.com', card_number='X')
        url = reverse('books:loan_return_fbv', args=[loan.pk])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.STATUS_RETURNED)
