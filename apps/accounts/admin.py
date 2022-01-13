from django import forms
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth.models import Group

from apps.accounts.models import User


class CustomUserChangeForm(forms.ModelForm):
    """
    The form to update a :class:`accounts.models.User` in the
    administration interface.
    """

    def clean_password(self):
        """
        A stub function to prevent errors when validating the form.
        """
        pass


class UserAdmin(auth_admin.UserAdmin):
    """
    The representation of :class:`accounts.models.User` in the
    administration interface.
    """
    form = CustomUserChangeForm

    list_display = (
        'email', 'lastname', 'firstname', 'id', 'is_superuser', 'date_joined',
        'last_login')
    list_filter = ('is_superuser', 'groups')
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ('groups',)

    fieldsets = (
        (None, {'fields': ('email', 'lastname', 'firstname')}),
        ('Permissions', {'fields': ('is_superuser', 'groups')}),
    )
    readonly_fields = ('email',)

    # No new users can be added.
    def has_add_permission(self, request):
        return False


admin.site.register(User, UserAdmin)


# Groups cannot be managed by the admin interface
admin.site.unregister(Group)
