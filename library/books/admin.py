from django.contrib import admin, messages
from django.utils import timezone
from django.db.models import Count
from django.core.exceptions import ValidationError

from .models import Author, Book, Loan, Category


class LoanInline(admin.TabularInline):
    model = Loan
    extra = 0
    fields = ('borrower_name', 'borrower_email', 'card_number', 'borrowed_at', 'due_date', 'status')
    readonly_fields = ('borrower_name', 'borrower_email', 'card_number', 'borrowed_at', 'due_date', 'status')
    can_delete = False


class BookInline(admin.TabularInline):
    model = Book
    fields = ('title', 'publication_year', 'copies_available')
    readonly_fields = ('title', 'publication_year', 'copies_available')
    extra = 0


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'nationality', 'birth_date')
    search_fields = ('first_name', 'last_name')
    list_filter = ('nationality',)
    inlines = (BookInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


@admin.action(description='Marquer les livres sélectionnés comme indisponibles')
def make_unavailable(modeladmin, request, queryset):
    updated = queryset.update(copies_available=0)
    messages.success(request, f'{updated} livre(s) marqués comme indisponibles.')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'category', 'copies_available')
    list_filter = ('category', 'author', 'publication_year')
    search_fields = ('title', 'isbn', 'author__first_name', 'author__last_name')
    actions = [make_unavailable]
    readonly_fields = ('date_added',)
    inlines = (LoanInline,)
    fieldsets = (
        ('Informations', {'fields': ('title', 'author', 'isbn', 'category', 'publication_year', 'language', 'publisher', 'pages')}),
        ('Disponibilité', {'fields': ('copies_total', 'copies_available')}),
        ('Média & description', {'fields': ('cover', 'description')}),
        ('Dates', {'fields': ('date_added',)}),
    )

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
        except ValidationError as e:
            self.message_user(request, f'Erreur de validation: {e}', level=messages.ERROR)
            raise
        super().save_model(request, obj, form, change)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower_name', 'borrower_email', 'card_number', 'borrowed_at', 'status', 'penalty')
    list_filter = ('status', 'borrowed_at')
    search_fields = ('borrower_name', 'borrower_email', 'card_number', 'book__title')
    actions = ['mark_returned']
    readonly_fields = ('borrowed_at', 'due_date', 'returned_at')

    def penalty(self, obj):
        return obj.penalty_amount()
    penalty.short_description = 'Pénalité (€)'

    @admin.action(description='Marquer les emprunts sélectionnés comme retournés')
    def mark_returned(self, request, queryset):
        count = 0
        for loan in queryset:
            if loan.status != Loan.STATUS_RETURNED:
                loan.mark_returned()
                count += 1
        messages.success(request, f'{count} emprunt(s) marqué(s) comme retournés.')

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
        except ValidationError as e:
            self.message_user(request, f'Erreur de validation: {e}', level=messages.ERROR)
            raise
        super().save_model(request, obj, form, change)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'book_count')
    search_fields = ('name',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_book_count=Count('books'))

    def book_count(self, obj):
        return obj._book_count
    book_count.short_description = 'Nombre de livres'


# Admin site customization
admin.site.site_header = 'Administration Bibliothèque'
admin.site.site_title = 'Bibliothèque — Admin'
admin.site.index_title = 'Tableau de bord'

