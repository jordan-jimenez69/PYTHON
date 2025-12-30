from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from books.models import Author, Book, Loan, Category
from django.utils import timezone
from datetime import timedelta


class ModelsTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name='Test', last_name='Author')
        self.cat = Category.objects.create(name='SciFi')
        self.book = Book.objects.create(
            title='Test Book',
            isbn='9780000000002',
            publication_year=2000,
            author=self.author,
            copies_total=2,
            copies_available=2,
            category=self.cat,
            price=Decimal('10.00')
        )

    def test_loan_decrements_and_increments(self):
        loan = Loan.objects.create(book=self.book, borrower_name='A', borrower_email='a@example.com', card_number='111')
        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, 1)
        # mark returned
        loan.status = Loan.STATUS_RETURNED
        loan.save()
        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, 2)

    def test_cannot_loan_if_no_copies(self):
        # use up copies
        Loan.objects.create(book=self.book, borrower_name='A', borrower_email='a@example.com', card_number='111')
        Loan.objects.create(book=self.book, borrower_name='B', borrower_email='b@example.com', card_number='222')
        with self.assertRaises(ValidationError):
            Loan.objects.create(book=self.book, borrower_name='C', borrower_email='c@example.com', card_number='333')

    def test_limit_five_loans_per_user(self):
        # create 5 different books
        books = []
        for i in range(5):
            b = Book.objects.create(
                title=f'B{i}', isbn=f'97800000000{i+3}', publication_year=2000+i, author=self.author, copies_total=1, copies_available=1, price=Decimal('5.00')
            )
            books.append(b)
            Loan.objects.create(book=b, borrower_name='User', borrower_email='u@example.com', card_number='CARD1')
        # attempt 6th
        b6 = Book.objects.create(title='B6', isbn='9780000000010', publication_year=2010, author=self.author, copies_total=1, copies_available=1, price=Decimal('5.00'))
        with self.assertRaises(ValidationError):
            Loan.objects.create(book=b6, borrower_name='User', borrower_email='u@example.com', card_number='CARD1')

    def test_days_overdue_and_penalty(self):
        loan = Loan.objects.create(book=self.book, borrower_name='A', borrower_email='a@example.com', card_number='111')
        # force due_date in the past
        loan.due_date = timezone.now() - timedelta(days=5)
        loan.returned_at = timezone.now()
        loan.save()
        self.assertTrue(loan.days_overdue() >= 5)
        self.assertTrue(loan.penalty_amount() >= 0)

    def test_cannot_delete_book_with_active_loans(self):
        loan = Loan.objects.create(book=self.book, borrower_name='A', borrower_email='a@example.com', card_number='111')
        with self.assertRaises(ValidationError):
            self.book.delete()
        # mark returned and then delete
        loan.status = Loan.STATUS_RETURNED
        loan.save()
        self.book.delete()
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())
