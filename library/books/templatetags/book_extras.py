from django import template
from django.utils.safestring import mark_safe
from ..models import Loan

register = template.Library()


@register.filter
def format_isbn(value):
    if not value:
        return ''
    s = ''.join(ch for ch in str(value) if ch.isdigit())
    if len(s) != 13:
        return value
    # simple grouping: 3-1-4-4-1 (not all ISBN use same grouping but it's ok for display)
    return f"{s[:3]}-{s[3]}-{s[4:8]}-{s[8:12]}-{s[12]}"


@register.filter
def days_overdue(loan):
    try:
        return loan.days_overdue()
    except Exception:
        return 0


@register.filter
def penalty_amount(loan):
    try:
        return loan.penalty_amount()
    except Exception:
        return 0


@register.simple_tag
def loan_status_badge(loan):
    status = getattr(loan, 'status', '')
    mapping = {
        Loan.STATUS_BORROWED: ('Emprunté', 'warning'),
        Loan.STATUS_RETURNED: ('Restitué', 'success'),
        Loan.STATUS_LATE: ('En retard', 'danger'),
        Loan.STATUS_CANCELED: ('Annulé', 'secondary'),
    }
    label, cls = mapping.get(status, (status, 'secondary'))
    return mark_safe(f"<span class='badge bg-{cls}'>{label}</span>")


@register.inclusion_tag('partials/book_card.html')
def book_card(book):
    return {'book': book}
