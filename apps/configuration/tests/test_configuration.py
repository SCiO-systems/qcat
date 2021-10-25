from unittest.mock import patch, Mock

from apps.configuration.configuration import (
    QuestionnaireConfiguration,
    QuestionnaireCategory,
    QuestionnaireSubcategory,
    QuestionnaireQuestiongroup,
    QuestionnaireQuestion,
    validate_type,
)
from apps.configuration.tests.test_models import get_valid_configuration_model
from apps.qcat.errors import (
    ConfigurationErrorInvalidCondition,
    ConfigurationErrorInvalidConfiguration,
    ConfigurationErrorInvalidOption,
    ConfigurationErrorInvalidQuestiongroupCondition,
    ConfigurationErrorNoConfigurationFound,
    ConfigurationErrorNotInDatabase,
)
from apps.qcat.tests import TestCase
from apps.questionnaire.models import Questionnaire

route_questionnaire_details = 'sample:questionnaire_details'


def get_valid_questionnaire_configuration():
    return QuestionnaireConfiguration('foo')


class QuestionnaireConfigurationTest(TestCase):

    @patch.object(QuestionnaireConfiguration, 'read_configuration')
    def test_QuestionnaireConfiguration_init_calls_read_configuration(
            self, mock_read_configuration):
        get_valid_questionnaire_configuration()
        mock_read_configuration.assert_called_once_with()


class QuestionnaireConfigurationGetListDataTest(TestCase):

    fixtures = [
        'global_key_values',
        'sample',
        'sample_questionnaires',
    ]

    def test_returns_list(self):
        questionnaires = Questionnaire.objects.all()
        conf = QuestionnaireConfiguration('sample')
        list_data = conf.get_list_data([q.data for q in questionnaires])
        self.assertEqual(len(list_data), 2)
        for d in list_data:
            self.assertEqual(len(d), 4)
            self.assertIn('key_1', d)
            self.assertIn('definition', d)
            self.assertIn('country', d)


class QuestionnaireConfigurationGeometryTest(TestCase):

    fixtures = [
        'global_key_values',
        'sample',
    ]

    def test_get_questionnaire_geometry_returns_geometry(self):
        conf = QuestionnaireConfiguration('sample')
        data = {'qg_39': [{'key_56': 'geometry'}]}
        geometry = conf.get_questionnaire_geometry(data)
        self.assertEqual(geometry, data['qg_39'][0]['key_56'])


class QuestionnaireConfigurationReadConfigurationTest(TestCase):

    def test_raises_error_if_no_configuration_object(self):
        conf = get_valid_questionnaire_configuration()
        with self.assertRaises(ConfigurationErrorNoConfigurationFound):
            conf.read_configuration()

    @patch('apps.configuration.configuration.validate_type')
    def test_calls_validate_type(self, mock_validate_type):
        conf = get_valid_questionnaire_configuration()
        conf_object = get_valid_configuration_model()
        conf.configuration_object = conf_object
        conf.read_configuration()
        mock_validate_type.assert_called_once_with(
            conf_object.data.get('sections'),
            list, 'sections', 'list of dicts', '-')


