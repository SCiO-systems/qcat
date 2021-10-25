from datetime import datetime

import pytest
from unittest.mock import patch, MagicMock

from django.core.exceptions import ValidationError
from django.utils.translation import get_language

from apps.configuration.editions.base import Edition
from apps.configuration.models import (
    Category,
    Configuration,
    Key,
    Questiongroup,
    Translation,
    Value,
    TranslationContent, Country)
from apps.qcat.tests import TestCase


def get_valid_configuration_model():
    Configuration.CODE_CHOICES += [('sample', 'sample')]
    return Configuration(code='sample', edition='2015', data={"sections": []})


def get_valid_translation_model():
    return Translation(translation_type='key', data={
        "configuration": {"keyword": {"en": "foo"}}})


def get_valid_translationcontent_instance(translation):
    return TranslationContent(
        translation=translation,
        keyword='keyword',
        configuration='configuration',
        text='foo'
    )


def get_valid_questiongroup_model():
    return Questiongroup(keyword='foo', configuration={})


def get_valid_key_model():
    translation = get_valid_translation_model()
    translation.save()
    return Key(
        keyword='foo', translation=translation, configuration={"foo": "bar"})


def get_valid_value_model():
    translation = get_valid_translation_model()
    translation.translation_type = 'value'
    translation.save()
    # key = get_valid_key_model()
    # key.save()
    return Value(
        keyword='foo', translation=translation,
        configuration={"foo": "bar"})


def get_valid_category_model():
    translation = get_valid_translation_model()
    translation.translation_type = 'category'
    translation.save()
    return Category(keyword='foo', translation=translation)


class CategoryModelTest(TestCase):

    def setUp(self):
        self.category = get_valid_category_model()

    def test_get_valid_category_model_is_valid(self):
        self.category.full_clean()  # Should not raise

    def test_id_is_primary_key(self):
        self.assertTrue(hasattr(self.category, 'id'))

    def test_keyword_is_mandatory(self):
        self.category.keyword = None
        with self.assertRaises(ValidationError):
            self.category.full_clean()

    def test_translation_needs_correct_type(self):
        translation = get_valid_translation_model()
        translation.translation_type = 'foo'
        translation.save()
        self.category.translation = translation
        with self.assertRaises(ValidationError):
            self.category.full_clean()

    @patch.object(Translation, 'get_translation')
    def test_get_translation_calls_translation_function(
            self, mock_Translation_get_translation):
        self.category.get_translation(
            'keyword', configuration='foo', locale='bar')
        mock_Translation_get_translation.assert_called_once_with(
            'keyword', configuration='foo', locale='bar')


class QuestiongroupModelTest(TestCase):

    def setUp(self):
        self.questiongroup = get_valid_questiongroup_model()

    def test_get_valid_questiongroup_model_is_valid(self):
        self.questiongroup.full_clean()  # Should not raise

    def test_id_is_primary_key(self):
        self.assertTrue(hasattr(self.questiongroup, 'id'))

    def test_keyword_is_mandatory(self):
        self.questiongroup.keyword = None
        with self.assertRaises(ValidationError):
            self.questiongroup.full_clean()

    def test_keyword_is_unique(self):
        self.questiongroup.save()
        q2 = get_valid_questiongroup_model()
        with self.assertRaises(ValidationError):
            q2.full_clean()

    def test_translation_is_not_mandatory(self):
        self.questiongroup.translation = None
        self.questiongroup.full_clean()  # Should not raise

    def test_configuration_is_not_mandatory(self):
        self.questiongroup.configuration = {}
        self.questiongroup.full_clean()  # Should not raise


