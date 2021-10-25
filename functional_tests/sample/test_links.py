import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from elasticmock import elasticmock

from apps.accounts.models import User
from functional_tests.base import FunctionalTest
from apps.sample.tests.test_views import route_questionnaire_list, \
    route_questionnaire_new
from apps.samplemulti.tests.test_views import route_questionnaire_new as \
    route_questionnaire_new_samplemulti, route_questionnaire_list as \
    route_questionnaire_list_samplemulti
from apps.search.tests.test_index import create_temp_indices

from functional_tests.pages.questionnaire import QuestionnaireStepPage
from functional_tests.pages.sample import SampleDetailPage, SampleEditPage, \
    SampleStepPage
from functional_tests.pages.samplemulti import SampleMultiDetailPage, \
    SampleMultiEditPage, SampleMultiStepPage


@elasticmock
class LinkTests(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'sample',
        'samplemulti',
        'sample_samplemulti_questionnaires',
    ]

    """
    1
        configurations: sample
        code: sample_1
        key_1 (en): This is the first key
        links: 3

    2
        configurations: sample
        code: sample_2
        key_1 (en): Foo
        links: -

    3
        configurations: samplemulti
        code: samplemulti_1
        key_1 (en): This is key 1a
        links: 1

    4
        configurations: samplemulti
        code: samplemulti_2
        key_1 (en): This is key 1b
        links: -
    """

    def setUp(self):
        super(LinkTests, self).setUp()
        create_temp_indices([('sample', '2015'), ('samplemulti', '2015')])

    def test_do_not_show_deleted_links_in_form(self):

        user = User.objects.get(pk=101)
        samplemulti_link = 'This is key 1a'
        sample_link = 'This is the first key.'

        # User goes to the SAMPLE questionnaire and sees the link
        detail_page_sample = SampleDetailPage(self)
        detail_page_sample.route_kwargs = {'identifier': 'sample_1'}
        detail_page_sample.open(login=True, user=user)
        assert detail_page_sample.has_text(samplemulti_link)

        # User starts editing the questionnaire
        detail_page_sample.create_new_version()
        edit_page = SampleEditPage(self)
        assert edit_page.has_text(samplemulti_link)

        # User opens the step with the link and sees the link is there
        edit_page.click_edit_category('cat_5')
        step_page = QuestionnaireStepPage(self)
        assert step_page.check_links([samplemulti_link])

        # User opens the details page of the SAMPLEMULTI questionnaire
        detail_page_multi = SampleMultiDetailPage(self)
        detail_page_multi.route_kwargs = {'identifier': 'samplemulti_1'}
        detail_page_multi.open()
        assert detail_page_multi.has_text(sample_link)

        # User deletes the questionnaire
        detail_page_multi.delete_questionnaire()

        # User opens the detail page of the SAMPLE questionnaire again. The link
        # is not there anymore.
        detail_page_sample.open()
        assert not detail_page_sample.has_text(samplemulti_link)

        # The link is not on the edit page either
        detail_page_sample.edit_questionnaire()
        assert not detail_page_sample.has_text(samplemulti_link)

        # Also on the step edit page, no link
        edit_page.click_edit_category('cat_5')
        assert step_page.check_links([])

        # The step can be submitted without an error
        step_page.submit_step()

    def test_show_only_one_linked_version(self):

        sample_title = 'This is the first key.'
        samplemulti_title = 'This is key 1a'
        samplemulti_changed_text = ' (changed)'
        samplemulti_title_changed = samplemulti_title + samplemulti_changed_text

        # Alice logs in
        # She goes to the SAMPLE questionnaire and sees the link
        user_1 = User.objects.get(pk=101)
        sample_detail_page = SampleDetailPage(self)
        sample_detail_page.route_kwargs = {'identifier': 'sample_1'}
        sample_detail_page.open(login=True, user=user_1)
        sample_detail_page.expand_details()

        expected_samplemulti_links = [
            {
                'title': samplemulti_title,
                'configuration': 'samplemulti',
            }
        ]
        sample_detail_page.check_linked_questionnaires(
            expected=expected_samplemulti_links)

        # She goes to the MULTISAMPLE questionnaire and sees the link
        sample_detail_page.click_linked_questionnaire(index=0)

        samplemulti_detail_page = SampleMultiDetailPage(self)
        samplemulti_detail_page.expand_details()

        expected_sample_links = [
            {
                'title': sample_title,
                'configuration': 'sample',
            }
        ]
        samplemulti_detail_page.check_linked_questionnaires(
            expected=expected_sample_links)

        # She edits the MULTISAMPLE questionnaire and sees only one
        # version is linked (still the same)
        samplemulti_detail_page.create_new_version()
        samplemulti_edit_page = SampleMultiEditPage(self)
        samplemulti_edit_page.click_edit_category('mcat_1')

        samplemulti_step_page = SampleMultiStepPage(self)
        samplemulti_step_page.enter_text(
            samplemulti_step_page.LOC_QUESTION_MQG01_MKEY01,
            samplemulti_changed_text)

        # She submits the step
        samplemulti_step_page.submit_step()

        # She sees that only one questionnaire is linked
        samplemulti_edit_page.expand_details()
        samplemulti_edit_page.check_linked_questionnaires(
            expected=expected_sample_links)

        # She goes to the SAMPLE questionnaire and sees only one version
        # is linked (the pending one)
        samplemulti_edit_page.click_linked_questionnaire(index=0)

        expected_samplemulti_links_changed = [
            {
                'title': samplemulti_title_changed,
                'configuration': 'samplemulti',
            }
        ]
        sample_detail_page.check_linked_questionnaires(
            expected=expected_samplemulti_links_changed)

        # She even creates a new version and opens the form and sees there is
        # only one version
        sample_detail_page.create_new_version()
        sample_edit_page = SampleEditPage(self)
        sample_edit_page.click_edit_category('cat_5')
        sample_step_page = SampleStepPage(self)
        sample_step_page.check_links([samplemulti_title_changed])
        sample_step_page.back_without_saving()

        # She logs out and sees only one questionnaire is linked (the
        # active one)
        sample_detail_page.logout()
        sample_detail_page.open()
        sample_detail_page.expand_details()
        sample_detail_page.check_linked_questionnaires(
            expected=expected_samplemulti_links)

        # She logs in as a different user and sees only one version is
        # linked (the active one)
        user_2 = User.objects.get(pk=102)
        sample_detail_page.open(login=True, user=user_2)
        sample_detail_page.expand_details()
        sample_detail_page.check_linked_questionnaires(
            expected=expected_samplemulti_links)

    def test_add_only_one_side_of_link_to_es_when_publishing(self):

        sample_name = 'asdfasdf'
        samplemulti_name = 'foobar'

        # Alice logs in
        user_alice = User.objects.get(pk=101)
        user_alice.groups = [Group.objects.get(pk=3), Group.objects.get(pk=4)]
        self.doLogin(user=user_alice)

        # She goes to the list page
        self.browser.get(self.live_server_url + reverse(route_questionnaire_list))

        # She sees two entries
        list_entries = self.findManyBy('xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 2)

        # She goes to the SAMPLEMULTI list view and sees 2 entries
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list_samplemulti))
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 2)

        # She enters a new SAMPLE questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new))
        self.click_edit_section('cat_1')
        self.findBy('name', 'qg_1-0-original_key_1').send_keys(sample_name)
        self.submit_form_step()

        sample_url = self.browser.current_url

        # She also enters a new SAMPLEMULTI questionnaire which links to the
        # newly created SAMPLE questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new_samplemulti))
        self.click_edit_section('mcat_1')
        self.findBy('name', 'mqg_01-0-original_mkey_01').send_keys(
            samplemulti_name)
        self.findBy(
            'xpath', '//input[contains(@class, "link-search-field")]'
                     '[1]').send_keys(sample_name)
        self.wait_for('xpath', '//li[@class="ui-menu-item"]')
        self.findBy(
            'xpath',
            '//li[@class="ui-menu-item"]//strong[text()="{}"'
            ']'.format(sample_name)).click()
        self.submit_form_step()

        samplemulti_url = self.browser.current_url

        # She goes to the list view and sees there are still only 2 entries
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 2)

        # She goes to the list view of SAMPLEMULTI and sees there are still
        # only 2 entries
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list_samplemulti))
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 2)

        # She goes back to the SAMPLEMULTI questionnaire and publishes it
        self.browser.get(samplemulti_url)
        import time; time.sleep(1)  # I know, not nice ...
        self.review_action('submit')
        self.review_action('review')
        self.review_action('publish')

        # She goes to the list view and sees there are still 2 entries (as the
        # SAMPLEMULTI questionnaires are not visible from SAMPLE)
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 2)

        # She goes to the SAMPLEMULTI list view and sees there are now 3 entries
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list_samplemulti))
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 3)

        # The first of the list is the newly created one, it does not have a
        # link attached (as the other side of the link is still "draft")
        self.findByNot(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//ul['
                     'contains(@class, "tech-attached")]/li/a')

        # She goes to the SAMPLE questionnaire and publishes it
        self.browser.get(sample_url)
        self.wait_for('xpath', '//a[@data-reveal-id="confirm-submit"]')
        self.review_action('submit')
        self.review_action('review')
        self.review_action('publish')

        # She goes to the SAMPLE list view and sees there are now 3 entries
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 3)

        # The first of the list is the newly created one and it does have a link
        # attached
        link_count = self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//ul['
                     'contains(@class, "tech-attached")]/li/a')
        self.assertEqual(link_count.text, '')

        # She goes to the SAMPLEMULTI list view and sees there are 3 entries
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list_samplemulti))
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 3)

        # The first of the list is the newly created one and it does now have a
        # link attached
        link_count = self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[2]//ul['
                     'contains(@class, "tech-attached")]/li/a')
        self.assertEqual(link_count.text, '')

    def test_do_not_add_duplicate_links_when_editing(self):
        # Alice logs in
        user_alice = User.objects.get(pk=101)
        user_alice.groups = [Group.objects.get(pk=3), Group.objects.get(pk=4)]
        self.doLogin(user=user_alice)

        # She enters a new SAMPLE questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new))
        self.click_edit_section('cat_1')
        self.findBy('name', 'qg_1-0-original_key_1').send_keys('Sample Q1')
        self.submit_form_step()

        sample_url = self.browser.current_url

        # She also enters a new SAMPLEMULTI questionnaire which links to the
        # newly created SAMPLE questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new_samplemulti))
        self.click_edit_section('mcat_1')
        self.findBy('name', 'mqg_01-0-original_mkey_01').send_keys(
            'Samplemulti Q1')
        self.findBy(
            'xpath', '//input[contains(@class, "link-search-field")]'
                     '[1]').send_keys('Sample Q1')
        self.wait_for('xpath', '//li[@class="ui-menu-item"]')
        self.findBy(
            'xpath',
            '//li[@class="ui-menu-item"]//strong[text()="Sample Q1"'
            ']').click()
        self.submit_form_step()

        samplemulti_url = self.browser.current_url

        # She sees the added link in 2 places, but each time only once!
        section_xpath = '//section[@id="mcat_1"]'
        link_xpath = '//section[@id="links"]'
        for xpath in [section_xpath, link_xpath]:
            sample_links = self.findManyBy(
                'xpath', '{}//article[contains(@class, "is-sample")]//a['
                         'contains(text(), "Sample Q1")]'.format(xpath))
            self.assertEqual(len(sample_links), 1)
            self.findBy('xpath', '{}//article[contains(@class, "is-sample")]//'
                                 'span[contains(@class, "tech-status") and '
                                 'contains(@class, "is-draft")]'.format(xpath))

        # She goes to the Sample Questionnaire. Again, she sees the link in 2
        # places, but each time only once!
        self.browser.get(sample_url)
        section_xpath = '//section[@id="cat_5"]'
        link_xpath = '//section[@id="links"]'
        for xpath in [section_xpath, link_xpath]:
            samplemulti_links = self.findManyBy(
                'xpath', '{}//article[contains(@class, "is-samplemulti")]//'
                         'a[contains(text(), "Samplemulti Q1")]'.format(xpath))
            self.assertEqual(len(samplemulti_links), 1)
            self.findBy(
                'xpath', '{}//article[contains(@class, "is-samplemulti")]//span['
                         'contains(@class, "tech-status") and contains('
                         '@class, "is-draft")]'.format(xpath))

        # She submits the Sample Questionnaire
        self.review_action('submit')

        # She edits the Questionnaire (only opens the section with the link and
        # closes it again)
        self.findBy('xpath', '//a[text()="Edit" and @type="submit"]').click()
        self.click_edit_section('cat_1')
        self.submit_form_step()

        # She sees that there is still only one link visible
        section_xpath = '//section[@id="cat_5"]'
        link_xpath = '//section[@id="links"]'
        for xpath in [section_xpath, link_xpath]:
            samplemulti_links = self.findManyBy(
                'xpath', '{}//article[contains(@class, "is-samplemulti")]//'
                         'a[contains(text(), "Samplemulti Q1")]'.format(xpath))
            self.assertEqual(len(samplemulti_links), 1)
            self.findBy(
                'xpath',
                '{}//article[contains(@class, "is-samplemulti")]//span['
                'contains(@class, "tech-status") and contains('
                '@class, "is-draft")]'.format(xpath))

        # She goes to the Samplmulti Questionnaire and sees the link (only once)
        self.browser.get(samplemulti_url)
        section_xpath = '//section[@id="mcat_1"]'
        link_xpath = '//section[@id="links"]'
        for xpath in [section_xpath, link_xpath]:
            sample_links = self.findManyBy(
                'xpath', '{}//article[contains(@class, "is-sample")]//a['
                         'contains(text(), "Sample Q1")]'.format(xpath))
            self.assertEqual(len(sample_links), 1)
            self.findBy('xpath', '{}//article[contains(@class, "is-sample")]//'
                                 'span[contains(@class, "tech-status") and '
                                 'contains(@class, "is-submitted")]'.format(
                xpath))

        # She submits the Samplemulti Questionnaire
        self.review_action('submit')

        # She edits the Questionnaire (only opens the section with the link and
        # closes it again)
        self.findBy('xpath', '//a[text()="Edit" and @type="submit"]').click()
        self.click_edit_section('mcat_1')
        self.submit_form_step()

        self.browser.get(samplemulti_url)
        section_xpath = '//section[@id="mcat_1"]'
        link_xpath = '//section[@id="links"]'
        for xpath in [section_xpath, link_xpath]:
            sample_links = self.findManyBy(
                'xpath', '{}//article[contains(@class, "is-sample")]//a['
                         'contains(text(), "Sample Q1")]'.format(xpath))
            self.assertEqual(len(sample_links), 1)
            self.findBy('xpath', '{}//article[contains(@class, "is-sample")]//'
                                 'span[contains(@class, "tech-status") and '
                                 'contains(@class, "is-submitted")]'.format(
                xpath))

        # From Sample Questionnaire, still only one version is linked
        self.browser.get(sample_url)
        section_xpath = '//section[@id="cat_5"]'
        link_xpath = '//section[@id="links"]'
        for xpath in [section_xpath, link_xpath]:
            samplemulti_links = self.findManyBy(
                'xpath', '{}//article[contains(@class, "is-samplemulti")]//'
                         'a[contains(text(), "Samplemulti Q1")]'.format(xpath))
            self.assertEqual(len(samplemulti_links), 1)
            self.findBy(
                'xpath',
                '{}//article[contains(@class, "is-samplemulti")]//span['
                'contains(@class, "tech-status") and contains('
                '@class, "is-submitted")]'.format(xpath))

        # She publishes the Sample Questionnaire and still, only one link
        self.hide_notifications()
        self.review_action('review')
        self.review_action('publish')
        section_xpath = '//section[@id="cat_5"]'
        link_xpath = '//section[@id="links"]'
        for xpath in [section_xpath, link_xpath]:
            samplemulti_links = self.findManyBy(
                'xpath', '{}//article[contains(@class, "is-samplemulti")]//'
                         'a[contains(text(), "Samplemulti Q1")]'.format(xpath))
            self.assertEqual(len(samplemulti_links), 1)
            self.findBy(
                'xpath',
                '{}//article[contains(@class, "is-samplemulti")]//span['
                'contains(@class, "tech-status") and contains('
                '@class, "is-submitted")]'.format(xpath))

        # From Samplemulti Questionnaire, still only one version is linked
        self.browser.get(samplemulti_url)
        section_xpath = '//section[@id="mcat_1"]'
        link_xpath = '//section[@id="links"]'
        for xpath in [section_xpath, link_xpath]:
            sample_links = self.findManyBy(
                'xpath', '{}//article[contains(@class, "is-sample")]//a['
                         'contains(text(), "Sample Q1")]'.format(xpath))
            self.assertEqual(len(sample_links), 1)
            self.findByNot('xpath', '{}//article[contains(@class, "is-sample")]//'
                                 'span[contains(@class, "tech-status")]'.format(
                xpath))
