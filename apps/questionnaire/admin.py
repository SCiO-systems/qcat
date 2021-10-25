from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from apps.configuration.models import Configuration, Country
from .models import Lock, Questionnaire


@admin.register(Lock)
class LockAdmin(admin.ModelAdmin):

    def questionnaire_code(self):
        return self.questionnaire.code

    list_display = ['id', questionnaire_code, 'user', 'start', 'is_finished']


class NewEditionFilter(admin.SimpleListFilter):
    title = _('Edition update required')
    parameter_name = 'has_new_edition'

    def lookups(self, request, model_admin):
        return (
            (True, _('Yes')),
            (False, _('No')),
        )

    def queryset(self, request, queryset):
        """
        Filter for latest configurations.
        """
        if self.value() is None:
            return queryset

        latest_configurations = Configuration.objects.distinct(
            'code'
        ).order_by(
            'code', '-created'
        ).values_list(
            'id', flat=True
        )
        if self.value() == 'True':
            return queryset.exclude(configuration_id__in=latest_configurations)
        else:
            return queryset.filter(configuration__id__in=latest_configurations)


class CountryFilter(admin.SimpleListFilter):
    title = _('Country')
    parameter_name = 'country'

    def lookups(self, request, model_admin):
        return ((country.keyword, country.__str__()) for country in Country.all().order_by('keyword'))

    def queryset(self, request, queryset):
        """
        This lookup assumes that only one country is stored per questionnaire, in the
        key 'qq_location'.
        """
        if self.value() is None:
            return queryset
        return queryset.filter(data__qg_location__0__country__icontains=self.value())


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    actions = None
    list_display_links = None
    list_display = [
        'id', 'code', 'get_name', 'status', 'updated', 'get_compilers', 'get_countries',
        'has_new_edition', 'edit_url'
    ]
    list_filter = ['configuration', 'status', NewEditionFilter, CountryFilter]

    def has_new_edition(self, obj):
        return obj.configuration_object.has_new_edition
    has_new_edition.boolean = True
    has_new_edition.short_description = _('Edition update available')

    def get_compilers(selfs, obj):
        return [compiler.get('name', '') for compiler in obj.compilers]
    get_compilers.short_description = _('Compiler')

    def get_countries(self, obj):
        return obj.get_countries()
    get_countries.short_description = _('Country')

    def edit_url(self, obj):
        return mark_safe(
            f'<a href="{obj.get_edit_url()}" target="_blank">Edit</a>'
        )
