import copy

from apps.configuration.configuration import QuestionnaireConfiguration
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.template.loader import render_to_string

from apps.configuration.models import Configuration, Key, Value, Translation, \
    Questiongroup, Category


class Edition:
    """
    Base class for a new edition of a questionnaire configuration, providing a central interface for:

    - Simple, explicit definition for changes in configuration
      - Re-use of operations, with possibility of customizing them (callables)
      - Changes can be tracked per question between editions

    - Verbose display of changes before application

    - Generic helper methods for help texts, release notes and such

    """

    code = ''
    edition = ''
    hierarchy = [
        'sections',
        'categories',
        'subcategories',
        'questiongroups',
        'questions'
    ]
    hierarchy_modules = 'modules'

    def __str__(self):
        return f'{self.code}: Edition {self.edition}'

    @property
    def operations(self):
        raise NotImplementedError('A list of operations is required.')

    def __init__(
            self, key: Key, value: Value, questiongroup: Questiongroup,
            category: Category, configuration: Configuration,
            translation: Translation):
        """
        Load operations, and validate the required instance variables.

        """
        self.key = key
        self.value = value
        self.questiongroup = questiongroup
        self.category = category
        self.configuration = configuration
        self.translation = translation
        self.validate_instance_variables()

    def validate_instance_variables(self):
        for required_variable in ['code', 'edition']:
            if not getattr(self, required_variable):
                raise NotImplementedError('Instance variable "%s" is required' % required_variable)

        if self.code not in [code[0] for code in Configuration.CODE_CHOICES]:
            raise AttributeError('Code %s is not a valid configuration code choice' % self.code)

    def run_operations(self):
        """
        Apply operations, as defined by self.operations

        """
        data = self.get_base_configuration_data()

        for _operation in self.operations:
            data = _operation.migrate(**data)

        self.save_object(**data)

    def get_base_configuration_data(self):
        """
        Get configuration data from the 'previous' version, which is the base for this edition.

        """
        print('code = ', self.code)
        print('edition = ', self.edition)

        objects = self.configuration.objects.all()
        for o in objects:
            print(o, o.code, o.edition)
        return self.configuration.objects.filter(
            code=self.code
        ).exclude(
            code=self.code, edition=self.edition
        ).latest(
            'created'
        ).data

    def save_object(self, **data) -> Configuration:
        """
        Create or update the configuration with the modified data.
        """
        try:
            obj = self.configuration.objects.get(
                edition=self.edition, code=self.code)
        except self.configuration.DoesNotExist:
            obj = self.configuration(edition=self.edition, code=self.code)
        obj.data = data

        # Validate the data before saving.
        questionnaire_configuration = QuestionnaireConfiguration(
            keyword=self.code, configuration_object=obj)
        if questionnaire_configuration.configuration_error:
            raise Exception('Configuration error: %s' %
                            questionnaire_configuration.configuration_error)
        obj.save()
        return obj

    def get_release_notes(self):
        for _operation in self.operations:
            yield _operation.render()

    def update_questionnaire_data(self, **data) -> dict:
        """
        Gets called when creating a new version of a questionnaire in a new
        edition. Calls each operation's "transform_questionnaire" method.
        """
        for _operation in self.operations:
            data = _operation.update_questionnaire_data(**data)
        return data

    @classmethod
    def run_migration(cls, apps, schema_editor):
        """
        Callable for the django migration file. Create an empty migration with:

        ```python manage.py makemigrations configuration --empty```

        Add this tho the operations list:

        operations = [
            migrations.RunPython(<Subclass>.run_migration)
        ]

        """
        if settings.IS_TEST_RUN:
            # This needs discussion! What is expected of this migration in test mode?
            return

        # Models are loaded here, so they are available in the context of a migration.
        model_names = ['Configuration', 'Key', 'Value', 'Translation']
        kwargs = {}

        for model in model_names:
            kwargs[model.lower()] = apps.get_model('configuration', model)

        cls(**kwargs).run_operations()

    @property
    def translation_key(self) -> str:
        """
        Name of the current configuration, used as dict-key in the translation-data
        (see Translation.get_translation)
        """
        return f'{self.code}_{self.edition}'

    def update_translation(self, update_pk: int, **data):
        """
        Helper to replace texts (for choices, checkboxes, labels, etc.).

        Create a new translation for this edition. Adds this configuration with
        edition as a new key to the given (update_pk) translation object.
        """
        obj = self.translation.objects.get(pk=update_pk)
        obj.data.update({self.translation_key: data})
        obj.save()

    def create_new_translation(
            self, translation_type, translation_keys: list=None,
            **data) -> Translation:
        """
        Create and return a new translation entry.
        """
        if translation_keys:
            data = {t: data for t in translation_keys}
        else:
            data = {self.translation_key: data}
        translation, __ = self.translation.objects.get_or_create(
            translation_type=translation_type, data=data)
        return translation

    def create_new_category(
            self, keyword: str, translation: dict or int or None) -> Category:
        if isinstance(translation, dict):
            translation_obj = self.create_new_translation(
                translation_type='category', **translation)
        elif isinstance(translation, int):
            translation_obj = self.translation.objects.get(pk=translation)
        else:
            translation_obj = None
        category, __ = self.category.objects.get_or_create(
            keyword=keyword, translation=translation_obj)
        return category

    def create_new_questiongroup(
            self, keyword: str, translation: dict or int or None) -> Questiongroup:
        if isinstance(translation, dict):
            translation_obj = self.create_new_translation(
                translation_type='questiongroup', **translation)
        elif isinstance(translation, int):
            translation_obj = self.translation.objects.get(pk=translation)
        else:
            translation_obj = None
        configuration = {}
        questiongroup, __ = self.questiongroup.objects.get_or_create(
            keyword=keyword, translation=translation_obj,
            configuration=configuration)
        return questiongroup

    def create_new_question(
            self, keyword: str, translation: dict or int, question_type: str,
            values: list=None, configuration: dict=None) -> Key:
        """
        Create and return a new question (actually, in DB terms, a key), with a
        translation.
        """
        if isinstance(translation, dict):
            translation_obj = self.create_new_translation(
                translation_type='key', **translation)
        else:
            translation_obj = self.translation.objects.get(pk=translation)
        configuration_data = configuration if configuration is not None else {}
        configuration_data.update({'type': question_type})

        try:
            key = self.key.objects.get(keyword=keyword)
            key.translation = translation_obj
            key.configuration = configuration_data
            key.save()
        except ObjectDoesNotExist:
            key = self.key.objects.create(
                keyword=keyword,
                translation=translation_obj,
                configuration=configuration_data
            )

        if values is not None:
            existing_values = key.values.all()
            for new_value in values:
                if new_value not in existing_values:
                    key.values.add(new_value)

        return key

    def create_new_value(
            self, keyword: str, translation: dict or int, order_value: int=None,
            configuration: dict=None, configuration_editions: list=None) -> Value:
        """
        Create and return a new value, with a translation.
        """
        if isinstance(translation, dict):
            translation_obj = self.create_new_translation(
                translation_type='value',
                translation_keys=configuration_editions, **translation)
        else:
            translation_obj = self.translation.objects.get(pk=translation)

        try:
            value = self.value.objects.get(keyword=keyword)
            value.translation = translation_obj
            value.order_value = order_value
            value.configuration = configuration
            value.save()
        except ObjectDoesNotExist:
            value = self.value.objects.create(
                keyword=keyword, translation=translation_obj,
                order_value=order_value, configuration=configuration)

        return value

    def create_new_values_list(self, values_list: list) -> list:
        """Create and return a list of simple values."""
        return [
            self.create_new_value(
                keyword=k,
                translation={
                    'label': {
                        'en': l
                    }
                })
            for k, l in values_list
        ]

    def add_new_value(
            self, question_keyword: str, value: Value, order_value: int=None):
        """
        Add a new value to an existing question.
        """
        key = self.key.objects.get(keyword=question_keyword)
        if order_value and not key.values.filter(pk=value.pk).exists():
            # If order_value is provided and the value was not yet added to the
            # question, update the ordering of the existing values.
            key.values.filter(
                order_value__gte=order_value
            ).update(
                order_value=F('order_value') + 1
            )
        key.values.add(value)

    def get_value(self, keyword: str) -> Value:
        return self.value.objects.get(keyword=keyword)

    def get_question(self, keyword: str) -> Key:
        return self.key.objects.get(keyword=keyword)

    def get_questiongroup(self, keyword: str) -> Questiongroup:
        return self.questiongroup.objects.get(keyword=keyword)

    def find_in_data(self, path: tuple, **data: dict) -> dict:
        """
        Helper to find and return an element inside a configuration data dict.
        Provide a path with keywords pointing to the desired element.

        Drills down to the element assuming the following hierarchy of
        configuration data:

        "data": {
          "sections": [
            {
              "keyword": "<section_keyword>",
              "categories": [
                {
                  "keyword": "<category_keyword>",
                  "subcategories": [
                    {
                      "keyword": "<subcategory_keyword>"
                      "questiongroups": [
                        {
                          "keyword": "<questiongroup_keyword>",
                          "questions": [
                            {
                              "keyword": "<question_keyword>"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ],
          "modules": [
            "cca"
          ]
        }
        """
        for hierarchy_level, path_keyword in enumerate(path):
            # Get the list of elements at the current hierarchy.
            element_list = data[self.hierarchy[hierarchy_level]]
            # Find the element by its keyword.
            data = next((item for item in element_list
                         if item['keyword'] == path_keyword), None)
            if data is None:
                raise KeyError(
                    'No element with keyword %s found in list of %s' % (
                        path_keyword, self.hierarchy[hierarchy_level]))

        return data

    def update_config_data(self, path: tuple, updated, level=0, **data):
        """
        Helper to update a portion of the nested configuration data dict.
        """
        current_hierarchy = self.hierarchy[level]

        # Make a copy of the current data, but reset the children.
        new_data = copy.deepcopy(data)
        new_data[current_hierarchy] = []

        for element in data[current_hierarchy]:
            if element['keyword'] != path[0]:
                new_element = element
            elif len(path) > 1:
                new_element = self.update_config_data(
                    path=path[1:], updated=updated, level=level+1, **element)
            else:
                new_element = updated
            new_data[current_hierarchy].append(new_element)

        return new_data

    def update_data(self, qg_keyword, q_keyword, updated, **data: dict) -> dict:
        """
        Helper to update a question of the questionnaire data dict.
        """
        questiongroup_data = data.get(qg_keyword, [])
        if not questiongroup_data:
            return data

        updated_questiongroup_data = []
        for qg_data in questiongroup_data:
            if q_keyword in qg_data:
                qg_data[q_keyword] = updated
            updated_questiongroup_data.append(qg_data)
        data[qg_keyword] = updated_questiongroup_data
        return data

    def add_new_module(self, updated, **data: dict) -> dict:
        """
        Helper to add a module to the configuration
        """
        # Modules data is fetched
        module_data = data.get(self.hierarchy_modules, [])
        if not module_data:
            return data

        # New module is appended
        module_data.append(updated)

        # Questionnaire configuration is updated with new module and returned
        data[self.hierarchy_modules] = module_data
        return data

    def append_translation(self, update_pk: int, **data):
        """
        Helper to append texts (for choices, checkboxes, labels, etc.).
        """
        obj = self.translation.objects.get(pk=update_pk)
        obj.data.update(data)
        obj.save()


class Operation:
    """
    Data structure for an 'operation' method.
    Centralized wrapper for all operations, so they can be extended / modified
    in a single class.
    """
    default_template = 'configuration/partials/release_note.html'

    def __init__(self, transform_configuration: callable, release_note: str, **kwargs):
        """

        Args:
            transform_configuration: callable for the update on the configuration data
            release_note: string with release note
            **kwargs:
                transform_questionnaire: callable. Used to transform the
                questionnaire data, e.g. for deleted/moved questions.
        """
        self.transform_configuration = transform_configuration
        self.release_note = release_note
        self.template_name = kwargs.get('template_name', self.default_template)
        self.transform_questionnaire = kwargs.get('transform_questionnaire')

    def migrate(self, **data) -> dict:
        return self.transform_configuration(**data)

    def render(self) -> str:
        return render_to_string(
            template_name=self.template_name,
            context={'note': self.release_note}
        )

    def update_questionnaire_data(self, **data):
        if self.transform_questionnaire:
            return self.transform_questionnaire(**data)
        return data
