from django.contrib import admin

from apps.configuration.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    The representation of :class:`configuration.models.Project` in the
    administration interface.
    """
    list_display = ('id', 'name', 'abbreviation', 'active',)
    list_filter = ('active',)
    search_fields = ('name', 'abbreviation',)
