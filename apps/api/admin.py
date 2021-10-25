from django.contrib import admin

from .models import RequestLog, NoteToken


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_filter = ('user', 'access', )
    date_hierarchy = 'access'
    list_display = ['__str__', 'access']


@admin.register(NoteToken)
class NoteTokenAdmin(admin.ModelAdmin):
    fields = ('user', 'notes', )
    list_display = ['__str__', 'user', 'created', 'requests_from_user']