class QuestionnaireCategoryTest(TestCase):

    fixtures = [
        'sample_global_key_values',
        'sample',
    ]

    def setUp(self):
        self.configuration = Mock()

    @patch('apps.configuration.configuration.validate_type')
    def test_calls_validate_type(self, mock_validate_type):
        configuration_dict = {
            "foo": "bar"
        }
        with self.assertRaises(ConfigurationErrorInvalidOption):
            QuestionnaireCategory(self.configuration, configuration_dict)
        mock_validate_type.assert_called_once_with(
            configuration_dict, dict, 'categories', 'list of dicts',
            'sections')

    def test_raises_error_if_keyword_not_found(self):
        configuration_dict = {}
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireCategory(self.configuration, configuration_dict)

    def test_raises_error_if_keyword_not_string(self):
        configuration_dict = {
            "keyword": ["bar"]
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireCategory(self.configuration, configuration_dict)

    def test_raises_error_if_not_in_db(self):
        configuration_dict = {
            "keyword": "bar"
        }
        with self.assertRaises(ConfigurationErrorNotInDatabase):
            QuestionnaireCategory(self.configuration, configuration_dict)

    def test_raises_error_if_subcategories_not_list(self):
        configuration_dict = {
            "keyword": "cat_1",
            "subcategories": "foo"
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireCategory(self.configuration, configuration_dict)


class QuestionnaireSubcategoryTest(TestCase):

    fixtures = [
        'sample_global_key_values',
        'sample',
    ]

    def setUp(self):
        self.category = Mock()

    @patch('apps.configuration.configuration.validate_type')
    def test_calls_validate_type(self, mock_validate_type):
        configuration_dict = {
            "foo": "bar"
        }
        with self.assertRaises(ConfigurationErrorInvalidOption):
            QuestionnaireSubcategory(self.category, configuration_dict)
        mock_validate_type.assert_called_once_with(
            configuration_dict, dict, 'subcategories', 'list of dicts',
            'categories')

    @patch.object(QuestionnaireSubcategory, 'validate_options')
    def test_calls_validate_options(self, mock_validate_options):
        configuration_dict = {
            "foo": "bar"
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireSubcategory(self.category, configuration_dict)
        mock_validate_options.assert_called_once_with()

    def test_raises_error_if_keyword_not_found(self):
        configuration_dict = {}
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireSubcategory(self.category, configuration_dict)

    def test_raises_error_if_keyword_not_string(self):
        configuration_dict = {
            "keyword": ["bar"]
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireSubcategory(self.category, configuration_dict)

    def test_raises_error_if_not_in_db(self):
        configuration_dict = {
            "keyword": "bar"
        }
        with self.assertRaises(ConfigurationErrorNotInDatabase):
            QuestionnaireSubcategory(self.category, configuration_dict)

    # def test_raises_error_if_no_questiongroups(self):
    #     configuration_dict = {
    #         "keyword": "subcat_1_1"
    #     }
    #     with self.assertRaises(ConfigurationErrorInvalidConfiguration):
    #         QuestionnaireSubcategory(self.category, configuration_dict)

    def test_raises_error_if_questiongroups_not_list(self):
        configuration_dict = {
            "keyword": "subcat_1_1",
            "questiongroups": "foo"
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireSubcategory(self.category, configuration_dict)


class QuestionnaireQuestiongroupTest(TestCase):

    fixtures = [
        'sample_global_key_values',
        'sample',
    ]

    def setUp(self):
        self.subcategory = Mock()
        self.subcategory.name_children = 'questions'

    def test_raises_error_if_keyword_not_found(self):
        configuration_dict = {}
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireQuestiongroup(self.subcategory, configuration_dict)

    def test_raises_error_if_keyword_not_string(self):
        configuration_dict = {
            "keyword": ["bar"]
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireQuestiongroup(self.subcategory, configuration_dict)

    def test_raises_error_if_min_num_not_integer(self):
        configuration_dict = {
            "keyword": "qg_1",
            "form_options": {"min_num": "foo"},
            "questions": [{"keyword": "key_1"}]
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireQuestiongroup(self.subcategory, configuration_dict)

    def test_raises_error_if_min_num_smaller_than_1(self):
        configuration_dict = {
            "keyword": "qg_1",
            "form_options": {"min_num": 0},
            "questions": [{"keyword": "key_1"}]
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireQuestiongroup(self.subcategory, configuration_dict)

    def test_raises_error_if_max_num_not_integer(self):
        configuration_dict = {
            "keyword": "qg_1",
            "form_options": {"max_num": "foo"},
            "questions": [{"keyword": "key_1"}]
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireQuestiongroup(self.subcategory, configuration_dict)

    def test_raises_error_if_max_num_smaller_than_1(self):
        configuration_dict = {
            "keyword": "qg_1",
            "form_options": {"max_num": -1},
            "questions": [{"keyword": "key_1"}]
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireQuestiongroup(self.subcategory, configuration_dict)

    def test_raises_error_if_questions_not_list(self):
        configuration_dict = {
            "keyword": "qg_1",
            "questions": "foo"
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireQuestiongroup(self.subcategory, configuration_dict)


class QuestionnaireQuestionTest(TestCase):

    fixtures = [
        'sample_global_key_values',
        'sample',
    ]

    def setUp(self):
        self.obj = Mock()
        self.obj.name_children = ''
        self.obj.Child = None
        self.parent_obj = Mock()

    def test_raises_error_if_key_not_found(self):
        configuration = {}
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireQuestion(self.parent_obj, configuration)

    def test_raises_error_if_key_not_string(self):
        configuration = {
            "keyword": ["bar"]
        }
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            QuestionnaireQuestion(self.parent_obj, configuration)

    def test_raises_error_if_not_in_db(self):
        configuration = {
            "keyword": "bar"
        }
        with self.assertRaises(ConfigurationErrorNotInDatabase):
            QuestionnaireQuestion(self.parent_obj, configuration)

    def test_lookup_choices_lookups_single_choice(self):
        mock_Questiongroup = Mock()
        mock_Questiongroup.configuration_keyword = 'sample'
        q = QuestionnaireQuestion(mock_Questiongroup, {'keyword': 'key_14'})
        l = q.lookup_choices_labels_by_keywords(['value_14_1'])
        self.assertEqual(l, ['Value 14_1'])

    def test_lookup_choices_lookups_many_choices(self):
        mock_Questiongroup = Mock()
        mock_Questiongroup.configuration_keyword = 'sample'
        q = QuestionnaireQuestion(mock_Questiongroup, {'keyword': 'key_14'})
        l = q.lookup_choices_labels_by_keywords(['value_14_1', 'value_14_2'])
        self.assertEqual(l, ['Value 14_1', 'Value 14_2'])

    def test_lookup_choices_boolean(self):
        q = QuestionnaireQuestion(self.parent_obj, {'keyword': 'key_14'})
        q.choices = ((True, 'Yes'), (False, 'No'))
        l = q.lookup_choices_labels_by_keywords([True])
        self.assertEqual(l, ['Yes'])

    def test_lookup_choices_integer(self):
        q = QuestionnaireQuestion(self.parent_obj, {'keyword': 'key_12'})
        q.choices = ((1, 'Low'), (2, 'High'))
        l = q.lookup_choices_labels_by_keywords([1])
        self.assertEqual(l, ['Low'])

    def test_raises_error_if_condition_wrong_formatted(self):
        condition = 'foo'
        with self.assertRaises(ConfigurationErrorInvalidCondition):
            QuestionnaireQuestion(
                self.parent_obj,
                {'keyword': 'key_15', 'form_options': {
                    'conditions': [condition]}})

    def test_raises_error_if_value_does_not_exist(self):
        condition = 'foo|True|key_16'
        with self.assertRaises(ConfigurationErrorInvalidCondition):
            QuestionnaireQuestion(
                self.parent_obj,
                {'keyword': 'key_15', 'form_options': {
                    'conditions': [condition]}})

    def test_raises_error_if_condition_expression_nonsense(self):
        condition = 'value_15_1|;:_|key_16'
        with self.assertRaises(ConfigurationErrorInvalidCondition):
            QuestionnaireQuestion(
                self.parent_obj,
                {'keyword': 'key_15', 'form_options': {
                    'conditions': [condition]}})

    def test_raises_error_if_questiongroup_condition_wrong_formatted(self):
        qg_condition = 'foo'
        with self.assertRaises(
                ConfigurationErrorInvalidQuestiongroupCondition):
            QuestionnaireQuestion(
                self.parent_obj,
                {
                    'keyword': 'key_16',
                    'form_options': {
                        'questiongroup_conditions': [qg_condition]}})

    def test_raises_error_if_questiongroup_condition_expression_nonsense(self):
        qg_condition = ';%.|foo'
        with self.assertRaises(
                ConfigurationErrorInvalidQuestiongroupCondition):
            QuestionnaireQuestion(
                self.parent_obj, {
                    'keyword': 'key_16',
                    'form_options': {
                        'questiongroup_conditions': [qg_condition]}})


class BaseConfigurationObjectValidateOptions(TestCase):

    def test_raises_error_if_invalid_options(self):
        conf = get_valid_questionnaire_configuration()
        conf.configuration = {"foo": "bar"}
        conf.valid_options = ["bar"]
        with self.assertRaises(ConfigurationErrorInvalidOption):
            conf.validate_options()

    def test_raises_error_if_some_invalid_options(self):
        conf = get_valid_questionnaire_configuration()
        conf.configuration = {"foo": "bar", "bar": "faz"}
        conf.valid_options = ["foo"]
        with self.assertRaises(ConfigurationErrorInvalidOption):
            conf.validate_options()

    def test_passes_if_all_valid_options(self):
        conf = get_valid_questionnaire_configuration()
        conf.configuration = {"foo": "bar", "bar": "faz"}
        conf.valid_options = ["foo", "bar"]
        conf.validate_options()  # Should not raise

    def test_passes_if_some_valid_options(self):
        conf = get_valid_questionnaire_configuration()
        conf.configuration = {"foo": "bar", "bar": "faz"}
        conf.valid_options = ["foo", "bar", "faz"]
        conf.validate_options()  # Should not raise


class ValidateTypeTest(TestCase):

    def test_raises_error_if_invalid_type(self):
        with self.assertRaises(ConfigurationErrorInvalidConfiguration):
            validate_type({}, list, 'foo', 'bar', 'faz')

    def test_passes_if_valid_type(self):
        validate_type({}, dict, 'foo', 'bar', 'faz')
