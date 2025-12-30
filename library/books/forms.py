from django import forms
from .models import Loan, Book
from django.core.exceptions import ValidationError
from django.utils import timezone


class LoanCreateForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['book', 'borrower_name', 'borrower_email', 'card_number', 'comments']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit the book choices to those with available copies
        self.fields['book'].queryset = Book.objects.filter(copies_available__gt=0).order_by('title')

    def clean(self):
        cleaned = super().clean()
        book = cleaned.get('book')
        card = cleaned.get('card_number')
        if book and book.copies_available <= 0:
            raise ValidationError("Ce livre n'a pas d'exemplaires disponibles.")
        if card:
            active = Loan.objects.filter(card_number=card).exclude(status__in=[Loan.STATUS_RETURNED, Loan.STATUS_CANCELED]).count()
            if active >= 5:
                raise ValidationError('Cet usager a déjà 5 emprunts actifs.')
        return cleaned
