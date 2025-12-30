from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from .models import Loan, Book


@receiver(pre_save, sender=Loan)
def loan_pre_save(sender, instance, **kwargs):
    """Before saving a loan, ensure availability and reserve a copy for new loans."""
    # store old status for post_save
    if instance.pk:
        try:
            old = Loan.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Loan.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

    # On creation: check availability, limit of 5 active loans and decrement
    if instance._state.adding and instance.status == Loan.STATUS_BORROWED:
        if instance.book.copies_available <= 0:
            raise ValidationError('Ce livre n\'a pas d\'exemplaires disponibles.')
        # check active loans for this card
        active_count = Loan.objects.filter(card_number=instance.card_number).filter(~Q(status=Loan.STATUS_RETURNED) & ~Q(status=Loan.STATUS_CANCELED)).count()
        if active_count >= 5:
            raise ValidationError('Cet usager a déjà 5 emprunts actifs.')
        # decrement inside a transaction to reduce race window
        with transaction.atomic():
            instance.book.decrement_available()


@receiver(post_save, sender=Loan)
def loan_post_save(sender, instance, created, **kwargs):
    """After saving a loan, handle status changes (return) to increment availability."""
    # If status changed to returned, increment available
    old_status = getattr(instance, '_old_status', None)
    if not created and old_status != instance.status and instance.status == Loan.STATUS_RETURNED:
        with transaction.atomic():
            instance.book.increment_available()


@receiver(post_delete, sender=Loan)
def loan_post_delete(sender, instance, **kwargs):
    """If a loan is deleted and it wasn't returned, free the copy."""
    if instance.status not in [Loan.STATUS_RETURNED, Loan.STATUS_CANCELED]:
        try:
            with transaction.atomic():
                instance.book.increment_available()
        except Exception:
            # don't raise to avoid failures during cleanup
            pass