class KeyModelTest(TestCase):

    def setUp(self):
        self.key = get_valid_key_model()

    def test_get_valid_key_model_is_valid(self):
        self.key.full_clean()  # Should not raise

    def test_id_is_primary_key(self):
        self.assertTrue(hasattr(self.key, 'id'))

    def test_keyword_is_mandatory(self):
        self.key.keyword = None
        with self.assertRaises(ValidationError):
            self.key.full_clean()

    def test_translation_needs_correct_type(self):
        translation = get_valid_translation_model()
        translation.translation_type = 'foo'
        translation.save()
        self.key.translation = translation
        with self.assertRaises(ValidationError):
            self.key.full_clean()

    def test_configuration_is_mandatory(self):
        self.key.configuration = None
        with self.assertRaises(ValidationError):
            self.key.full_clean()

    def test_configuration_cannot_be_empty(self):
        self.key.configuration = {}
        with self.assertRaises(ValidationError):
            self.key.full_clean()

    @patch.object(Translation, 'get_translation')
    def test_get_translation_calls_translation_function(
            self, mock_Translation_get_translation):
        self.key.get_translation('keyword', configuration='foo', locale='bar')
        mock_Translation_get_translation.assert_called_once_with(
            'keyword', configuration='foo', locale='bar')

    def test_type_returns_type(self):
        self.key.configuration = {"type": "foo"}
        self.assertEqual(self.key.type_, 'foo')

    def test_type_returns_None_if_not_found(self):
        self.assertIsNone(self.key.type_)

    def test_can_have_one_value(self):
        self.key.save()
        self.assertEqual(self.key.values.count(), 0)
        value = get_valid_value_model()
        value.save()
        self.key.values.add(value)
        self.assertEqual(self.key.values.count(), 1)

    def test_can_have_multiple_values(self):
        self.key.save()
        value_1 = get_valid_value_model()
        value_1.save()
        self.key.values.add(value_1)
        value_2 = get_valid_value_model()
        value_2.keyword = 'bar'
        value_2.save()
        self.key.values.add(value_2)
        self.assertEqual(self.key.values.count(), 2)


class ValueModelTest(TestCase):

    def setUp(self):
        self.value = get_valid_value_model()

    def test_get_valid_value_model_is_valid(self):
        self.value.full_clean()  # Should not raise

    def test_id_is_primary_key(self):
        self.assertTrue(hasattr(self.value, 'id'))

    def test_keyword_is_mandatory(self):
        self.value.keyword = None
        with self.assertRaises(ValidationError):
            self.value.full_clean()

    def test_translation_needs_correct_type(self):
        translation = get_valid_translation_model()
        translation.translation_type = 'foo'
        translation.save()
        self.value.translation = translation
        with self.assertRaises(ValidationError):
            self.value.full_clean()

    def test_configuration_is_not_mandatory(self):
        self.value.configuration = None
        self.value.full_clean()  # Should not raise

    def test_configuration_can_be_empty(self):
        self.value.configuration = {}
        self.value.full_clean()  # Should not raise

    @patch.object(Translation, 'get_translation')
    def test_get_translation_calls_translation_function(
            self, mock_Translation_get_translation):
        self.value.get_translation(
            'keyword', configuration='foo', locale='bar')
        mock_Translation_get_translation.assert_called_once_with(
            'keyword', configuration='foo', locale='bar')

    def test_can_have_one_key(self):
        self.value.save()
        self.assertEqual(self.value.key_set.count(), 0)
        key = get_valid_key_model()
        key.save()
        self.value.key_set.add(key)
        self.assertEqual(self.value.key_set.count(), 1)

    def test_can_have_multiple_keys(self):
        self.value.save()
        key_1 = get_valid_key_model()
        key_1.save()
        self.value.key_set.add(key_1)
        key_2 = get_valid_key_model()
        key_2.keyword = 'bar'
        key_2.save()
        self.value.key_set.add(key_2)
        self.assertEqual(self.value.key_set.count(), 2)


