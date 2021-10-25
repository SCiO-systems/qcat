# Prevent logging of Elasticsearch queries
import logging
from elasticmock import elasticmock

import pytest

logging.disable(logging.CRITICAL)

import collections

from django.db.models import Q

from apps.qcat.tests import TestCase
from apps.questionnaire.models import Questionnaire
from apps.questionnaire.utils import get_list_values
from apps.search.search import advanced_search
from apps.search.tests.test_index import create_temp_indices

FilterParam = collections.namedtuple(
            'FilterParam',
            ['questiongroup', 'key', 'values', 'operator', 'type'])


@elasticmock
class AdvancedSearchTest(TestCase):

    fixtures = [
        'global_key_values',
        'sample',
        'samplemulti',
        'sample_questionnaires_search',
    ]

    def setUp(self):
        create_temp_indices([('sample', '2015'), ('samplemulti', '2015')])

    def test_advanced_search(self):
        filter_param = FilterParam(
            questiongroup='qg_11', key='key_14', values=['value_14_1'],
            operator='eq', type='image_checkbox')
        key_search = advanced_search(
            filter_params=[filter_param],
            configuration_codes=['sample']).get('hits')
        self.assertEqual(key_search.get('total'), 2)

        filter_param = FilterParam(
            questiongroup='qg_11', key='key_14', values=['value_14_2'],
            operator='eq', type='image_checkbox')
        key_search = advanced_search(
            filter_params=[filter_param],
            configuration_codes=['sample']).get('hits')
        self.assertEqual(key_search.get('total'), 1)

    def test_advanced_search_single_filter(self):
        filter_param = FilterParam(
            questiongroup='qg_11', key='key_14', values=['value_14_1'],
            operator='eq', type='image_checkbox')
        search = advanced_search(
            filter_params=[filter_param], configuration_codes=['sample']
        ).get('hits')
        self.assertEqual(search.get('total'), 2)

    def test_advanced_search_multiple_arguments(self):
        query_string = 'key'
        filter_param = FilterParam(
            questiongroup='qg_35', key='key_48', values=['value_1'],
            operator='eq', type='radio')
        search = advanced_search(
            filter_params=[filter_param],
            query_string=query_string,
            configuration_codes=['sample']
        ).get('hits')
        self.assertEqual(search.get('total'), 1)
        hit_ids = [r.get('_id') for r in search.get('hits')]
        self.assertEqual(hit_ids, ['1'])

    def test_advanced_search_multiple_arguments_match_one(self):
        query_string = 'key'
        filter_param = FilterParam(
            questiongroup='qg_35', key='key_48', values=['value_1'],
            operator='eq', type='radio')
        search = advanced_search(
            filter_params=[filter_param],
            query_string=query_string,
            configuration_codes=['sample'],
            match_all=False
        ).get('hits')
        self.assertEqual(search.get('total'), 2)
        hit_ids = [r.get('_id') for r in search.get('hits')]
        self.assertEqual(hit_ids, ['2', '1'])

    def test_advanced_search_multiple_arguments_2_match_one(self):
        query_string = 'key'
        filter_param = FilterParam(
            questiongroup='qg_11', key='key_14', values=['value_14_1'],
            operator='eq', type='image_checkbox')
        search = advanced_search(
            filter_params=[filter_param],
            query_string=query_string,
            configuration_codes=['sample'],
            match_all=False
        ).get('hits')
        self.assertEqual(search.get('total'), 3)
        hit_ids = [r.get('_id') for r in search.get('hits')]
        self.assertEqual(hit_ids, ['2', '1', '5'])

    def test_advanced_search_multiple_arguments_2(self):
        query_string = 'key'
        filter_param = FilterParam(
            questiongroup='qg_11', key='key_14', values=['value_14_1'],
            operator='eq', type='image_checkbox')
        search = advanced_search(
            filter_params=[filter_param],
            query_string=query_string,
            configuration_codes=['sample']
        ).get('hits')
        self.assertEqual(search.get('total'), 1)
        hit_ids = [r.get('_id') for r in search.get('hits')]
        self.assertEqual(hit_ids, ['1'])

    def test_advanced_search_multiple_arguments_same_filter(self):
        filter_param = FilterParam(
            questiongroup='qg_11', key='key_14',
            values=['value_14_1', 'value_14_3'],
            operator='eq', type='image_checkbox')
        search = advanced_search(
            filter_params=[filter_param],
            configuration_codes=['sample']
        ).get('hits')
        self.assertEqual(search.get('total'), 3)
        hit_ids = [r.get('_id') for r in search.get('hits')]
        self.assertEqual(hit_ids, ['1', '5', '4'])

    def test_advanced_search_multiple_arguments_same_filter_2(self):
        filter_param_1 = FilterParam(
            questiongroup='qg_11', key='key_14',
            values=['value_14_1', 'value_14_3'],
            operator='eq', type='image_checkbox')
        filter_param_2 = FilterParam(
            questiongroup='qg_35', key='key_48', values=['value_3'],
            operator='eq', type='radio')
        search = advanced_search(
            filter_params=[filter_param_1, filter_param_2],
            configuration_codes=['sample']
        ).get('hits')
        self.assertEqual(search.get('total'), 1)
        hit_ids = [r.get('_id') for r in search.get('hits')]
        self.assertEqual(hit_ids, ['4'])

    def test_advanced_search_multiple_arguments_same_filter_2_match_one(self):
        filter_param_1 = FilterParam(
            questiongroup='qg_11', key='key_14',
            values=['value_14_1', 'value_14_3'],
            operator='eq', type='image_checkbox')
        filter_param_2 = FilterParam(
            questiongroup='qg_35', key='key_48', values=['value_2'],
            operator='eq', type='radio')
        search = advanced_search(
            filter_params=[filter_param_1, filter_param_2],
            configuration_codes=['sample'],
            match_all=False,
        ).get('hits')
        self.assertEqual(search.get('total'), 4)
        hit_ids = [r.get('_id') for r in search.get('hits')]
        self.assertListEqual(hit_ids, ['1', '2', '5', '4'])

    def test_advanced_search_gte(self):
        filter_param = FilterParam(
            questiongroup='qg_11', key='key_14', values=['2'],
            operator='gte', type='image_checkbox')
        with self.assertRaises(NotImplementedError):
            search = advanced_search(
                filter_params=[filter_param],
                configuration_codes=['sample']
            ).get('hits')
            self.assertEqual(search.get('total'), 2)
            hit_ids = [r.get('_id') for r in search.get('hits')]
            self.assertEqual(hit_ids, ['4', '1'])

    def test_advanced_search_lt(self):
        filter_param = FilterParam(
            questiongroup='qg_11', key='key_14', values=['2'],
            operator='lt', type='image_checkbox')
        with self.assertRaises(NotImplementedError):
            search = advanced_search(
                filter_params=[filter_param],
                configuration_codes=['sample']
            ).get('hits')
            self.assertEqual(search.get('total'), 2)
            hit_ids = [r.get('_id') for r in search.get('hits')]
            self.assertEqual(hit_ids, ['5', '1'])

    def test_advanced_search_lte(self):
        filter_param = FilterParam(
            questiongroup='qg_35', key='key_48', values=['2'],
            operator='lte', type='radio')
        with self.assertRaises(NotImplementedError):
            search = advanced_search(
                filter_params=[filter_param],
                configuration_codes=['sample']
            ).get('hits')
            self.assertEqual(search.get('total'), 2)
            hit_ids = [r.get('_id') for r in search.get('hits')]
            self.assertEqual(hit_ids, ['2', '1'])

    def test_advanced_search_gte_lte(self):
        filter_param_1 = FilterParam(
            questiongroup='qg_11', key='key_14', values=['1'],
            operator='lte', type='image_checkbox')
        filter_param_2 = FilterParam(
            questiongroup='qg_11', key='key_14', values=['3'],
            operator='gte', type='image_checkbox')
        with self.assertRaises(NotImplementedError):
            search = advanced_search(
                filter_params=[filter_param_1, filter_param_2],
                configuration_codes=['sample'],
                match_all=False,
            ).get('hits')
            self.assertEqual(search.get('total'), 3)
            hit_ids = [r.get('_id') for r in search.get('hits')]
            self.assertEqual(hit_ids, ['5', '4', '1'])


@elasticmock
class GetListValuesTest(TestCase):

    fixtures = [
        'global_key_values',
        'sample',
        'samplemulti',
        'sample_questionnaires_search',
    ]

    def setUp(self):
        create_temp_indices([('sample', '2015'), ('samplemulti', '2015')])

    def test_returns_same_result_for_es_search_and_db_objects(self):
        es_hits = advanced_search(
            filter_params=[], query_string='key',
            configuration_codes=['sample'])
        res_1 = get_list_values(
            configuration_code='sample', es_hits=es_hits.get(
                'hits', {}).get('hits', []))
        ids = [q.get('id') for q in res_1]
        res_2 = get_list_values(
            configuration_code='sample',
            questionnaire_objects=Questionnaire.objects.filter(pk__in=ids),
            status_filter=Q())

        for res in [res_1, res_2]:
            for r in res:
                self.assertEqual(r.get('configuration'), 'sample')
                self.assertIn('key_1', r)
                self.assertIn('key_5', r)
                self.assertIn('created', r)
                self.assertIn('updated', r)
