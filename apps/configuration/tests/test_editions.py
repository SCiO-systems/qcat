from unittest import mock

import pytest
from django.core.exceptions import ObjectDoesNotExist
from apps.qcat.tests import TestCase
from apps.configuration.models import Configuration, Key, Value, Translation, \
    Questiongroup, Category
from ..editions.base import Edition, Operation
from ..editions.technologies_2018 import Technologies as Technologies2018


class EditionsTest(TestCase):

    @property
    def model_kwargs(self):
        mock_translation = mock.MagicMock(spec=Translation)
        mock_key = mock.MagicMock(spec=Key)
        mock_value = mock.MagicMock(spec=Value)
        mock_questiongroup = mock.MagicMock(spec=Questiongroup)
        mock_category = mock.MagicMock(spec=Category)
        for mock_obj in [mock_translation, mock_key, mock_value]:
            mock_obj.objects.get_or_create.return_value = (mock.sentinel, True)
        return dict(
            key=mock_key,
            value=mock_value,
            questiongroup=mock_questiongroup,
            category=mock_category,
            configuration=mock.MagicMock(spec=Configuration),
            translation=mock_translation,
        )

    def get_edition(self, code='test_code', edition='1234'):

        class TestEdition(Edition):
            def __init__(self, code, edition, **kwargs):
                self.code = code
                self.edition = edition
                super().__init__(**kwargs)

        return TestEdition(
            code=code,
            edition=edition,
            **self.model_kwargs
        )

    def test_invalid_code(self):
        with self.assertRaises(AttributeError):
            self.get_edition()

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_no_operations(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]
        with self.assertRaises(NotImplementedError):
            self.get_edition().operations

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_update_translation(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        new_translation = {'label': 'bar'}
        edition = self.get_edition()
        translation_obj = mock.MagicMock()
        edition.translation.objects.get.return_value = translation_obj

        edition.update_translation(
            update_pk=1, **new_translation
        )
        self.assertIn(
            mock.call.data.update({'test_code_1234': new_translation}),
            translation_obj.method_calls
        )

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_create_translation(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        new_translation = {'label': 'bar'}
        edition = self.get_edition()

        edition.create_new_translation(
            translation_type='type', **new_translation)

        self.assertIn(
            mock.call.get_or_create(
                data={'test_code_1234': new_translation},
                translation_type='type'),
            edition.translation.objects.method_calls
        )

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_create_translation_configurations(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        new_translation = {'label': 'bar'}
        edition = self.get_edition()

        edition.create_new_translation(
            translation_type='type', translation_keys=['foo', 'bar'],
            **new_translation)

        self.assertIn(
            mock.call.get_or_create(
                data={'foo': new_translation, 'bar': new_translation},
                translation_type='type'),
            edition.translation.objects.method_calls
        )

    @mock.patch.object(Edition, 'create_new_translation')
    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_create_new_value_configuration_editions(
            self, mock_choices, mock_create_new_translation):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        edition = self.get_edition()

        translation = {'label': 'bar'}
        conf_editions = ['foo', 'bar']
        edition.create_new_value(
            keyword='keyword', translation=translation,
            configuration_editions=conf_editions)

        self.assertIn(
            mock.call(
                label='bar', translation_type='value',
                translation_keys=conf_editions),
            mock_create_new_translation.call_args_list
        )

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_create_new_value_new_translation(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        edition = self.get_edition()
        edition.value.objects.get.side_effect = ObjectDoesNotExist

        translation = {'label': 'bar'}
        edition.create_new_value(keyword='keyword', translation=translation)

        # Creates translation
        self.assertIn(
            mock.call.get_or_create(
                data={'test_code_1234': translation},
                translation_type='value'),
            edition.translation.objects.method_calls
        )
        # Creates value
        self.assertIn(
            mock.call.create(
                configuration=None, keyword='keyword', order_value=None,
                translation=edition.translation.objects.get_or_create.return_value[0]),
            edition.value.objects.method_calls
        )

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_create_new_value_existing_translation(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        edition = self.get_edition()
        edition.value.objects.get.side_effect = ObjectDoesNotExist

        config = {'some': 'config'}
        edition.create_new_value(
            keyword='keyword', translation=1, order_value=1,
            configuration=config)

        # Creates translation
        self.assertIn(
            mock.call.get(pk=1),
            edition.translation.objects.method_calls
        )
        # Creates value
        self.assertIn(
            mock.call.create(
                configuration=config, keyword='keyword', order_value=1,
                translation=edition.translation.objects.get.return_value),
            edition.value.objects.method_calls
        )

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_create_new_question(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        edition = self.get_edition()
        edition.key.objects.get.side_effect = ObjectDoesNotExist

        translation = {'label': 'bar'}
        edition.create_new_question(
            keyword='keyword', translation=translation, question_type='text')

        # Creates translation
        self.assertIn(
            mock.call.get_or_create(
                data={'test_code_1234': translation},
                translation_type='key'),
            edition.translation.objects.method_calls
        )
        # Creates question
        self.assertIn(
            mock.call.create(
                configuration={'type': 'text'}, keyword='keyword',
                translation=edition.translation.objects.get_or_create.return_value[0]),
            edition.key.objects.method_calls
        )

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_create_new_question_exists(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        edition = self.get_edition()
        translation = {'label': 'bar'}
        mock_key = mock.MagicMock(
            spec=Key, translation=translation,
            configuration={'configuration': 'initial'})
        edition.key.objects.get.return_value = mock_key

        edition.create_new_question(
            keyword='keyword', translation=translation, question_type='text',
            configuration={'configuration': 'updated'})

        assert mock_key.configuration['configuration'] == 'updated'

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_find_in_data(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        edition = self.get_edition()

        data = {
            'sections': [
                {
                    'keyword': 'section_1',
                    'categories': [
                        {
                            'keyword': 'category_1',
                            'subcategories': [
                                {
                                    'keyword': 'subcat_1',
                                    'questiongroups': [
                                        {
                                            'keyword': 'qg_1',
                                            'questions': [
                                                {
                                                    'keyword': 'question_1',
                                                }
                                            ]
                                        },
                                        {
                                            'keyword': 'qg_2',
                                            'questions': [
                                                {
                                                    'keyword': 'question_2'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    'keyword': 'section_2',
                    'categories': [
                        {
                            'keyword': 'category_2'
                        }
                    ]
                }
            ]
        }

        self.assertEqual(
            edition.find_in_data(
                path=('section_2', 'category_2'),
                **data)['keyword'],
            'category_2')

        self.assertEqual(
            edition.find_in_data(
                path=('section_1', 'category_1', 'subcat_1', 'qg_2', 'question_2'),
                **data)['keyword'],
            'question_2')

        with self.assertRaises(KeyError):
            edition.find_in_data(path=('does', 'not', 'exist'), **data)

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_update_config_data(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        edition = self.get_edition()

        data = {
            'sections': [
                {
                    'keyword': 'section_1',
                    'categories': [
                        {
                            'keyword': 'category_1',
                            'subcategories': [
                                {
                                    'keyword': 'subcat_1',
                                    'questiongroups': [
                                        {
                                            'keyword': 'qg_1',
                                            'questions': [
                                                {
                                                    'keyword': 'question_1',
                                                }
                                            ]
                                        },
                                        {
                                            'keyword': 'qg_2',
                                            'questions': [
                                                {
                                                    'keyword': 'question_2'
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    'keyword': 'section_2',
                    'categories': [
                        {
                            'keyword': 'category_2'
                        }
                    ]
                }
            ]
        }

        updated_value = {'keyword': 'category_2', 'foo': 'bar'}
        updated_data = edition.update_config_data(
            path=('section_2', 'category_2'), updated=updated_value, **data)
        self.assertEqual(
            edition.find_in_data(
                path=('section_2', 'category_2'),
                **updated_data)['foo'],
            'bar')

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_update_data_single(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        edition = self.get_edition()

        data = {
            'qg_1': [
                {
                    'key_1': 'Foo',
                    'key_2': 'Bar'
                }
            ],
            'qg_2': [
                {
                    'key_3': 'Faz'
                }
            ]
        }
        updated = edition.update_data('qg_1', 'key_2', None, **data)
        data['qg_1'][0]['key_2'] = None
        self.assertDictEqual(updated, data)

        updated = edition.update_data('qg_1', 'key_2', 'Taz', **data)
        data['qg_1'][0]['key_2'] = 'Taz'
        self.assertDictEqual(updated, data)

    @mock.patch.object(Configuration, 'CODE_CHOICES', new_callable=mock.PropertyMock)
    def test_update_data_multiple(self, mock_choices):
        mock_choices.return_value = [('test_code', 'test_code'), ]

        edition = self.get_edition()

        data = {
            'qg_1': [
                {
                    'key_2': 'Faz'
                },
                {
                    'key_1': 'Foo',
                },
                {
                    'key_1': 'Faz',
                    'key_2': 'Taz'
                }
            ]
        }
        updated = edition.update_data('qg_1', 'key_2', None, **data)
        for i in range(len(data['qg_1'])):
            data['qg_1'][i]['key_2'] = None
        self.assertDictEqual(updated, data)


class EditionTechnologies2018Test(TestCase):

    def get_edition(self):
        return Technologies2018(
            key=Key, value=Value, questiongroup=Questiongroup,
            category=Category, configuration=Configuration,
            translation=Translation
        )

    def test_move_date_documentation_data(self):
        edition = self.get_edition()
        moved_empty = edition.move_date_documentation_data(**{})
        self.assertDictEqual(moved_empty, {})

        moved_found = edition.move_date_documentation_data(**{
            'qg_accept_conditions': [
                {
                    'date_documentation': 'date',
                    'accept_conditions': True
                }
            ]
        })
        self.assertDictEqual(moved_found, {
            'qg_accept_conditions': [{'accept_conditions': True}],
            'tech_qg_250': [{'date_documentation': 'date'}]
        })

        # This used to cause an error ...
        moved_partial_empty = edition.move_date_documentation_data(**{
            'qg_accept_conditions': [
                {
                    'accept_conditions': True
                }
            ]
        })
        self.assertDictEqual(moved_partial_empty, {
            'qg_accept_conditions': [{'accept_conditions': True}]
        })

    def test_delete_tech_groqing_seasons(self):
        edition = self.get_edition()
        delete_empty = edition.delete_tech_growing_seasons(**{})
        self.assertDictEqual(delete_empty, {})

        # Condition not met, no other values in tech_qg_19 (all should be deleted)
        deleted = edition.delete_tech_growing_seasons(**{
            'tech_qg_19': [
                {
                    'tech_growing_seasons': 'foo',
                    'tech_growing_seasons_specify': 'bar',
                }
            ]
        })
        self.assertDictEqual(deleted, {})

        # Condition not met, other values in tech_qg_19 should remain
        deleted = edition.delete_tech_growing_seasons(**{
            'tech_qg_19': [
                {
                    'tech_growing_seasons': 'foo',
                    'tech_growing_seasons_specify': 'bar',
                    'other_key': 'faz'
                }
            ],
            'tech_qg_9': [
                {
                    'tech_landuse_2018': [
                        'something_else'
                    ]
                }
            ]
        })
        self.assertDictEqual(deleted, {
            'tech_qg_19': [
                {
                    'other_key': 'faz'
                }
            ],
            'tech_qg_9': [
                {
                    'tech_landuse_2018': [
                        'something_else'
                    ]
                }
            ]
        })

        # Condition met, no other values in tech_qg_19 (all should be moved)
        moved_found_condition = edition.delete_tech_growing_seasons(**{
            'tech_qg_19': [
                {
                    'tech_growing_seasons': 'foo',
                    'tech_growing_seasons_specify': 'bar',
                }
            ],
            'tech_qg_9': [
                {
                    'tech_landuse_2018': [
                        'tech_lu_cropland',  # Data is only moved if this question is available
                        'something_else',
                    ]
                }
            ]
        })
        self.assertDictEqual(moved_found_condition, {
            'tech_qg_10': [
                {
                    'tech_growing_seasons': 'foo',
                    'tech_growing_seasons_specify': 'bar'
                }
            ],
            'tech_qg_9': [
                {
                    'tech_landuse_2018': [
                        'tech_lu_cropland',
                        'something_else'
                    ]
                }
            ]
        })

        # Condition met, tech_qg_19 has other value (which should stay)
        moved_found_condition_other = edition.delete_tech_growing_seasons(**{
            'tech_qg_19': [
                {
                    'tech_growing_seasons': 'foo',
                    'tech_growing_seasons_specify': 'bar',
                    'other_key': 'faz'
                }
            ],
            'tech_qg_9': [
                {
                    'tech_landuse_2018': [
                        'tech_lu_cropland',  # Data is only moved if this question is available
                        'something_else',
                    ]
                }
            ]
        })
        self.assertDictEqual(moved_found_condition_other, {
            'tech_qg_10': [
                {
                    'tech_growing_seasons': 'foo',
                    'tech_growing_seasons_specify': 'bar'
                }
            ],
            'tech_qg_19': [
                {
                    'other_key': 'faz'
                }
            ],
            'tech_qg_9': [
                {
                    'tech_landuse_2018': [
                        'tech_lu_cropland',
                        'something_else'
                    ]
                }
            ]
        })

        foo = edition.delete_tech_growing_seasons(**{
            "tech_qg_19": [
                {
                    "tech_growing_seasons": "growing_season_1"
                }
            ],
            "tech_qg_20": [
                {
                    "tech_slm_group": [
                        "tech_slm_group_drainage"
                    ]
                }
            ],
            "tech_qg_9": []
        })
        self.assertDictEqual(foo, {
            "tech_qg_20": [
                {
                    "tech_slm_group": [
                        "tech_slm_group_drainage"
                    ]
                }
            ],
            "tech_qg_9": []
        })

class OperationTest(TestCase):

    def test_update_questionnaire_data(self):
        mock_fn = mock.Mock()
        operation = Operation(
            transform_configuration='',
            release_note='',
            transform_questionnaire=mock_fn
        )
        data = {'foo': 'bar'}
        operation.update_questionnaire_data(**data)
        mock_fn.assert_called_once_with(**data)