class TranslationModelTest(TestCase):

    def setUp(self):
        self.translation = get_valid_translation_model()

    def test_get_valid_translation_model_is_valid(self):
        self.translation.full_clean()  # Should not raise

    def test_id_is_primary_key(self):
        self.assertTrue(hasattr(self.translation, 'id'))

    def test_translation_type_is_mandatory(self):
        self.translation.translation_type = None
        with self.assertRaises(ValidationError):
            self.translation.full_clean()

    def test_translation_type_needs_to_be_valid(self):
        self.translation.translation_type = 'foo'
        with self.assertRaises(ValidationError):
            self.translation.full_clean()

    def test_empty_response_for_translation_without_content(self):
        self.assertIsNone(
            self.translation.get_translation('keyword'),
            ''
        )

    @patch('django.utils.translation.pgettext_lazy')
    def test_empty_response_without_translation(self, mock_pgettext_lazy):
        self.translation.get_translation('keyword')
        mock_pgettext_lazy.assert_not_called()

    @patch.object(Translation, 'translationcontent_set')
    def test_get_translation_does_not_change_locale(self,
                                                    mocktranslationcontent_set):
        mocktranslationcontent_set.exists.return_value = True
        mocktranslationcontent_set.return_value = {'wocat': 'foo'}
        self.translation.get_translation('keyword', locale='es')
        self.assertEqual(get_language(), 'en')

    @patch('apps.configuration.models.activate')
    def test_get_translation_activates_other_locale(self,
                                                    mock_activate):
        self.translation.get_translation(
            'keyword', configuration='configuration', locale='es'
        )
        mock_activate.assert_any_call('es')
        mock_activate.assert_any_call(get_language())

    @patch('apps.configuration.models.pgettext_lazy')
    @patch.object(Translation, 'translationcontent_set')
    def test_get_translation_calls_pgettext(self, mocktranslationcontent_set,
                                            mock_pgettext):
        mocktranslationcontent_set.exists.return_value = True
        mocktranslationcontent_set.return_value = {'wocat': 'foo'}
        self.translation.get_translation(
            'keyword', configuration='configuration', locale='es'
        )
        mock_pgettext.assert_called_once_with('configuration keyword', 'foo')

    def test_get_translation_returns_empty_if_configuration_not_found(self):
        self.assertIsNone(self.translation.get_translation(
            'keyword', configuration='foo'), None)

    def test_get_translation_edition(self):
        translation = Translation(data={
            'configuration': {'keyword': {'en': 'foo'}},
            'configuration_edition': {'keyword': {'en': 'all new'}}
        })
        self.assertEqual(
            translation.get_translation('keyword', 'configuration', edition='edition'),
            'all new'
        )

    def test_get_translation_fallback(self):
        translation = Translation(data={
            'configuration': {'keyword': {'en': 'foo'}},
            'configuration_edition': {'keyword': {'en': 'all new'}}
        })
        self.assertEqual(
            translation.get_translation('keyword', 'configuration'),
            'foo'
        )


class ValueUserTest(TestCase):

    fixtures = [
        'global_key_values',
    ]

    def test_all_returns_all_countries(self):
        all = Country.all()
        self.assertEqual(len(all), 249)

    def test_get_returns_single_country(self):
        ch = Country.get('CHE')
        self.assertEqual(ch, Value.objects.get(pk=215))

    def test_get_returns_none_if_not_found(self):
        notfound = Country.get('foo')
        self.assertIsNone(notfound)


@pytest.fixture
def mock_edition(request):
    class MockEdition(Edition):
        code = 'technologies'
        edition = 'sub'

    request.cls.mock_edition = MockEdition


class ConfigurationTest(TestCase):

    def test_has_new_version(self):
        """
        This tests the queryset, but it is an important one.

        """
        old_edition = get_valid_configuration_model()
        old_edition.edition = '2000'
        old_edition.created = datetime(2000, 1, 1)
        old_edition.save()
        new_edition = get_valid_configuration_model()
        new_edition.edition = '2001'
        new_edition.created = datetime(2001, 1, 1)
        new_edition.save()
        self.assertTrue(old_edition.has_new_edition)
        self.assertFalse(new_edition.has_new_edition)

    @pytest.mark.usefixtures('mock_edition')
    def test_get_none_edition(self):
        with patch.object(Configuration, 'find_subclass') as find_mock:
            find_mock.return_value = self.mock_edition({}, {}, {}, {}, {}, {})
            config = Configuration(code='foo', edition='bar')
            self.assertIsNone(config.get_edition())

    @pytest.mark.usefixtures('mock_edition')
    def test_get_valid_edition(self):
        with patch.object(Configuration, 'find_subclass') as find_mock:
            find_mock.return_value = self.mock_edition({}, {}, {}, {}, {}, {})
            config = Configuration(code='technologies', edition='sub')
            self.assertEqual(config.get_edition(), find_mock.return_value)

    @pytest.mark.usefixtures('mock_edition')
    def test_find_subclass(self):
        # Mock a 'module' with the attribute Foo, so it is found by dir(module).
        module = MagicMock()
        module.Foo = self.mock_edition
        config = Configuration()

        with patch('apps.configuration.models.importlib.util') as importlib:
            importlib.module_from_spec.return_value = module
            self.assertIsInstance(config.find_subclass(''), self.mock_edition)
