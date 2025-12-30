from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import timedelta, date
from django.db.models import Q


def validate_isbn13(value):
    """Validate ISBN-13: 13 digits with correct checksum."""
    if not value:
        return
    if not value.isdigit() or len(value) != 13:
        raise ValidationError('L\'ISBN doit contenir 13 chiffres.')
    # checksum calculation
    total = 0
    for i, ch in enumerate(value[:12]):
        n = int(ch)
        total += n if i % 2 == 0 else n * 3
    check = (10 - (total % 10)) % 10
    if check != int(value[12]):
        raise ValidationError('ISBN-13 invalide (checksum incorrect).')


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Author(models.Model):
    # allow blank for migration from previous `name` field
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    biography = models.TextField(blank=True)
    date_of_death = models.DateField(null=True, blank=True)
    website = models.URLField(blank=True)
    photo = models.ImageField(upload_to='authors/', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['first_name', 'last_name'], name='unique_author_full_name')
        ]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class Book(models.Model):
    title = models.CharField(max_length=300)
    isbn = models.CharField(max_length=13, unique=True, validators=[validate_isbn13])
    publication_year = models.PositiveIntegerField(validators=[MinValueValidator(1450)], null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name='books')
    copies_available = models.PositiveIntegerField(default=1)
    copies_total = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    language = models.CharField(max_length=30, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    date_added = models.DateTimeField(auto_now_add=True, null=True)

    def clean(self):
        # publication year can't be in the future
        current_year = date.today().year
        if self.publication_year and not (1450 <= self.publication_year <= current_year):
            raise ValidationError({'publication_year': f'L\'année doit être entre 1450 et {current_year}.'})
        # copies_available cannot exceed copies_total
        if self.copies_available > self.copies_total:
            raise ValidationError({'copies_available': 'Le nombre d\'exemplaires disponibles ne peut dépasser le total.'})

    def __str__(self):
        return self.title

    def available(self):
        return self.copies_available > 0

    def decrement_available(self, qty=1):
        if self.copies_available - qty < 0:
            raise ValidationError("Pas assez d'exemplaires disponibles.")
        self.copies_available -= qty
        self.save()

    def increment_available(self, qty=1):
        if self.copies_available + qty > self.copies_total:
            raise ValidationError("Le nombre d'exemplaires disponibles ne peut dépasser le total.")
        self.copies_available += qty
        self.save()

    def delete(self, *args, **kwargs):
        """Prevent deletion if there are active loans (borrowed or late).
        If only returned/canceled loans exist, delete them first then delete the book."""
        active = self.loans.exclude(status__in=[Loan.STATUS_RETURNED, Loan.STATUS_CANCELED])
        if active.exists():
            raise ValidationError("Impossible de supprimer ce livre : il existe des emprunts actifs.")
        # Remove returned/canceled loans so PROTECT doesn't block deletion
        self.loans.filter(status__in=[Loan.STATUS_RETURNED, Loan.STATUS_CANCELED]).delete()
        return super().delete(*args, **kwargs)


class Loan(models.Model):
    STATUS_BORROWED = 'borrowed'
    STATUS_RETURNED = 'returned'
    STATUS_LATE = 'late'
    STATUS_CANCELED = 'canceled'

    STATUS_CHOICES = [
        (STATUS_BORROWED, 'Emprunté'),
        (STATUS_RETURNED, 'Restitué'),
        (STATUS_LATE, 'En retard'),
        (STATUS_CANCELED, 'Annulé'),
    ]

    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='loans')
    borrower_name = models.CharField(max_length=200)
    borrower_email = models.EmailField()
    card_number = models.CharField(max_length=50)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_BORROWED)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ['-borrowed_at']

    def clean(self):
        # Ensure book has available copies when creating a loan
        if self._state.adding and (self.book.copies_available <= 0):
            raise ValidationError('Ce livre n\'a pas d\'exemplaires disponibles.')
        # Check borrower doesn't exceed 5 active loans
        from django.db.models import Q
        active_count = Loan.objects.filter(card_number=self.card_number).filter(~Q(status=self.STATUS_RETURNED) & ~Q(status=self.STATUS_CANCELED)).count()
        if self._state.adding and active_count >= 5:
            raise ValidationError('Cet usager a déjà 5 emprunts actifs.')

    def save(self, *args, **kwargs):
        # On create set due_date to borrowed_at + 14 days
        if not self.due_date:
            now = timezone.now()
            if not self.borrowed_at:
                self.borrowed_at = now
            self.due_date = self.borrowed_at + timedelta(days=14)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        ref = self.returned_at or timezone.now()
        return self.due_date and (ref > self.due_date)

    def days_overdue(self):
        if not self.due_date:
            return 0
        ref = self.returned_at or timezone.now()
        delta = ref - self.due_date
        return max(0, delta.days)

    def penalty_amount(self):
        per_day = getattr(settings, 'LOAN_PENALTY_PER_DAY', Decimal('0.50'))
        return Decimal(self.days_overdue()) * Decimal(per_day)

    def mark_returned(self):
        if self.status == self.STATUS_RETURNED:
            return
        self.returned_at = timezone.now()
        self.status = self.STATUS_RETURNED
        self.save()

    def __str__(self):
        return f"{self.book.title} — {self.borrower_name} ({self.status})"
