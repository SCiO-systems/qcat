import logging
from elasticmock import elasticmock
from unittest.mock import patch, MagicMock, sentinel, Mock

import pytest
from django.conf import settings
from django.http import Http404
from django.test import RequestFactory
from rest_framework.test import force_authenticate, APIRequestFactory
from rest_framework.response import Response

from apps.accounts.tests.test_models import create_new_user
from apps.qcat.tests import TestCase
from apps.questionnaire.models import Questionnaire
from apps.questionnaire.serializers import QuestionnaireSerializer
from apps.questionnaire.api.views import QuestionnaireListView, \
    QuestionnaireDetailView,  QuestionnaireAPIMixin, \
    ConfiguredQuestionnaireDetailView
from apps.search.tests.test_index import create_temp_indices


@elasticmock
class QuestionnaireListViewTest(TestCase):
    fixtures = [
        'global_key_values',
        'sample',
        'sample_questionnaires',
    ]

    def setUp(self):
        #create_temp_indices([('sample', '2015')])
        self.factory = RequestFactory()
        self.url = '/en/api/v1/questionnaires/sample_1/'
        self.request = self.factory.get(self.url)
        self.request.version = 'v1'
        self.view = self.setup_view(
            QuestionnaireListView(), self.request, identifier='sample_1'
        )
        self.view.configuration_code = 'sample'

    def test_logs_call(self):
        """
        Use the requestfactory from the rest-framework, as this handles the
        custom token authentication nicely.
        """
        user = create_new_user()
        request = APIRequestFactory().get(self.url)
        force_authenticate(request, user=user)
        with patch('api.models.RequestLog.save') as mock_save:
            view = QuestionnaireListView()
            view.configuration_code = 'sample'
            view.get_es_results = Mock()
            view.get_es_results.return_value = {}
            view.dispatch(request)
            mock_save.assert_called_once_with()


    def test_api_detail_url(self):
        questionnaire = Questionnaire.objects.get(code='sample_1')
        serialized = QuestionnaireSerializer(questionnaire).data
        item = self.view.replace_keys(es_hit={'_source': serialized})
        self.assertEqual(
            item.get('api_url'), '/en/api/v1/questionnaires/sample_1/'
        )

    def test_current_page(self):
        request = self.factory.get('{}?page=5'.format(self.url))
        request.version = 'v1'
        view = self.setup_view(self.view, request, identifier='sample_1')
        view.set_attributes()
        view.configuration_code = 'sample'
        view.get_elasticsearch_items()
        self.assertEqual(view.current_page, 5)

    @patch('apps.questionnaire.views.get_configuration_index_filter')
    @patch('apps.questionnaire.views.advanced_search')
    def test_access_elasticsearch(
            self, mock_advanced_search, mock_get_configuration_index_filter):
        mock_get_configuration_index_filter.return_value = ['sample']
        mock_advanced_search.return_value = {}
        self.view.get(self.request)
        mock_advanced_search.assert_called_once_with(
            limit=settings.API_PAGE_SIZE,
            offset=0,
            filter_params=[],
            query_string='',
            configuration_codes=['sample'],
        )

    @patch('apps.questionnaire.views.advanced_search')
    def test_pagination(self, mock_advanced_search):
        mock_advanced_search.return_value = {}
        with patch('apps.questionnaire.view_utils.ESPagination.__init__') as mock:
            mock.return_value = None
            self.view.get_es_paginated_results({})
            mock.assert_called_once_with([], 0)

    @patch('apps.questionnaire.api.views.QuestionnaireListView._get_paginate_link')
    def test_next_link(self, mock_get_paginate_link):
        view = self.setup_view(self.view, self.request, identifier='sample_1')
        view.current_page = 2
        view.get_next_link()
        mock_get_paginate_link.assert_called_with(3)

    @patch('apps.questionnaire.api.views.QuestionnaireListView._get_paginate_link')
    def test_previous_links(self, mock_get_paginate_link):
        view = self.setup_view(self.view, self.request, identifier='sample_1')
        view.current_page = 2
        view.get_previous_link()
        mock_get_paginate_link.assert_called_with(1)

    def test_response_type(self):
        self.view.get_es_results = Mock()
        self.view.get_es_results.return_value = {}
        response = self.view.get(self.request)
        self.assertIsInstance(response, Response)

    def test_language_text_mapping(self):
        data = {'a': 'foo'}
        self.assertEqual(
            self.view.language_text_mapping(**data),
            [{'language': 'a', 'text': 'foo'}]
        )

    @patch('apps.questionnaire.views.get_configuration_index_filter')
    @patch.object(QuestionnaireAPIMixin, 'update_dict_keys')
    def test_v1_filter(
            self, mock_update_dict_keys, mock_get_configuration_index_filter):
        mock_get_configuration_index_filter.return_value = ['sample']
        request = self.factory.get(self.url)
        request.version = 'v1'
        view = self.setup_view(self.view, request, identifier='sample_1')
        view.get(self.request)
        self.assertTrue(mock_update_dict_keys.called)

    @patch('apps.questionnaire.views.get_configuration_index_filter')
    @patch.object(QuestionnaireAPIMixin, 'filter_dict')
    def test_v2_filter(
            self, mock_filter_dict, mock_get_configuration_index_filter):
        mock_get_configuration_index_filter.return_value = ['sample']
        request = self.factory.get(self.url)
        request.version = 'v2'
        view = self.setup_view(self.view, request, identifier='sample_1')
        view.get(self.request)
        self.assertTrue(mock_filter_dict.called)

    def test_api_url_detail_v1(self):
        items = [{'code': 'spam', 'configuration': 'sample'}]
        updated = list(self.view.filter_dict(items))
        self.assertEqual(
            updated[0]['details'], '/en/api/v1/questionnaires/spam/'
        )

    def test_api_url_detail_v2(self):
        items = [{'code': 'spam', 'configuration': 'sample'}]
        request = self.request
        request.version = 'v2'
        view = self.setup_view(self.view, request)
        updated = list(view.filter_dict(items))
        self.assertEqual(
            updated[0]['details'], '/en/api/v2/questionnaires/spam/'
        )

    @patch('apps.questionnaire.api.views.reverse')
    def test_api_v2_language_aware(self, mock_reverse):
        items = [{'code': 'spam', 'configuration': 'sample'}]
        request = self.request
        request.version = 'v2'
        view = self.setup_view(self.view, request)
        list(view.filter_dict(items))
        mock_reverse.assert_any_call(viewname='sample:questionnaire_details',
                                     kwargs={'identifier': 'spam'})


