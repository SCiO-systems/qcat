# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.test.utils import override_settings
from elasticsearch import TransportError
from unittest.mock import Mock

from apps.qcat.tests import TestCase
from apps.search.utils import (
    get_alias,
    get_analyzer,
    check_connection,
    force_strings)


class GetAnalyzerTest(TestCase):

    @override_settings(ES_ANALYZERS=(('foo', 'bar'), ('faz', 'taz')))
    def test_returns_analyzer_by_language(self):
        ret = get_analyzer('foo')
        self.assertEqual(ret, 'bar')

    @override_settings(ES_ANALYZERS=(('foo', 'bar'), ('faz', 'taz')))
    def test_returns_None_if_not_found(self):
        ret = get_analyzer('asdf')
        self.assertIsNone(ret)

    @override_settings(ES_ANALYZERS=None)
    def test_returns_None_if_not_set(self):
        ret = get_analyzer('foo')
        self.assertIsNone(ret)


@override_settings(ES_INDEX_PREFIX='prefix_')
class GetAliasTest(TestCase):

    def test_returns_single_configuration_code(self):
        alias = get_alias('foo')
        self.assertEqual(alias, 'prefix_foo')

    def test_returns_no_configuration_code(self):
        alias = get_alias('')
        self.assertEqual(alias, 'prefix_')

    def test_returns_multiple_configuration_codes(self):
        alias = get_alias('foo', 'bar')
        self.assertEqual(alias, 'prefix_foo,prefix_bar')


class TestConnectionTest(TestCase):

    def test_calls_info_if_no_index_provided(self):
        es = Mock()
        check_connection(es)
        es.info.assert_called_once_with()

    def test_returns_true_if_available_no_index_provided(self):
        es = Mock()
        es.info.return_value = {}
        success, error_msg = check_connection(es)
        self.assertTrue(success)
        self.assertEqual(error_msg, '')

    def test_returns_false_if_not_available_no_index_provided(self):
        es = Mock()
        es.info.side_effect = TransportError
        success, error_msg = check_connection(es)
        self.assertFalse(success)
        self.assertNotEqual(error_msg, '')

    def test_calls_index_exists_with_index(self):
        es = Mock()
        check_connection(es, index='foo')
        es.indices.exists.assert_called_once_with(index='foo')

    def test_returns_true_if_available_with_index(self):
        es = Mock()
        es.indices.exists.return_value = True
        success, error_msg = check_connection(es, index='foo')
        self.assertTrue(success)
        self.assertEqual(error_msg, '')

    def test_returns_false_if_not_available_with_index(self):
        es = Mock()
        es.indices.exists.side_effect = TransportError
        success, error_msg = check_connection(es, index='foo')
        self.assertFalse(success)
        self.assertNotEqual(error_msg, '')

    def test_returns_false_if_index_not_exists_with_index(self):
        es = Mock()
        es.indices.exists.return_value = False
        success, error_msg = check_connection(es, index='foo')
        self.assertFalse(success)
        self.assertNotEqual(error_msg, '')


class ForceStringsTest(TestCase):

    def setUp(self):
        self.single_level = {
            'a': _(u'Login')
        }
        self.multi_level = {
            'a': {
                'b': {
                    'c': _(u'Login')
                }
            }
        }

    def test_single_level(self):
        single_level = force_strings(self.single_level)
        self.assertIsInstance(single_level['a'], str)

    def test_multi_level(self):
        multi_level = force_strings(self.multi_level)
        self.assertIsInstance(multi_level['a']['b']['c'], str)
