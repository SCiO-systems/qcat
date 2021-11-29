import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from elasticmock import elasticmock

from apps.accounts.tests.test_models import create_new_user
from functional_tests.base import FunctionalTest
from apps.questionnaire.models import Questionnaire
from apps.sample.tests.test_views import route_questionnaire_new


@elasticmock
class QuestionnaireTest(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'sample',
    ]

    def test_add_points(self):

        # cat_3_position = get_position_of_category('cat_3', start0=True)

        # Alice logs in
        user_moderator = create_new_user()
        user_moderator.groups = [
            Group.objects.get(pk=3), Group.objects.get(pk=4)]
        self.doLogin(user=user_moderator)

        # She starts editing a new questionnaire, no map is visible
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new))
        self.findByNot('class_name', 'map-preview-container')

        # She goes to a step with the map and sets a point on the map
        self.click_edit_section('cat_3')
        map = self.findBy(
            'xpath', '//div[contains(@class, "map-form-container")]')
        self.scroll_to_element(map)
        import time; time.sleep(1)
        map.click()

        # She saves the step
        self.submit_form_step()

        # In the overview, she now sees a map with the point on it
        self.findBy('class_name', 'map-preview-container')

        # In the database, a geometry was added
        db_questionnaire = Questionnaire.objects.order_by('-id')[0]
        geom = db_questionnaire.geom
        self.assertIsNotNone(geom)

        self.click_edit_section('cat_0')
        self.select_chosen_element(
            'id_qg_location_0_country_chosen', 'Afghanistan')
        self.submit_form_step()

        # In the overview, there is still the map with the point.
        self.findBy('class_name', 'map-preview-container')

        # She edits the questionnaire and adds another point
        self.click_edit_section('cat_3')
        map = self.findBy(
            'xpath', '//div[contains(@class, "map-form-container")]')
        self.scroll_to_element(map)
        import time; time.sleep(1)
        self.findBy('xpath', '//label[@for="qg_39_1_1"]').click()
        self.findBy('xpath', '//label[@for="qg_39_1_1"]').click()
        action = webdriver.common.action_chains.ActionChains(self.browser)
        action.move_to_element_with_offset(map, 5, 5)
        action.click()
        action.perform()

        # She submits the step and sees the map on the overview is updated
        self.submit_form_step()
        self.findBy('class_name', 'map-preview-container')

        # In the database, the geometry was updated
        db_questionnaire = Questionnaire.objects.order_by('-id')[0]
        self.assertNotEqual(db_questionnaire.geom, geom)

        # She publishes the questionnaire
        self.rearrangeStickyMenu()
        self.review_action('submit')
        self.review_action('review')
        self.review_action('publish')

        # She sees that still, the map is there on the overview
        self.findBy('class_name', 'map-preview-container')