@pytest.fixture
def es(request):
    """
    In order to allow multiple Elasticsearch indices when running tests in
    parallel, overwrite ES_INDEX_PREFIX settings for each test function
    according to its slave id.

    Usage for tests that require Elasticsearch:
    @pytest.mark.usefixtures('es')
    """
    from django.conf import settings
    from apps.search.index import get_elasticsearch
    from apps.search.search import get_indices_alias

    # Clear lru_cache of Elasticsearch indices.
    get_indices_alias.cache_clear()

    # Test setup
    xdist_suffix = getattr(
        request.config, 'slaveinput', {}
    ).get('slaveid', 'es_test_index')
    es_prefix = f'{settings.ES_INDEX_PREFIX}{xdist_suffix}'
    setattr(settings, 'ES_INDEX_PREFIX', es_prefix)

    # Actual test
    yield

    # Test teardown
    # get_elasticsearch().indices.delete(index=f'{es_prefix}*')


class QuestionnaireDetailViewTest(TestCase):
    """
    Tests for v1
    """
    fixtures = [
        'sample_global_key_values',
        'sample',
        'sample_questionnaires',
    ]

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.factory = RequestFactory()
        self.url = '/en/api/v1/questionnaires/sample_1/'
        self.request = self.factory.get(self.url)
        self.request.version = 'v1'
        self.invalid_request = self.factory.get('/en/api/v1/questionnaires/foo')
        self.identifier = 'sample_1'
        self.view = self.setup_view(
            QuestionnaireDetailView(), self.request, identifier=self.identifier
        )

    def get_serialized_data(self):
        questionnaire = Questionnaire.objects.get(code=self.identifier)
        return QuestionnaireSerializer(questionnaire).data

    def test_invalid_element(self):
        with self.assertRaises(Http404):
            self.view.get(self.invalid_request)

    def test_get_object(self):
        item = self.view.get_current_object()
        self.assertEqual(item.id, 1)
        self.assertEqual(item.code, self.identifier)

    def test_api_detail_url(self):
        serialized = self.get_serialized_data()
        serialized['list_data']['name'] = 'foo'
        serialized['list_data']['definition'] = 'bar'
        item = self.view.replace_keys({'_source': serialized})
        with self.assertRaises(KeyError):
            foo = item['api_url']  # noqa


@elasticmock
class ConfiguredQuestionnaireDetailViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.url = '/en/api/v2/questionnaires/sample_1/'
        self.request = self.factory.get(self.url)
        self.request.version = 'v2'
        self.identifier = 'sample_1'
        self.view = self.setup_view(
            ConfiguredQuestionnaireDetailView(), self.request,
            identifier=self.identifier
        )
        self.view.obj = None

    @patch('apps.questionnaire.api.views.get_language')
    @patch('apps.questionnaire.api.views.get_questionnaire_data_in_single_language')
    def test_prepare_data_one_language(self, mock_single_language,
                                       mock_get_language):
        mock_get_language.return_value = sentinel.language
        self.view.object = MagicMock(
            data=sentinel.data,
            original_locale=sentinel.original_locale
        )
        self.view.prepare_data()
        mock_single_language.assert_called_once_with(
            locale=sentinel.language,
            original_locale=sentinel.original_locale,
            questionnaire_data=sentinel.data
        )
