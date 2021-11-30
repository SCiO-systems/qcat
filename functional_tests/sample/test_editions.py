from unittest import mock

from apps.accounts.models import User
from apps.configuration.models import Configuration
from django.conf import settings
from django.core.management import call_command
from apps.questionnaire.models import Questionnaire
from functional_tests.base import FunctionalTest
from functional_tests.pages.sample import SampleDetailPage, SampleEditPage, \
    SampleStepPage

CODE_CHOICES = Configuration.CODE_CHOICES


@mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
class EditionTest(FunctionalTest):
    """
    Sample edition 2018, see release notes in sample_2018.py
    """

    fixtures = [
        'groups_permissions',
        'sample_global_key_values',
        'sample',
        'sample_questionnaire_status',
    ]

    def setUp(self):
        super().setUp()
        call_command('delete_caches')
        self.user = User.objects.get(pk=101)
        with mock.patch.object(
                Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock) \
                as mock_choices:
            mock_choices.return_value = CODE_CHOICES + [('sample', 'sample'), ]
            call_command('runscript', 'sample_2018')

    def tearDown(self):
        super().tearDown()
        from apps.configuration.cache import get_cached_configuration
        get_cached_configuration.cache_clear()

    def test_edit_public_new_config_edition(self, mock_choices):
        return
        mock_choices.return_value = CODE_CHOICES + [('sample', 'sample'), ]

        code = 'sample_3'
        old_version = Questionnaire.objects.get(code=code)

        # A user logs in and goes to the detail page of a public questionnaire
        # where he is the compiler
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': code}

        detail_page.open(login=True, user=self.user)

        # The user sees a hint about a new edition on the detail page
        detail_page.close_edition_modal()
        assert detail_page.has_new_edition()

        # The user creates a new version
        detail_page.create_new_version()

        # The new version is in the new edition
        new_version = Questionnaire.objects.latest('updated')
        assert new_version.configuration.edition == '2018'

        # The data of the old version was cleaned up
        assert old_version.data['qg_2'][0]['key_2'] is not None
        assert new_version.data['qg_2'][0]['key_2'] is None

        assert old_version.data['qg_2'][0]['key_3'] \
            == new_version.data['qg_2'][0]['key_3']

        assert 'qg_5' in old_version.data
        assert 'qg_5' not in new_version.data

        # The old values are still there
        edit_page = SampleEditPage(self)
        assert edit_page.has_text('Foo 3')

        # New questions are available and can be entered
        edit_page.click_edit_category('cat_4')
        step_page = SampleStepPage(self)
        step_page.enter_text(
            step_page.LOC_FORM_INPUT_KEY_68, 'New key for edition 2018')
        step_page.submit_step()
        assert edit_page.has_text('New key for edition 2018')

        # The old values are still there
        assert edit_page.has_text('Foo 3')

        # Questions also have updated labels
        edit_page.click_edit_category('cat_1')
        assert step_page.has_text('Key 1 (edition 2018):')
        step_page.submit_step()

        # The old values are still there
        assert edit_page.has_text('Foo 3')

        # The user submits the version
        edit_page.submit_questionnaire()

        # The version is reviewed (in DB)
        new_version.status = settings.QUESTIONNAIRE_PUBLIC
        new_version.save()

        # The new public version does not have a hint about new editions
        detail_page.open()
        assert not detail_page.has_new_edition()
