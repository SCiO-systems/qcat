from django.contrib.auth.models import Group, Permission  # noqa

from apps.qcat.tests import TestCase


class InitialGroupsTest(TestCase):

    fixtures = [
        'groups_permissions',
    ]

    def test_all_groups_are_loaded(self):
        self.assertEqual(Group.objects.count(), 5)

    def test_administrators_have_all_permissions(self):
        pass
        # admin_group = Group.objects.get(name='Administrators')
        # self.assertEqual(
        #     admin_group.permissions.count(), Permission.objects.count())


class InitialPermissionsTest(TestCase):

    def test_all_permissions_are_loaded(self):
        pass
        # permissions = Permission.objects.count()
        # self.assertEqual(permissions, 56)
