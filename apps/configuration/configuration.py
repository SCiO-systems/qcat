import contextlib
import collections
import datetime

import floppyforms as forms
from django.apps import apps
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.forms import BaseFormSet, formset_factory
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from apps.configuration.models import (
    Category,
    Configuration,
    Key,
    Questiongroup)
from apps.configuration.utils import get_choices_from_model, get_choices_from_questiongroups
from apps.qcat.errors import (
    ConfigurationError,
    ConfigurationErrorInvalidCondition,
    ConfigurationErrorInvalidConfiguration,
    ConfigurationErrorInvalidOption,
    ConfigurationErrorInvalidQuestiongroupCondition,
    ConfigurationErrorNoConfigurationFound,
    ConfigurationErrorNotInDatabase,
)
from apps.qcat.utils import is_empty_list_of_dicts
from apps.questionnaire.models import File
from .fields import XMLCompatCharField


User = get_user_model()


class BaseConfigurationObject(object):
    """
    This is the base class for all Questionnaire Configuration objects.
    """

    def __init__(self, parent_object, configuration):
        """
        Sets the following attributes for each configuration object:

            ``self.configuration``: The configuration dictionary.

            ``self.keyword``: The keyword identifier of the object.

            ``self.configuration_object``: The database configuration
                object

            ``self.configuration_keyword``: The code of the current
                configuration

            ``self.parent_object``: The parent configuration object.

            ``self.label``: The (translated) label.

            ``self.children``: The child configuration objects if
                available.
        """
        validate_type(
            configuration, dict, self.name_current, 'list of dicts',
            self.name_parent)
        self.configuration = configuration
        self.validate_options()

        keyword = self.configuration.get('keyword')
        if not isinstance(keyword, str):
            raise ConfigurationErrorInvalidConfiguration(
                'keyword', 'str', self.name_current)
        self.keyword = keyword

        if isinstance(self, (
                QuestionnaireSection, QuestionnaireCategory,
                QuestionnaireSubcategory)):
            try:
                self.configuration_object = Category.objects.get(
                    keyword=self.keyword)
            except Category.DoesNotExist:
                raise ConfigurationErrorNotInDatabase(Category, self.keyword)
        elif isinstance(self, QuestionnaireQuestiongroup):
            try:
                self.configuration_object = Questiongroup.objects.get(
                    keyword=self.keyword)
            except Questiongroup.DoesNotExist:
                raise ConfigurationErrorNotInDatabase(
                    Questiongroup, self.keyword)
        elif isinstance(self, QuestionnaireQuestion):
            try:
                self.configuration_object = Key.objects.get(
                    keyword=self.keyword)
            except Key.DoesNotExist:
                raise ConfigurationErrorNotInDatabase(Key, self.keyword)
        else:
            raise Exception('Unknown instance')

        self.configuration_keyword = parent_object.configuration_keyword
        self.edition = parent_object.edition
        self.parent_object = parent_object

        self.helptext = ''
        self.label = ''
        self.label_view = ''
        translation = self.configuration_object.translation
        if translation:
            translation_kwargs = dict(configuration=self.configuration_keyword, edition=self.edition)
            self.helptext = translation.get_translation(
                keyword='helptext', **translation_kwargs
            )
            self.label = translation.get_translation(
                keyword='label', **translation_kwargs
            )
            self.label_view = translation.get_translation(
                keyword='label_view', **translation_kwargs
            )
            if self.label_view is None:
                self.label_view = self.label
            if isinstance(self, QuestionnaireQuestion):
                self.label_filter = translation.get_translation(
                    keyword='label_filter', **translation_kwargs
                )
                if self.label_filter is None:
                    self.label_filter = self.label_view

        # Should be at the bottom of the function
        children = []
        configuration_children = self.configuration.get(self.name_children)
        if configuration_children:
            if (not isinstance(configuration_children, list)
                    or len(configuration_children) == 0):
                raise ConfigurationErrorInvalidConfiguration(
                    self.name_children, 'list of dicts', self.name_current)
            for configuration_child in configuration_children:
                children.append(
                    self.Child(self, configuration_child))
            self.children = children

    def validate_options(self):
        """
        Validate a configuration dict to check if it contains invalid
        options as keys.

        Raises:
            :class:`qcat.errors.ConfigurationErrorInvalidOption`
        """
        invalid_options = list(
            set(self.configuration) - set(self.valid_options))
        if len(invalid_options) > 0:
            raise ConfigurationErrorInvalidOption(
                invalid_options[0], self.configuration, self)

    def get_translation_ids(self) -> list:
        # Recursively get the IDs of all translations objects of the
        # configuration object and its children.

        # Not all configuration objects have a translation
        # (e.g. QuestionnaireConfiguration).
        try:
            res = [self.configuration_object.translation.id]
        except AttributeError:
            res = []

        # Not all configuration objects have children (e.g.
        # QuestionnaireQuestion).
        try:
            for child in self.children:
                res += child.get_translation_ids()
        except AttributeError:
            pass

        # QuestionnaireQuestion objects have values.
        if isinstance(self, QuestionnaireQuestion):
            res += [v.translation.id for v in self.value_objects]

        return res


class QuestionnaireQuestion(BaseConfigurationObject):
    """
    A class representing the configuration of a Question of the
    Questionnaire. A Question basically consists of the Key and optional
    Values (for Questions with predefined Answers)
    """
    valid_options = [
        'keyword',
        'view_options',
        'form_options',
        'filter_options',
        'summary',
    ]
    valid_field_types = [
        'bool',
        'cb_bool',
        'char',
        'checkbox',
        'multi_select',
        'date',
        'file',
        'hidden',
        'image',
        'image_checkbox',
        'link_video',
        'measure',
        'radio',
        'select',
        'select_type',
        'text',
        'todo',
        'user_id',
        'link_id',
        'int',
        'float',
        'map',
        'select_model',
        'select_conditional_questiongroup',
        'select_conditional_custom',
        'display_only',
        'wms_layer',
    ]
    translation_original_prefix = 'original_'
    translation_translation_prefix = 'translation_'
    translation_old_prefix = 'old_'
    value_image_path = 'assets/img/'
    name_current = 'questions'
    name_parent = 'questiongroups'
    name_children = ''
    Child = None

    def __init__(self, parent_object, configuration):
        """
        Parameter ``configuration`` is a ``dict`` containing the
        configuration of the Question. It needs to have the following
        format::

          {
            # The keyword of the key of the question.
            "keyword": "KEY",

            # (optional)
            "view_options": {
              # Default: "default"
              "template": "TEMPLATE_NAME",

              # Default: ""
              "label_position": "",

              # Default: "h5"
              "label_tag": "h5",

              # Default: ""
              "layout": "stacked",

              # Default: false
              "with_raw_values": true,

              # Default: false
              "in_list": true,

              # Default: false
              "is_name": true,
            },

            # (optional)
            "form_options": {
              # Default: "default"
              "template": "TEMPLATE_NAME",

              # Default: None
              "max_length": 500,

              # Default: 3
              "num_rows": 5,

              # Default: ""
              "helptext_position": "tooltip",

              # Default: ""
              "label_position": "placeholder",

              # Default: []
              "questiongroup_conditions": [],
            },

            # (optional)
            "filter_options": {
                "order": 1
            }
          }

        .. seealso::
            For more information on the format and the configuration
            options, please refer to the documentation:
            :doc:`/configuration/questiongroup`

        Raises:
            :class:`qcat.errors.ConfigurationErrorInvalidConfiguration`,
            ``ConfigurationErrorNotInDatabase``.
        """
        super(QuestionnaireQuestion, self).__init__(
            parent_object, configuration)
        self.questiongroup = parent_object

        self.key_config = self.configuration_object.configuration

        self.field_type = self.key_config.get('type', 'char')
        if self.field_type not in self.valid_field_types:
            raise ConfigurationErrorInvalidOption(
                self.field_type, 'type', 'Key')

        view_options = self.key_config.get('view_options', {})
        if configuration.get('view_options'):
            view_options.update(configuration.get('view_options'))
        self.view_options = view_options

        form_options = self.key_config.get('form_options', {})
        if configuration.get('form_options'):
            form_options.update(configuration.get('form_options'))
        self.form_options = form_options

        self.in_list = self.view_options.get('in_list', False) is True
        self.is_name = self.view_options.get('is_name', False) is True
        self.is_geometry = self.view_options.get('is_geometry', False) is True

        self.max_length = self.form_options.get('max_length', None)
        if self.max_length and not isinstance(self.max_length, int):
            self.max_length = None
        self.num_rows = self.form_options.get('num_rows', 3)

        filter_options = self.key_config.get('filter_options', {})
        if configuration.get('filter_options'):
            filter_options.update(configuration.get('filter_options', {}))
        self.filter_options = filter_options

        summary_config = self.key_config.get('summary', {})
        if configuration.get('summary'):
            summary_config.update(configuration.get('summary'))
        self.summary = summary_config

        self.images = []
        self.choices = ()
        self.choices_helptexts = []
        self.value_objects = []
        translation_kwargs = dict(configuration=self.configuration_keyword, edition=self.edition)

        if self.field_type in ['bool']:
            self.choices = ((1, _('Yes')), (0, _('No')))
        elif self.field_type in ['cb_bool']:
            self.choices = ((1, self.label),)
        elif self.field_type in [
                'measure', 'checkbox', 'image_checkbox', 'select_type',
                'select', 'radio', 'select_conditional_custom', 'multi_select']:
            self.value_objects = self.configuration_object.values.all()
            if len(self.value_objects) == 0:
                raise ConfigurationErrorNotInDatabase(
                    self, '[values of key {}]'.format(self.keyword))
            if self.field_type in [
                    'select_type', 'select', 'select_conditional_custom']:
                choices = [('', '-', '')]
            else:
                choices = []
            ordered_values = False
            for i, v in enumerate(self.value_objects):
                if v.order_value:
                    ordered_values = True
                if self.field_type in ['measure']:
                    choices.append((
                        i + 1,
                        v.get_translation(keyword='label', **translation_kwargs),
                        v.get_translation(keyword='helptext', **translation_kwargs)
                    ))
                else:
                    choices.append((
                        v.keyword,
                        v.get_translation(keyword='label', **translation_kwargs),
                        v.get_translation(keyword='helptext', **translation_kwargs)
                    ))
                if self.field_type in ['image_checkbox']:
                    self.images.append('{}{}'.format(
                        self.value_image_path,
                        v.configuration.get('image_name')))
            if ordered_values is False:
                try:
                    choices = sorted(choices, key=lambda tup: tup[1])
                except TypeError:
                    pass
            self.choices = tuple([c[:2] for c in choices])
            self.choices_helptexts = [c[2] for c in choices]

        self.additional_translations = {}
        if self.field_type in ['measure']:
            translation = self.configuration_object.translation
            label_left = translation.get_translation(
                keyword='label_left', **translation_kwargs
            )
            label_right = translation.get_translation(
                keyword='label_right', **translation_kwargs
            )
            self.additional_translations.update(
                {'label_left': label_left, 'label_right': label_right})

        self.conditional = self.form_options.get('conditional', False)

        question_conditions = []
        for question_cond in self.form_options.get('question_conditions', []):
            try:
                cond_expression, cond_name = question_cond.split('|')
            except ValueError:
                raise ConfigurationErrorInvalidCondition(
                    question_cond, 'Needs to have form "expression|name"')
            # Check the condition expression
            try:
                cond_expression = eval('{}{}'.format(0, cond_expression))
            except SyntaxError:
                raise ConfigurationErrorInvalidQuestiongroupCondition(
                    question_cond,
                    'Expression "{}" is not a valid Python condition'.format(
                        cond_expression))
            question_conditions.append(question_cond)

        self.question_conditions = question_conditions
        self.question_condition = self.form_options.get('question_condition')

        conditions = []
        for condition in self.form_options.get('conditions', []):
            try:
                cond_value, cond_expression, cond_key = condition.split('|')
            except ValueError:
                raise ConfigurationErrorInvalidCondition(
                    condition, 'Needs to have form "value|condition|key"')
            # Check that value exists
            if cond_value not in [str(v[0]) for v in self.choices]:
                raise ConfigurationErrorInvalidCondition(
                    condition, 'Value "{}" of condition not found in the Key\''
                    's choices'.format(cond_value))
            # Check the condition expression
            try:
                # todo: don't use eval (here and further down)
                cond_expression = eval(cond_expression)
            except SyntaxError:
                raise ConfigurationErrorInvalidCondition(
                    condition, 'Expression "{}" is not a valid Python '
                    'condition'.format(cond_expression))
            if not isinstance(cond_expression, bool):
                raise ConfigurationErrorInvalidCondition(
                    condition,
                    'Only the following Python expressions are valid: bool')
            # TODO
            # Check that the key exists in the same questiongroup.
            # cond_key_object = self.questiongroup.get_question_by_key_keyword(
            #     cond_key)
            # if cond_key_object is None:
            #     raise ConfigurationErrorInvalidCondition(
            #         condition,
            #         'Key "{}" is not in the same questiongroup'.format(
            #             cond_key))
            # if not (
            #         self.field_type == 'image_checkbox' and
            #         cond_key_object.field_type == 'image_checkbox'):
            #     raise ConfigurationErrorInvalidCondition(
            #         condition, 'Only valid for types "image_checkbox"')
            conditions.append((cond_value, cond_expression, cond_key))
        self.conditions = conditions

        questiongroup_conditions = []
        for questiongroup_condition in self.form_options.get(
                'questiongroup_conditions', []):
            try:
                cond_expression, cond_name = questiongroup_condition.split('|')
            except ValueError:
                raise ConfigurationErrorInvalidQuestiongroupCondition(
                    questiongroup_condition,
                    'Needs to have form "expression|name"')
            # Check the condition expression
            try:
                cond_expression = eval('{}{}'.format(0, cond_expression))
            except SyntaxError:
                raise ConfigurationErrorInvalidQuestiongroupCondition(
                    questiongroup_condition,
                    'Expression "{}" is not a valid Python condition'.format(
                        cond_expression))
            questiongroup_conditions.append(questiongroup_condition)

        self.questiongroup_conditions = questiongroup_conditions

        # TODO
        self.required = False

    def add_form(
            self, formfields, templates, options, show_translation=False,
            edit_mode='edit', questionnaire_data=None):
        """
        Adds one or more fields to a dictionary of formfields.

        Args:
            ``formfields`` (dict): A dictionary of formfields.

            ``templates`` (dict): A dictionary with templates to be used
            to render the questions.

            ``options`` (dict): A dictionary with configuration options
            to be used by the template when rendering the questions.

            ``show_translation`` (bool): A boolean indicating whether to
            add additional fields for translation (``True``) or not
            (``False``). Defaults to ``False``.

            ``edit_mode`` (string): A string indicating the current mode
            of the form (eg. if it is read-only). Defaults to ``edit``.
            Valid options are:

                * ``edit``: Default form rendering.

                * ``view``: Read-only mode, all form fields rendered as
                  disabled.

        Returns:
            ``dict``. The updated formfields dictionary.

            ``dict``. The updated templates dictionary.
        """
        form_template = 'default'
        if self.field_type == 'measure':
            form_template = 'inline_3'
        elif self.field_type == 'image_checkbox':
            form_template = 'no_label'
        form_template = 'form/question/{}.html'.format(
            self.form_options.get('template', form_template))
        field = None
        translation_field = None
        widget = None

        field_options = self.form_options
        field_options.update({
            'helptext': self.helptext,
            'helptext_choices': self.choices_helptexts,
            'additional_translations': self.additional_translations,
        })

        attrs = {}
        if edit_mode == 'view':
            # Read-only mode, disable all input fields.
            attrs.update({'disabled': 'disabled'})

        if field_options.get('label_position') == 'placeholder':
            attrs.update({'placeholder': self.label})

        if self.question_conditions:
            field_options.update(
                {'data-question-conditions': self.question_conditions}
            )

        if self.question_condition:
            field_options.update(
                {'data-question-condition': self.question_condition}
            )

        attrs.update(self.form_options.get('field_options', {}))
        attrs.update({
            'conditional': self.conditional,
            'questiongroup_conditions': ','.join(
                self.questiongroup_conditions)
        })

        # Disable inherited questions.
        if self.parent_object.inherited_configuration:
            attrs.update({
                'disabled': 'disabled'
            })

        if self.field_type in ['char', 'wms_layer']:
            max_length = self.max_length
            if max_length is None:
                max_length = 2000
            widget = TextInput(attrs)
            translation_widget = forms.HiddenInput(attrs)
            if show_translation is True:
                widget = forms.HiddenInput(attrs)
                translation_widget = TextInput(attrs)
            widget.options = field_options
            translation_widget.options = field_options
            field = XMLCompatCharField(
                label=self.label, widget=widget,
                required=self.required, max_length=max_length)
            translation_field = XMLCompatCharField(
                label=self.label, widget=translation_widget,
                required=self.required, max_length=max_length)
        elif self.field_type == 'link_video':
            widget = TextInput(attrs)
            widget.options = field_options
            field = forms.CharField(
                label=self.label, widget=widget,
                required=self.required)
        elif self.field_type in ['date']:
            widget = DateInput(attrs)
            widget.options = field_options
            field = forms.CharField(
                label=self.label, widget=widget, required=self.required)
        elif self.field_type in ['int', 'float']:
            field_options.update({'field_type': self.field_type})
            if self.field_type == 'float':
                attrs.update({'step': 'any'})
            now_year = datetime.datetime.now().year
            if attrs.get('max') == 'now':
                attrs.update({'max': now_year})
            if attrs.get('min') == 'now':
                attrs.update({'min': now_year})
            widget = NumberInput(attrs)
            widget.options = field_options
            field = forms.CharField(
                label=self.label, widget=widget, required=self.required)
        elif self.field_type in [
                'user_id', 'link_id', 'hidden', 'display_only', 'map']:
            widget = HiddenInput()
            if self.field_type == 'user_id':
                widget.css_class = 'select-user-id'
            elif self.field_type == 'link_id':
                widget.css_class = 'select-link-id is-cleared'
            field = forms.CharField(
                label=None, widget=widget, required=self.required)
        elif self.field_type == 'text':
            max_length = self.max_length
            if max_length is None:
                max_length = 5000
            attrs.update({'rows': self.num_rows})
            widget = forms.Textarea(attrs=attrs)
            translation_widget = forms.HiddenInput(attrs=attrs)
            if show_translation is True:
                widget = forms.HiddenInput(attrs=attrs)
                translation_widget = forms.Textarea(attrs=attrs)
            field = XMLCompatCharField(
                label=self.label, widget=widget,
                required=self.required, max_length=max_length)
            translation_field = XMLCompatCharField(
                label=self.label, widget=translation_widget,
                required=self.required)
        elif self.field_type == 'bool':
            widget = RadioSelect(choices=self.choices, attrs=attrs)
            widget.options = field_options
            if self.form_options.get('extra') == 'inline':
                widget.template_name = 'form/field/radio_inline.html'
            if self.keyword == 'accept_conditions':
                widget.template_name = 'form/field/accept_conditions.html'
            field = forms.IntegerField(
                label=self.label, widget=widget,
                required=self.required)
        elif self.field_type == 'measure':
            widget = MeasureSelect(attrs=attrs)
            widget.options = field_options
            if self.form_options.get('layout', '') == 'stacked':
                widget = MeasureSelectStacked()
            field = forms.ChoiceField(
                label=self.label, choices=self.choices, widget=widget,
                required=self.required)
        elif self.field_type == 'select':
            widget = Select(attrs=attrs)
            widget.options = field_options
            widget.searchable = False
            field = forms.ChoiceField(
                label=self.label, choices=self.choices, widget=widget,
                required=self.required)
        elif self.field_type == 'radio':
            widget = RadioSelect(choices=self.choices, attrs=attrs)
            widget.options = field_options
            field = forms.ChoiceField(
                label=self.label, choices=self.choices, widget=widget,
                required=self.required)
        elif self.field_type in ['checkbox', 'cb_bool']:
            widget = Checkbox(attrs=attrs)
            if self.form_options.get('layout', '') == 'measure':
                widget = MeasureCheckbox()
            widget.options = field_options
            field = forms.MultipleChoiceField(
                label=self.label, widget=widget, choices=self.choices,
                required=self.required)
        elif self.field_type in ['multi_select']:
            widget = MultiSelect(attrs=attrs)
            widget.options = field_options
            field = forms.MultipleChoiceField(
                label=self.label, widget=widget, choices=self.choices,
                required=self.required)
        elif self.field_type == 'image_checkbox':
            # Make the image paths available to the widget
            widget = ImageCheckbox(attrs=attrs)
            widget.images = self.images
            widget.options = field_options
            field = forms.MultipleChoiceField(
                label=self.label, widget=widget, choices=self.choices,
                required=self.required)
        elif self.field_type in ['image', 'file']:
            if self.field_type == 'file':
                attrs.update({'css_class': 'upload-file'})
            widget = FileUpload(attrs=attrs)
            formfields['file_{}'.format(self.keyword)] = forms.FileField(
                widget=widget, required=self.required, label=self.label)
            field = forms.CharField(
                required=self.required, widget=forms.HiddenInput())
        elif self.field_type in ['select_type', 'select_conditional_custom']:
            if self.field_type == 'select_conditional_custom':
                attrs.update({
                    'disabled': 'disabled'
                })
            widget = Select(attrs=attrs)
            widget.options = field_options
            widget.searchable = True
            field = forms.ChoiceField(
                label=self.label, widget=widget, choices=self.choices,
                required=self.required)
        elif self.field_type == 'todo':
            field = forms.CharField(
                label=self.label,
                widget=forms.TextInput(
                    attrs={'readonly': 'readonly', 'value': '[TODO]'}),
                required=self.required)
        elif self.field_type == 'select_model':
            attrs.update({
                'data-key-keyword': self.keyword,
            })
            widget = Select(attrs=attrs)
            widget.options = field_options
            widget.searchable = True
            choices = [('', '-')]
            choices.extend(
                get_choices_from_model(self.form_options.get('model')))
            field = forms.ChoiceField(
                label=self.label, widget=widget, choices=choices,
                required=self.required)
        elif self.field_type == 'select_conditional_questiongroup':
            attrs.update({
                'data-key-keyword': self.keyword,
            })
            widget = Select(attrs=attrs)
            widget.options = field_options
            widget.searchable = True
            choices = [('', '-')]
            questiongroups = self.form_options.get(
                'options_by_questiongroups', [])
            widget.options_order = questiongroups
            choices.extend(get_choices_from_questiongroups(
                questionnaire_data, questiongroups, self.configuration_keyword,
                self.edition))
            field = ConditionalQuestiongroupChoiceField(
                label=self.label, widget=widget, choices=choices,
                required=self.required, question=self)
        else:
            raise ConfigurationErrorInvalidOption(
                self.field_type, 'type', self)

        if translation_field is None:
            # Values which are not translated
            formfields[self.keyword] = field
            templates[self.keyword] = form_template
            options[self.keyword] = field_options
        else:
            # Store the old values in a hidden field
            old = forms.CharField(
                label=self.label, widget=forms.HiddenInput(),
                required=self.required)
            if show_translation:
                formfields['{}{}'.format(
                    self.translation_translation_prefix,
                    self.keyword)] = translation_field
            formfields['{}{}'.format(
                self.translation_original_prefix, self.keyword)] = field
            formfields['{}{}'.format(
                self.translation_old_prefix, self.keyword)] = old
            for f in [
                '{}{}'.format(
                    self.translation_translation_prefix,
                    self.keyword),
                '{}{}'.format(
                    self.translation_original_prefix, self.keyword),
                '{}{}'.format(
                    self.translation_old_prefix, self.keyword)
            ]:
                templates[f] = form_template
                options[f] = field_options

        if widget:
            widget.conditional = self.conditional
            widget.questiongroup_conditions = ','.join(
                self.questiongroup_conditions)

        return formfields, templates, options

    def get_details(
            self, data=None, measure_label=None, questionnaire_object=None):
        if data is None:
            data = {}
        MAX_MEASURE_LEVEL = 5
        template_values = self.view_options
        template_values.update({
            'additional_translations': self.additional_translations,
        })
        value = data.get(self.keyword)
        if self.field_type in ['select_conditional_questiongroup']:
            # Determine the options currently valid based on availability of
            # certain questiongroups in the data JSON.
            questiongroups = self.form_options.get(
                'options_by_questiongroups', [])
            questionnaire_data = {}
            if questionnaire_object:
                questionnaire_data = questionnaire_object.data
            self.choices = get_choices_from_questiongroups(
                questionnaire_data, questiongroups, self.configuration_keyword,
                self.edition)
        if self.field_type in [
                'bool', 'measure', 'checkbox', 'image_checkbox',
                'select_type', 'select', 'cb_bool', 'radio',
                'select_conditional_questiongroup',
                'select_conditional_custom', 'multi_select']:
            # Look up the labels for the predefined values
            if not isinstance(value, list):
                value = [value]
            values = self.lookup_choices_labels_by_keywords(value)
        if self.field_type in [
                'char', 'text', 'todo', 'date', 'int', 'display_only']:
            template_name = 'textarea'
            template_values.update({
                'key': self.label_view,
                'value': value,
            })
        elif self.field_type in ['map']:
            template_name = 'map'
            try:
                map_url = reverse('{}:questionnaire_view_map'.format(
                    self.view_options.get('configuration')), kwargs={
                    'identifier': questionnaire_object.code})
            except NoReverseMatch:
                map_url = None
            template_values.update({
                'key': self.label_view,
                'value': value,
                'questionnaire_object': questionnaire_object,
                'map_url': map_url,
            })
        elif self.field_type in ['float']:
            template_name = 'float'
            template_values.update({
                'key': self.label_view,
                'value': value,
                'decimals': self.form_options.get(
                    'field_options', {}).get('decimals'),
            })
        elif self.field_type in ['bool', 'select_type', 'select',
                                 'select_conditional_questiongroup',
                                 'select_conditional_custom']:
            template_name = 'textinput'
            template_values.update({
                'key': self.label_view,
                'value': values[0],
            })
        elif self.field_type in ['measure']:
            template_name = 'measure_bar'
            level = None
            try:
                pos = [c[1] for c in self.choices].index(values[0])
                level = round(pos / len(self.choices) * MAX_MEASURE_LEVEL)
            except ValueError:
                pass
            if measure_label is None:
                key = self.label_view
            else:
                key = measure_label
            template_values.update({
                'key': key,
                'value': values[0],
                'level': level,
            })
        elif self.field_type in ['checkbox', 'cb_bool', 'radio', 'multi_select']:
            # Keep only values which were selected.
            values = [v for v in values if v]

            template_name = 'checkbox'
            if self.view_options.get('with_raw_values') is True:
                # Also add the raw keywords of the values.
                value_keywords = []
                for v in value:
                    if v is not None:
                        i = [y[0] for y in list(self.choices)].index(v)
                        value_keywords.append(self.choices[i][0])
                values = list(zip(values, value_keywords))
            template_values.update({
                'key': self.label_view,
                'values': values,
            })
        elif self.field_type in ['image_checkbox']:
            conditional_outputs = []
            for v in value:
                conditional_rendered = None
                for cond in self.conditions:
                    if v != cond[0]:
                        continue
                    cond_key_object = self.questiongroup.\
                        get_question_by_key_keyword(cond[2])
                    conditional_rendered = cond_key_object.get_details(data)
                conditional_outputs.append(conditional_rendered)

            # Look up the image paths for the values
            images = []
            value_keywords = []
            for v in value:
                if v is not None:
                    i = [y[0] for y in list(self.choices)].index(v)
                    value_keywords.append(self.choices[i][0])
                    images.append(self.images[i])
            template_name = 'image_checkbox'
            if self.conditional:
                template_name = 'image_checkbox_conditional'
            template_values.update({
                'key': self.label_view,
                'values': list(zip(
                    values, images, conditional_outputs, value_keywords)),
            })
        elif self.field_type in ['link_video']:
            template_name = 'video'
            template_values.update({
                'key': self.label_view,
                'value': value,
            })
        elif self.field_type in ['image', 'file']:
            file_data = File.get_data(uid=value)
            template_name = 'file'
            preview_image = ''
            if file_data:
                preview_image = file_data.get('interchange_list')[1][0]
            template_values.update({
                'content_type': file_data.get('content_type'),
                'preview_image': preview_image,
                'key': self.label_view,
                'value': file_data.get('url'),
            })
        elif self.field_type in ['user_id']:
            template_name = 'user_display'
            if value is not None:
                unknown_user = False
                try:
                    user = User.objects.get(pk=value)
                    user_display = user.get_display_name()
                except User.DoesNotExist:
                    unknown_user = True
                    user_display = 'Unknown User'
                template_values.update({
                    'value': user_display,
                    'user_id': value,
                    'unknown_user': unknown_user,
                })
            else:
                return '\n'

        elif self.field_type == 'hidden':
            template_name = 'hidden'
            template_values.update({
                'key': self.label_view,
                'value': value,
            })

        elif self.field_type == 'select_model':
            template_name = 'select_model'
            model = apps.get_model(app_label='configuration', model_name=self.form_options['model'])
            template_values.update({
                'value': value,
                'label': self.label_view,
            })
            try:
                template_values['text'] = model.objects.get(id=value).__str__()
            except model.DoesNotExist:
                # Edge condition for old cases without ID but with display value
                template_values['text'] = data.get(f'{self.keyword}_display', '')
        elif self.field_type in ['link_id']:
            return '\n'

        elif self.field_type in ['wms_layer']:
            template_name = 'wms_layer'
            template_values.update({
                'layer': value,
                'wms_url': self.view_options.get('wms_url'),
            })
        else:
            raise ConfigurationErrorInvalidOption(
                self.field_type, 'type', self)

        if (self.form_options.get('layout') == 'stacked'
                or self.view_options.get('layout') == 'stacked'):
            if self.view_options.get('label_position') == 'none':
                key = None
            # Add all values and their measure value.
            all_values = []
            for choice in self.choices:
                current_level = 1
                for v in values:
                    if v == choice[1]:
                        current_level = MAX_MEASURE_LEVEL
                all_values.append((current_level, choice[1]))
            template_values.update({
                'all_values': all_values,
                'label_text_direction': self.view_options.get(
                    'label_text_direction')
            })

        template_name = self.view_options.get('template', template_name)
        if template_name == 'raw':
            return template_values
        template = 'details/field/{}.html'.format(template_name)
        return render_to_string(template, template_values)

    def lookup_choices_labels_by_keywords(self, keywords):
        """
        Small helper function to lookup the label of choices (values of
        the keys) based on their keyword. If a label is not found, an
        empty string is added as label.

        Args:
            ``keywords`` (list): A list with value keywords.

        Returns:
            ``list``. A list with labels of the values.
        """
        labels = []
        for keyword in keywords:
            if (not isinstance(keyword, str) and not isinstance(keyword, bool)
                    and not isinstance(keyword, int)):
                labels.append('')
            labels.append(dict(self.choices).get(keyword))
        return labels


class QuestionnaireQuestiongroup(BaseConfigurationObject):
    """
    A class representing the configuration of a Questiongroup of the
    Questionnaire.
    """
    valid_options = [
        'keyword',
        'questions',
        'view_options',
        'form_options',
    ]
    default_template = 'default'
    default_min_num = 1
    name_current = 'questiongroups'
    name_parent = 'subcategories'
    name_children = 'questions'
    Child = QuestionnaireQuestion
    inherited_configuration = None
    inherited_questiongroup = None

    def __init__(self, parent_object, configuration):
        """
        Parameter ``configuration`` is a ``dict`` containing the
        configuration of the Questiongroup. It needs to have the
        following format::

          {
            # The keyword of the questiongroup.
            "keyword": "QUESTIONGROUP_KEYWORD",

            # (optional)
            "view_options": {
              # Default: "default"
              "template": "TEMPLATE_NAME",

              # Default: ""
              "conditional_question": "KEY_KEYWORD",

              # Default: ""
              "layout": "before_table"
            },

            # (optional)
            "form_options": {
              # Default: "default"
              "template": "TEMPLATE_NAME",

              # Default: 1
              "min_num": 2,

              # Default: 1
              "max_num: 3,

              # Default: ""
              "numbered": "NUMBERED",

              # Default: ""
              "detail_level": "DETAIL_LEVEL",

              # Default: ""
              "questiongroup_condition": "CONDITION_NAME",

              # Default: "" - can also be a list!
              "layout": "before_table",

              # Default: ""
              "row_class": "no-top-margin".

              # Default: "h4"
              "label_tag": "h5",

              # Default: ""
              "label_class": "",

              # Default: ""
              "table_columns": 2
            },

            # A list of questions.
            "questions": [
              # ...
            ]
          }

        .. seealso::
            For more information on the format and the configuration
            options, please refer to the documentation:
            :doc:`/configuration/questiongroup`

        Raises:
            :class:`qcat.errors.ConfigurationErrorInvalidConfiguration`
        """
        super(QuestionnaireQuestiongroup, self).__init__(
            parent_object, configuration)
        self.questions = self.children

        self.configuration = self.configuration_object.configuration

        view_options = self.configuration.get('view_options', {})
        if configuration.get('view_options'):
            view_options.update(configuration.get('view_options'))
        self.view_options = view_options

        form_options = self.configuration.get('form_options', {})
        if configuration.get('form_options'):
            form_options.update(configuration.get('form_options'))
        self.form_options = form_options

        self.min_num = self.form_options.get('min_num', self.default_min_num)
        if not isinstance(self.min_num, int) or self.min_num < 1:
            raise ConfigurationErrorInvalidConfiguration(
                'min_num', 'integer >= 1', 'questiongroup')

        self.max_num = self.form_options.get('max_num', self.min_num)
        if not isinstance(self.max_num, int) or self.max_num < 1:
            raise ConfigurationErrorInvalidConfiguration(
                'max_num', 'integer >= 1', 'questiongroup')

        self.questiongroup_condition = self.form_options.get(
            'questiongroup_condition')

        self.numbered = self.form_options.get('numbered', '')
        if self.numbered not in ['inline', 'prefix']:
            self.numbered = ''

        self.detail_level = self.form_options.get('detail_level')

        self.inherited_configuration = self.configuration.get(
            'inherited_configuration')
        self.inherited_questiongroup = self.configuration.get(
            'inherited_questiongroup')

        # TODO
        self.required = False

    def get_form(
            self, post_data=None, initial_data=None, show_translation=False,
            edit_mode='edit', edited_questiongroups=None, initial_links=None,
            questionnaire_data=None):
        """
        Returns:
            ``forms.formset_factory``. A formset consisting of one or
            more form fields representing a set of questions belonging
            together and which can possibly be repeated multiple times.
        """
        if edited_questiongroups is None:
            edited_questiongroups = []
        form_template = 'form/questiongroup/{}.html'.format(
            self.form_options.get('template', 'default'))
        # todo: this is a workaround.
        # inspect following problem: the form_template throws an error
        # when the config is loaded from the lru_cache.
        # this is might be caused by mro or mutable types as method
        # kwargs.
        if self.form_options.get('template', '').endswith('.html'):
            form_template = self.form_options.get('template')

        formfields = {}
        templates = {}
        options = {}
        for f in self.questions:
            formfields, templates, options = f.add_form(
                formfields, templates, options, show_translation,
                edit_mode=edit_mode, questionnaire_data=questionnaire_data)

        if self.numbered != '':
            formfields['__order'] = forms.IntegerField(
                label='order', widget=forms.HiddenInput())
            if isinstance(initial_data, list):
                initial_data = sorted(
                    initial_data, key=lambda qg: qg.get('__order', 0))

        Form = type('Form', (forms.Form,), formfields)

        formset_options = {
            'max_num': self.max_num,
            'min_num': self.min_num,
            'extra': 0,
            'validate_max': True,
            'validate_min': False,
        }

        if self.required is True:
            FormSet = formset_factory(
                Form, formset=RequiredFormSet, **formset_options)
        else:
            FormSet = formset_factory(Form, **formset_options)

        if initial_data and len(initial_data) == 1 and initial_data[0] == {}:
            initial_data = None

        has_changes = False
        if self.keyword in edited_questiongroups:
            has_changes = True

        # TODO: Highlight changes disabled.
        # For the time being, the function to show changes has been
        # disabled. Delete the following line to reenable it.
        has_changes = False

        config = self.form_options
        config.update({
            'keyword': self.keyword,
            'helptext': self.helptext,
            'label': self.label,
            'templates': templates,
            'options': options,
            'questiongroup_condition': self.questiongroup_condition,
            'numbered': self.numbered,
            'detail_level': self.detail_level,
            'template': form_template,
            'has_changes': has_changes,
        })

        if self.form_options.get('link'):
            link_name = self.form_options.get('link')
            curr_initial_data = []
            curr_initial_links = initial_links.get(link_name, [])
            for link in curr_initial_links:
                curr_initial_data.append({'link_id': link.get('id')})
            initial_data = curr_initial_data

            try:
                link = reverse('{}:questionnaire_link_search'.format(link_name))
            except NoReverseMatch:
                link = None
            config.update({
                'search_url': link,
                'initial_links': curr_initial_links,
            })

        # This is a fix for editing UNCCD cases where boolean values were stored
        # incorrectly as "false" and "true" instead of 0 and 1.
        if initial_data is not None:
            for data_dict in initial_data:
                for key, value in data_dict.items():
                    if key not in ['unccd_partnership', 'unccd_property_rights',
                                   'unccd_local_stakeholders',
                                   'unccd_population_involved',
                                   'unccd_impact_biodiversity_conservation',
                                   'unccd_impact_cc_mitigation',
                                   'unccd_impact_cc_adaptation',
                                   'unccd_cost_benefit_analysis',
                                   'unccd_technology_disseminated',
                                   'unccd_incentives', 'unccd_replicability']:
                        continue
                    if value is False:
                        data_dict[key] = 0
                    else:
                        data_dict[key] = 1

        return config, FormSet(
            post_data, prefix=self.keyword, initial=initial_data)

    def get_rendered_questions(self, data, questionnaire_object=None):
        questiongroups = []
        for d in data:
            rendered_questions = []
            if self.view_options.get('extra') == 'measure_other':
                measure_label = d.get(self.questions[0].keyword, '')
                rendered_questions.append(
                    self.questions[1].get_details(
                        d, measure_label=measure_label,
                        questionnaire_object=questionnaire_object))
                if len(self.questions) > 2:
                    for question in self.questions[2:]:
                        if question.conditional:
                            continue
                        rendered_questions.append(question.get_details(
                            d, questionnaire_object=questionnaire_object))
            else:
                for question in self.questions:
                    if question.conditional:
                        continue

                    question_details = question.get_details(
                        d, questionnaire_object=questionnaire_object)
                    if question_details:
                        rendered_questions.append(question_details)
            questiongroups.append(rendered_questions)
        return questiongroups

    def get_details(self, data=None, links=None, questionnaire_object=None):
        if data is None:
            data = []
        view_template = 'details/questiongroup/{}.html'.format(
            self.view_options.get('template', 'default'))
        questiongroups = self.get_rendered_questions(
            data, questionnaire_object=questionnaire_object)
        config = self.view_options
        config.update({
            'numbered': self.numbered,
            'label': self.label,
            'label_class': self.view_options.get('label_class'),
        })
        template_values = {
            'questiongroups': questiongroups,
            'config': config,
        }
        if links:
            template_values.update({
                'links': links,
            })
        if self.view_options.get('raw_questions', False) is True:
            raw_questions = []
            for d in data:
                raw_questions.append(self.get_raw_data([d]))
            template_values.update({'raw_questions': raw_questions})
        if self.view_options.get('with_keys', False) is True:
            keys = []
            for q in self.questions:
                keys.append(q.label)
            template_values.update({'keys': keys})
        return render_to_string(
            view_template, template_values)

    def get_question_by_key_keyword(self, key_keyword):
        for question in self.questions:
            if question.keyword == key_keyword:
                return question
        return None

    def get_top_subcategory(self):
        """
        Helper function to get the top subcategory of a questiongroup. This is
        used to display a nicer error message in the form, also stating the
        subcategory (with numbering) in which the error occurred.
        """
        parent = self.parent_object
        next_parent = parent.parent_object
        while not isinstance(next_parent, QuestionnaireCategory):
            parent = next_parent
            next_parent = next_parent.parent_object
        return parent

    def get_raw_data(self, data):
        """
        Return only the raw data of a questiongroup. Data belonging to
        this questiongroup is returned as a flat dictionary. Predefined
        values are looked up to return their display value. The label of
        the key is also added to the dict.

        Args:
            ``questionnaire_data`` (dict): The questionnaire data
            dictionary.

        Returns:
            ``dict``. A flat dictionary with only the keys and values of
            the current questiongroup.
        """
        raw_data = {}
        for question in self.questions:
            for questiongroup_data in data:
                question_data = questiongroup_data.get(
                    question.keyword)
                # Still look up the display values for fields
                # with predefined internal values.
                if question.field_type in [
                        'bool', 'measure', 'checkbox',
                        'image_checkbox', 'select_type', 'radio']:
                    if not isinstance(question_data, list):
                        question_data = [question_data]
                    question_data = question.\
                        lookup_choices_labels_by_keywords(
                            question_data)
                raw_data[question.keyword] = question_data
                raw_data['label_{}'.format(question.keyword)]\
                    = question.label_view
        return raw_data


class QuestionnaireSubcategory(BaseConfigurationObject):
    """
    A class representing the configuration of a Subcategory of the
    Questionnaire.
    """
    valid_options = [
        'keyword',
        'questiongroups',
        'subcategories',
        'form_options',
        'view_options',
    ]
    name_current = 'subcategories'
    name_parent = 'categories'
    name_children = 'questiongroups'
    Child = QuestionnaireQuestiongroup

    def __init__(self, parent_object, configuration):
        """
        Parameter ``configuration`` is a ``dict`` containing the
        configuration of the Subcategory. It needs to have the following
        format::

          {
            # The keyword of the subcategory.
            "keyword": "SUBCAT_KEYWORD",

            # (optional)
            "view_options": {
              # Default: "default"
              "template": "TEMPLATE_NAME",

              # Default: false
              "raw_questions": true,

              # Default: None
              "table_grouping": []
            },

            # (optional)
            "form_options": {
              # Default: "default"
              "template": "TEMPLATE_NAME",

              # Default: ""
              "label_tag": "h3",

              # Default: ""
              "label_class": "top-margin",

              # Default: []
              "questiongroup_conditions": [],

              # Default: ""
              "questiongroup_conditions_template": ""
            },

            # A list of questiongroups.
            "questiongroups": [
              # ...
            ],

            # A list of subcategories.
            "subcategories": [
              # ...
            ]
          }

        .. seealso::
            For more information on the format and the configuration
            options, please refer to the documentation:
            :doc:`/configuration/subcategory`

        Raises:
            :class:`qcat.errors.ConfigurationErrorInvalidConfiguration`,
            ``ConfigurationErrorNotInDatabase``.
        """
        super(QuestionnaireSubcategory, self).__init__(
            parent_object, configuration)

        view_options = self.configuration.get('view_options', {})
        if configuration.get('view_options'):
            view_options.update(configuration.get('view_options'))
        self.view_options = view_options

        form_options = self.configuration.get('form_options', {})
        if configuration.get('form_options'):
            form_options.update(configuration.get('form_options'))
        self.form_options = form_options

        # A Subcategory can have further subcategories or questiongroups
        subcategories = []
        conf_subcategories = self.configuration.get('subcategories', [])
        for conf_subcategory in conf_subcategories:
            subcategories.append(
                QuestionnaireSubcategory(self, conf_subcategory))
        self.subcategories = subcategories

        questiongroups = []
        conf_questiongroups = self.configuration.get('questiongroups', [])
        for conf_questiongroup in conf_questiongroups:
            questiongroups.append(
                QuestionnaireQuestiongroup(self, conf_questiongroup))
        self.questiongroups = questiongroups

        if len(self.subcategories) > 0:
            self.children = self.subcategories
        else:
            self.children = self.questiongroups

        self.link_questiongroups = []
        if self.form_options.get('has_links', False) is True:
            for qg in self.questiongroups:
                if qg.form_options.get('link'):
                    self.link_questiongroups.append(qg.keyword)

        self.table_grouping = self.view_options.get('table_grouping', None)
        self.table_headers = []
        self.table_helptexts = []
        if self.table_grouping:
            for questiongroup in self.questiongroups:
                if questiongroup.keyword in [
                        g[0] for g in self.table_grouping]:
                    for question in questiongroup.questions:
                        self.table_headers.append(question.label)
                        self.table_helptexts.append(question.helptext)

    def get_form(
            self, post_data=None, initial_data=None, show_translation=False,
            edit_mode='edit', edited_questiongroups=None, initial_links=None):
        """
        Returns:
            ``dict``. A dict with configuration elements, namely ``label``.
            ``list``. A list of formsets of question groups, together
            forming a subcategory.
        """
        if initial_data is None:
            initial_data = {}
        if edited_questiongroups is None:
            edited_questiongroups = []
        form_template = 'form/subcategory/{}.html'.format(
            self.form_options.get('template', 'default'))
        formsets = []
        config = self.form_options

        if config.get('questiongroup_conditions_template'):
            config['questiongroup_conditions_template_path'] = \
                'form/field/{}.html'.format(
                    config.get('questiongroup_conditions_template'))

        config.update({
            'label': self.label,
            'keyword': self.keyword,
            'helptext': self.helptext,
            'form_template': form_template,
        })
        has_changes = False
        for questiongroup in self.questiongroups:
            questionset_initial_data = initial_data.get(questiongroup.keyword)
            formsets.append(
                questiongroup.get_form(
                    post_data=post_data, initial_data=questionset_initial_data,
                    show_translation=show_translation, edit_mode=edit_mode,
                    edited_questiongroups=edited_questiongroups,
                    initial_links=initial_links,
                    questionnaire_data=initial_data))
            config['next_level'] = 'questiongroups'
            if questiongroup.keyword in edited_questiongroups:
                has_changes = True
        for subcategory in self.subcategories:
            formsets.append(
                subcategory.get_form(
                    post_data=post_data, initial_data=initial_data,
                    show_translation=show_translation, edit_mode=edit_mode,
                    edited_questiongroups=edited_questiongroups,
                    initial_links=initial_links))
            config['next_level'] = 'subcategories'

        # TODO: Highlight changes disabled.
        # For the time being, the function to show changes has been
        # disabled. Delete the following line to reenable it.
        has_changes = False

        config.update({'has_changes': has_changes})

        if self.table_grouping:
            config.update({
                'table_grouping': self.table_grouping,
                'table_headers': self.table_headers,
                'table_helptexts': self.table_helptexts,
            })

        return config, formsets

    def has_content(self, data):
        """
        Whether this subcategory has content (data) or not.

        Args:
            data: The data dictionary.

        Returns:
            bool.
        """
        for questiongroup in self.questiongroups:
            questiongroup_data = data.get(questiongroup.keyword, [])
            if not is_empty_list_of_dicts(questiongroup_data):
                return True
        return False

    def get_details(self, data=None, links=None, questionnaire_object=None):
        """
        Returns:
            ``string``. A rendered representation of the subcategory
            with its questiongroups.

            ``bool``. A boolean indicating whether the subcategory and
            its questiongroups have some data in them or not.
        """
        if data is None:
            data = {}
        view_template = 'details/subcategory/{}.html'.format(
            self.view_options.get('template', 'default'))
        rendered_questiongroups = []
        rendered_questions = []
        raw_questiongroups = []
        has_content = False
        for questiongroup in self.questiongroups:
            questiongroup_links = {}
            if questiongroup.keyword in self.link_questiongroups:
                try:
                    link_configuration_code = \
                        questiongroup.keyword.rsplit('__', 1)[1]
                except IndexError:
                    link_configuration_code = None

                if links and link_configuration_code is not None:
                    questiongroup_links[link_configuration_code] = links.get(
                        link_configuration_code, [])

            questiongroup_data = data.get(questiongroup.keyword, [])
            if not is_empty_list_of_dicts(questiongroup_data) or \
                    questiongroup_links:
                has_content = True
                if self.table_grouping and questiongroup.keyword in [
                        item for sublist in self.table_grouping
                        for item in sublist]:
                    # Order the values of the questiongroups according
                    # to their questions
                    q_order = [q.keyword for q in questiongroup.questions]
                    # qg_data = []
                    # Add empty values for all keys not available to
                    # keep the order inside the table even with empty
                    # values.
                    for qg in questiongroup_data:
                        for q in q_order:
                            if q not in qg:
                                qg[q] = []

                        # Remove data entries not in q_order anymore (e.g.
                        # removed questions after edition update) to prevent
                        # error when sorting below.
                        for k in set(qg.keys()) - set(q_order):
                            del qg[k]

                    sorted_questiongroup_data = [
                        sorted(qg.items(), key=lambda i: q_order.index(i[0]))
                        for qg in questiongroup_data]

                    data_labelled = []
                    for qg in sorted_questiongroup_data:
                        qg_labelled = []
                        for q in qg:
                            q_value = q[1]
                            q_obj = questiongroup.get_question_by_key_keyword(
                                q[0])
                            if not q_obj:
                                continue
                            if not isinstance(q_value, list):
                                q_value = [q_value]
                            values = []
                            for v in q_value:
                                q_choice = next((
                                    item for item in q_obj.choices if
                                    item[0] == v), None)
                                if q_choice:
                                    values.append(q_choice[1])
                                else:
                                    values.append(v)
                            qg_labelled.append((q_obj.label, values))
                        data_labelled.append(qg_labelled)
                    config = questiongroup.view_options
                    config.update({
                        'qg_keyword': questiongroup.keyword,
                        'data': sorted_questiongroup_data,
                        'data_labelled': data_labelled,
                        'label': questiongroup.label,
                    })
                    raw_questiongroups.append(config)
                elif self.view_options.get('raw_questions', False) is True:
                    config = questiongroup.view_options
                    config.update({
                        'qg': questiongroup.keyword,
                        'questions': questiongroup.get_rendered_questions(
                            questiongroup_data),
                    })
                    rendered_questions.append(config)
                else:
                    questiongroup_config = questiongroup.view_options
                    questiongroup_config.update({
                        'keyword': questiongroup.keyword,
                        'label': questiongroup.label,
                    })
                    rendered_questiongroups.append((
                        questiongroup_config,
                        questiongroup.get_details(
                            questiongroup_data, links=questiongroup_links,
                            questionnaire_object=questionnaire_object)))
        subcategories = []
        for subcategory in self.subcategories:
            sub_rendered, sub_has_content = subcategory.get_details(
                data=data, links=links,
                questionnaire_object=questionnaire_object)
            if sub_has_content:
                subcategories.append(sub_rendered)
                has_content = True

        template_values = self.view_options
        template_values.update({
            'questiongroups': rendered_questiongroups,
            'questions': rendered_questions,
            'subcategories': subcategories,
            'label': self.label_view,
            'label_position': self.view_options.get('label_position'),
            'label_tag': self.view_options.get('label_tag'),
            'label_class': self.view_options.get('label_class'),
            'numbering': self.form_options.get('numbering'),
            'helptext': self.helptext,
        })
        if self.table_grouping:
            template_values.update({
                'table_grouping': self.table_grouping,
                'table_headers': self.table_headers,
                'raw_questiongroups': raw_questiongroups,
            })

        if self.view_options.get('media_gallery', False) is True:
            media_data = self.parent_object.parent_object.parent_object.get_image_data(data)
            media_content = media_data.get('content', [])
            media_additional = media_data.get('additional', {})
            if media_content:
                # If there is at least one image (even though it might be the
                # header image), that's enough to show the current subcategory.
                has_content = True
            template_values.update({
                'media_content': media_content,
                'media_additional': media_additional,
            })

        rendered = render_to_string(view_template, template_values)
        return rendered, has_content


class QuestionnaireCategory(BaseConfigurationObject):
    """
    A class representing the configuration of a Category of the
    Questionnaire.
    """
    valid_options = [
        'keyword',
        'subcategories',
        'view_options',
        'form_options',
    ]
    name_current = 'categories'
    name_parent = 'sections'
    name_children = 'subcategories'
    Child = QuestionnaireSubcategory

    def __init__(self, parent_object, configuration):
        """
        Parameter ``configuration`` is a ``dict`` containing the
        configuration of the Category. It needs to have the following
        format::

          {
            # The keyword of the category.
            "keyword": "CAT_KEYWORD",

            # (optional)
            "view_options": {
              # Default: "default"
              "template": "TEMPLATE_NAME",

              # Default: false
              "use_raw_data": true,

              # Default: false
              "with_metadata": true,

              # Default: {}
              "additional_data": {
                "QUESTIONGROUP": ["KEY"]
              }
            },

            # A list of subcategories.
            "subcategories": [
              {
                # ...
              }
            ]
          }

        .. seealso::
            For more information on the format and the configuration
            options, please refer to the documentation:
            :doc:`/configuration/category`
        """
        super(QuestionnaireCategory, self).__init__(
            parent_object, configuration)
        self.subcategories = self.children

        view_options = self.configuration.get('view_options', {})
        if configuration.get('view_options'):
            view_options.update(configuration.get('view_options'))
        self.view_options = view_options

        form_options = self.configuration.get('form_options', {})
        if configuration.get('form_options'):
            form_options.update(configuration.get('form_options'))
        self.form_options = form_options

    def get_link_questiongroups(self):
        qg = []
        for subcategory in self.subcategories:
            qg.extend(subcategory.link_questiongroups)
        return qg

    def get_form(
            self, post_data=None, initial_data=None, show_translation=False,
            edit_mode='edit', edited_questiongroups=None, initial_links=None):
        """
        Returns:
            ``dict``. A dict with configuration elements, namely ``label``.
            ``list``. A list of a list of subcategory formsets.
        """
        if edited_questiongroups is None:
            edited_questiongroups = []
        subcategory_formsets = []
        for subcategory in self.subcategories:
            subcategory_formsets.append(
                subcategory.get_form(
                    post_data=post_data, initial_data=initial_data,
                    show_translation=show_translation, edit_mode=edit_mode,
                    edited_questiongroups=edited_questiongroups,
                    initial_links=initial_links))
        has_changes = False
        for qg in self.get_questiongroups():
            if qg.keyword in edited_questiongroups:
                has_changes = True
                break

        # TODO: Highlight changes disabled.
        # For the time being, the function to show changes has been
        # disabled. Delete the following line to reenable it.
        has_changes = False

        config = {
            'label': self.label,
            'numbering': self.form_options.get('numbering'),
            'helptext': self.helptext,
            'has_changes': has_changes,
        }
        configuration = self.view_options.get('configuration')
        if configuration:
            config.update({'configuration': configuration})
        return config, subcategory_formsets

    def get_completeness(self, data):
        """
        Return the number of subcategories with content and the total number of
        subcategories.

        Args:
            data: The data dictionary.

        Returns:
            int, int.
        """
        complete = 0
        total = len(self.get_subcategories())
        for subcategory in self.subcategories:
            if subcategory.has_content(data) is True:
                complete += 1
        return complete, total

    def get_subcategories(self):
        """
        Return a list of all subcategories.

        Returns:
            list.
        """
        return [c for c in self.subcategories if
                c.questiongroups or c.subcategories]

    def get_details(
            self, data=None, permissions=None, edit_step_route='',
            questionnaire_object=None, csrf_token=None,
            edited_questiongroups=None, view_mode='view', links=None,
            review_config=None, user=None, completeness_percentage=0):
        if data is None:
            data = {}
        if permissions is None:
            permissions = []
        if edited_questiongroups is None:
            edited_questiongroups = []
        view_template = 'details/category/{}.html'.format(
            self.view_options.get('template', 'default'))
        rendered_subcategories = []
        with_content = 0
        raw_data = {}
        metadata = {}
        for subcategory in self.subcategories:
            rendered_subcategory, has_content = subcategory.get_details(
                data, links=links, questionnaire_object=questionnaire_object)
            if has_content:
                category_config = {
                    'keyword': subcategory.keyword
                }
                rendered_subcategories.append(
                    (rendered_subcategory, category_config))
                with_content += 1

        if (self.view_options.get('with_metadata', False) is True
                and questionnaire_object is not None):
            metadata = questionnaire_object.get_metadata()

        if self.view_options.get('use_raw_data', False) is True:
            raw_data = self.get_raw_category_data(data)

        additional_data = {}
        additional_keys = self.view_options.get('additional_data', {})
        if additional_keys != {}:
            for qg in self.parent_object.parent_object.get_questiongroups():
                if qg.keyword not in [
                        a[0] for a in additional_keys.items()]:
                    continue

                qg_data = data.get(qg.keyword, [])
                for key in additional_keys[qg.keyword]:
                    question = qg.get_question_by_key_keyword(key)
                    additional_entry = []
                    for d in qg_data:
                        k = d.get(key)
                        if k is None:
                            continue
                        if question.field_type in [
                                'bool', 'measure', 'checkbox',
                                'image_checkbox', 'select_type', 'radio']:
                            if not isinstance(k, list):
                                k = [k]
                            k = question.\
                                lookup_choices_labels_by_keywords(k)
                        additional_entry.append(k)
                    additional_data[key] = additional_entry
                    additional_data[
                        'label_{}'.format(key)] = question.label_view

        questionnaire_identifier = 'new'
        if questionnaire_object is not None:
            questionnaire_identifier = questionnaire_object.code

        configuration = self.view_options.get(
            'configuration', self.configuration_keyword)

        has_changes = False
        for qg in self.get_questiongroups():
            if qg.keyword in edited_questiongroups:
                has_changes = True
                break

        # TODO: Highlight changes disabled.
        # For the time being, the function to show changes has been
        # disabled. Delete the following line to reenable it.
        has_changes = False

        categories_with_content = self.get_subcategories()

        history = []
        if questionnaire_object is not None:
            history = questionnaire_object.get_history_versions(user)

        return render_to_string(
            view_template, {
                'subcategories': rendered_subcategories,
                'raw_data': raw_data,
                'additional_data': additional_data,
                'metadata': metadata,
                'label': self.label,
                'numbering': self.form_options.get('numbering'),
                'keyword': self.keyword,
                'csrf_token': csrf_token,
                'permissions': permissions,
                'view_mode': view_mode,
                'complete': with_content,
                'total': len(categories_with_content),
                'progress': int(
                    with_content / len(categories_with_content) * 100),
                'edit_step_route': edit_step_route,
                'configuration_name': configuration,
                'questionnaire_identifier': questionnaire_identifier,
                'questionnaire_object': questionnaire_object,
                'has_changes': has_changes,
                'review_config': review_config,
                'user': user,
                'completeness_percentage': completeness_percentage,
                'history': history,
            })

    def get_raw_category_data(self, questionnaire_data):
        """
        Return only the raw data of a category. The entire questionnaire
        data is scanned for the questiongroups belonging to the current
        category. Only the data of these questiongroups is then
        returned as a flat dict.

        .. important::
            This function may return unexpected outputs when used on
            categories with repeating questiongroups or with keys having
            the same keyword.

        Args:
            ``questionnaire_data`` (dict): The questionnaire data
            dictionary.

        Returns:
            ``dict``. A flat dictionary with only the keys and values of
            the current category.
        """
        raw_category_data = {}
        for subcategory in self.subcategories:
            for questiongroup in subcategory.questiongroups:
                questiongroups_data = questionnaire_data.get(
                    questiongroup.keyword, {})
                raw_category_data.update(questiongroup.get_raw_data(
                    questiongroups_data))
        return raw_category_data

    def get_questiongroups(self):
        def unnest_questiongroups(nested):
            ret = []
            try:
                for child in nested.children:
                    if not isinstance(child, QuestionnaireQuestiongroup):
                        ret.extend(unnest_questiongroups(child))
                    else:
                        ret.append(child)
            except AttributeError:
                pass
            return ret
        return unnest_questiongroups(self)


class QuestionnaireSection(BaseConfigurationObject):
    """
    A class representing the configuration of a Section of the
    Questionnaire.
    """
    valid_options = [
        'categories',
        'keyword',
        'view_options',
    ]
    name_current = 'sections'
    name_parent = None
    name_children = 'categories'
    Child = QuestionnaireCategory

    def __init__(self, parent_object, configuration):
        """
        Parameter ``configuration`` is a ``dict`` containing the
        configuration of the Section. It needs to have the following
        format::

          {
            # The keyword of the section.
            "keyword": "SECTION_KEYWORD",

            # (optional)
            "view_options": {
              # Default: "default"
              "template": "TEMPLATE_NAME",

              # Default: false
              "media_gallery": true
            },

            # A list of categories.
            "categories": [
              {
                # ...
              }
            ]
          }

        .. seealso::
            For more information on the format and the configuration
            options, please refer to the documentation:
            :doc:`/configuration/section`
        """
        super(QuestionnaireSection, self).__init__(
            parent_object, configuration)
        self.categories = self.children

        view_options = self.configuration.get('view_options', {})
        if configuration.get('view_options'):
            view_options.update(configuration.get('view_options'))
        self.view_options = view_options

        form_options = self.configuration.get('form_options', {})
        if configuration.get('form_options'):
            form_options.update(configuration.get('form_options'))
        self.form_options = form_options

    def get_completeness(self, data):
        """
        Return the number of subcategories with content and the total number of
        subcategories.

        Args:
            data: The data dictionary.

        Returns:
            int, int.
        """
        complete = 0
        total = 0
        for category in self.categories:
            complete_category, total_category = category.get_completeness(data)
            total += total_category
            complete += complete_category
        return complete, total

    def get_details(
            self, data=None, permissions=None, review_config=None,
            edit_step_route='', questionnaire_object=None, csrf_token=None,
            edited_questiongroups=None, view_mode='view', links=None, user=None,
            completeness_percentage=0):

        view_template = 'details/section/{}.html'.format(
            self.view_options.get('template', 'default'))

        rendered_categories = []
        for category in self.categories:
            rendered_categories.append(category.get_details(
                data, permissions=permissions, edit_step_route=edit_step_route,
                questionnaire_object=questionnaire_object,
                csrf_token=csrf_token,
                edited_questiongroups=edited_questiongroups,
                view_mode=view_mode, links=links, review_config=review_config,
                user=user, completeness_percentage=completeness_percentage))

        media_content = []
        media_additional = {}
        if self.view_options.get('media_gallery', False) is True:
            media_data = self.parent_object.get_image_data(data)
            media_content = media_data.get('content', [])
            media_additional = media_data.get('additional', {})

        return render_to_string(view_template, {
            'label': self.label,
            'keyword': self.keyword,
            'categories': rendered_categories,
            'media_content': media_content,
            'media_additional': media_additional,
        })

    def get_questiongroups(self):
        def unnest_questiongroups(nested):
            ret = []
            try:
                for child in nested.children:
                    if not isinstance(child, QuestionnaireQuestiongroup):
                        ret.extend(unnest_questiongroups(child))
                    else:
                        ret.append(child)
            except AttributeError:
                pass
            return ret
        return unnest_questiongroups(self)


class QuestionnaireConfiguration(BaseConfigurationObject):
    """
    A class representing the configuration of a Questionnaire.

    .. seealso::
        For more information on the format and the configuration
        options, please refer to the documentation:
        :doc:`/configuration/questionnaire`
    """
    valid_options = [
        'sections',
        'modules',
    ]
    name_current = '-'
    name_parent = '-'
    name_children = 'sections'
    Child = QuestionnaireSection

    def __init__(self, keyword, configuration_object=None):
        self.keyword = keyword
        self.configuration_keyword = keyword
        self.sections = []
        self.modules = []
        self.inherited_data = {}
        self.configuration_object = configuration_object
        if self.configuration_object is None:
            # read_configuration will handle errors if it does not exist
            with contextlib.suppress(Configuration.DoesNotExist):
                self.configuration_object = Configuration.latest_by_code(
                    keyword)
        # Also store edition for easier access
        self.edition = None
        if self.configuration_object:
            self.edition = self.configuration_object.edition
        self.configuration_error = None
        try:
            self.read_configuration()
        except Exception as e:
            if isinstance(e, ConfigurationError):
                self.configuration_error = e
            else:
                raise e

    @property
    def has_new_edition(self):
        return self.configuration_object.has_new_edition

    def get_modules(self):
        return self.modules

    def get_inherited_data(self):
        return self.inherited_data

    def get_configuration_errors(self):
        return self.configuration_error

    @staticmethod
    def get_country_filter(country_keyword):
        """
        Return the query parameters representing a country filter.

        Args:
            country_keyword:

        Returns:

        """
        return 'filter__qg_location__country={}'.format(country_keyword)

    def add_category(self, category):
        self.categories.append(category)

    def get_category(self, keyword):
        for section in self.sections:
            for category in section.categories:
                if category.keyword == keyword:
                    return category
        return None

    def get_questiongroups(self):
        def unnest_questiongroups(nested):
            ret = []
            try:
                for child in nested.children:
                    if not isinstance(child, QuestionnaireQuestiongroup):
                        ret.extend(unnest_questiongroups(child))
                    else:
                        ret.append(child)
            except AttributeError:
                pass
            return ret
        return unnest_questiongroups(self)

    def get_questiongroup_by_keyword(self, keyword):
        for questiongroup in self.get_questiongroups():
            if questiongroup.keyword == keyword:
                return questiongroup
        return None

    def get_question_by_keyword(self, questiongroup_keyword, keyword):
        questiongroup = self.get_questiongroup_by_keyword(
            questiongroup_keyword)
        if questiongroup is not None:
            return questiongroup.get_question_by_key_keyword(keyword)
        return None

    def get_completeness(self, data):
        """
        Return the number of subcategories with content and the total number of
        subcategories.

        Args:
            data: The data dictionary.

        Returns:
            int, int.
        """
        complete = 0
        total = 0
        for section in self.sections:
            complete_section, total_section = section.get_completeness(data)
            complete += complete_section
            total += total_section
        return complete, total

    def get_details(
            self, data=None, permissions=None, review_config=None,
            edit_step_route='', questionnaire_object=None, csrf_token=None,
            edited_questiongroups=None, view_mode='view', links=None, user=None,
            completeness_percentage=0):
        rendered_sections = []
        for section in self.sections:
            rendered_sections.append(section.get_details(
                data, permissions=permissions, review_config=review_config,
                edit_step_route=edit_step_route,
                questionnaire_object=questionnaire_object,
                csrf_token=csrf_token,
                edited_questiongroups=edited_questiongroups,
                view_mode=view_mode,
                links=links,
                user=user,
                completeness_percentage=completeness_percentage))
        return rendered_sections

    def get_toc_data(self):
        categories = []
        for section in self.sections:
            for category in section.categories:
                categories.append((
                    category.keyword, category.label,
                    category.form_options.get('numbering')))
        return categories

    def get_image_data(self, data):
        """
        Return image data from outside the category. Loops through all
        the fields to find the questiongroups containing images. For all
        these, basic information about the images are collected and
        returned as a list of dictionaries.

        Args:
            ``data`` (dict): A questionnaire data dictionary.

        Returns:
            ``list``. A list of dictionaries for each image. Each
            dictionary has the following entries:

            - ``image``: The URL of the original image.

            - ``interchange``: The data which can be used for the
              interchange of images.

            - ``caption``: The caption of the image. Corresponds to
              field ``image_caption``.

            - ``date``: The date of the image. Corresponds to field
              ``image_date``.

            - ``location``: The location of the image. Corresponds to field
              ``image_date``.

            - ``photographer``: The photographer of the image.
              Corresponds to field ``image_photographer``.
        """
        image_questiongroups = []
        additional_data = {}
        for questiongroup in self.get_questiongroups():
            if questiongroup.keyword == 'qg_image_remarks':
                additional_data.update(
                    questiongroup.get_raw_data(
                        data.get('qg_image_remarks', [])))
            for question in questiongroup.questions:
                if question.field_type == 'image' and data.get(
                        questiongroup.keyword) is not None:
                    image_questiongroups.extend(
                        data.get(questiongroup.keyword))

        images = []
        for image in image_questiongroups:
            # Maybe it is not a real image (e.g. maps can also be uploaded as
            # images)
            if image.get('image') is None:
                continue
            image_data = File.get_data(uid=image.get('image'))
            images.append({
                'image': image_data.get('url'),
                'interchange': image_data.get('interchange'),
                'interchange_list': image_data.get('interchange_list'),
                'caption': image.get('image_caption'),
                'date': image.get('image_date'),
                'location': image.get('image_location'),
                'photographer': image.get('image_photographer'),
                'absolute_path': image_data.get('absolute_path'),
                'relative_path': image_data.get('relative_path'),
                'target': image.get('image_target'),
            })
        return {
            'content': images,
            'additional': additional_data,
        }

    def get_filter_keys(self):
        """
        Return a list of FilterKey named tuples containing information about the
        filterable keys.

        Returns:
            List of FilterKey named tuples.
        """
        # Note that path and label need to appear first so they can be used as
        # select options.
        FilterKey = collections.namedtuple(
            'FilterKey',
            ['path', 'label', 'order', 'key', 'questiongroup', 'filter_type',
             'section_label'])
        filter_keys = []
        for questiongroup in self.get_questiongroups():
            for question in questiongroup.questions:
                if question.filter_options and question.filter_options.get('order') is not None:
                    section = questiongroup.get_top_subcategory().parent_object
                    filter_keys.append(FilterKey(
                        path=f'{questiongroup.keyword}__{question.keyword}',
                        label=question.label_filter,
                        order=question.filter_options.get('order'),
                        key=question.keyword,
                        questiongroup=questiongroup.keyword,
                        filter_type=question.field_type,
                        section_label=section.label))
        return sorted(filter_keys, key=lambda k: k.order)

    def get_list_data(self, questionnaire_data_list):
        """
        Get the data for the list representation of questionnaires.
        Which questions are shown depends largely on the option
        ``in_list`` of the question configuration.

        Args:
            ``questionnaire_data_list`` (list): A list of Questionnaire
            data dicts.

        Returns:
            ``list``. A list of dicts. A dict containing the keys and
            values to be appearing in the list. The values are not
            translated.
        """
        # Collect which keys are to be shown in the list.
        list_configuration = []
        for questiongroup in self.get_questiongroups():
            for question in questiongroup.questions:
                if question.in_list is True:
                    list_configuration.append((
                        questiongroup.keyword, question.keyword,
                        question.field_type))

        questionnaire_value_list = []
        for questionnaire_data in questionnaire_data_list:
            questionnaire_value = {}
            for list_entry in list_configuration:
                for question_data in questionnaire_data.get(list_entry[0], []):
                    key = list_entry[1]
                    value = question_data.get(list_entry[1])
                    if list_entry[2] == 'image':
                        key = 'image'
                        if questionnaire_value.get(key):
                            # If there is already an image, do not add it again
                            continue
                        image_data = File.get_data(uid=value)
                        interchange_list = image_data.get('interchange_list')
                        if interchange_list:
                            value = interchange_list[0][0]
                    if list_entry[2] in [
                            'bool', 'measure', 'checkbox', 'image_checkbox',
                            'select_type']:
                        # Look up the labels for the predefined values
                        if not isinstance(value, list):
                            value = [value]
                        qg = self.get_questiongroup_by_keyword(list_entry[0])
                        if qg is None:
                            break
                        k = qg.get_question_by_key_keyword(list_entry[1])
                        if k is None:
                            break
                        values = k.lookup_choices_labels_by_keywords(value)
                        if list_entry[2] in ['bool', 'measure', 'select_type']:
                            value = values[0]
                    questionnaire_value[key] = value
            # 'remap' keys for description field, providing a consistent access key.
            mapping = {
                'approaches': 'app_definition',
                'cca': 'tech_definition',
                'cbp': 'tech_definition',
                'sample': 'key_5',
                'samplemodule': 'modkey_01',
                'samplemulti': 'mkey_01',
                'technologies': 'tech_definition',
                'unccd': 'unccd_description',
                'watershed': 'app_definition'
            }

            # For testing configurations (e.g. 'sample', 'samplemulti'), there
            # is no qg_name/name questiongroup/key. Instead, it relies on the
            # (probably deprecated) "is_name" key in the configuration json. In
            # order to add their name correctly to the list data, they are added
            # manually here.
            if 'name' not in questionnaire_value:
                name_key, name_qg = self.get_name_keywords()
                if name_key is not None:
                    questionnaire_value['name'] = questionnaire_data.get(
                        name_qg, [{}])[0].get(name_key, {})

            # If configuration mapping is not set up, a KeyError will be raised.
            questionnaire_value['definition'] = questionnaire_value.get(
                mapping[self.keyword], {'en': ''}
            )

            questionnaire_value_list.append(questionnaire_value)
        return questionnaire_value_list

    def get_name_keywords(self):
        """
        Return the keywords of the question and questiongroup which
        contain the name of the questionnaire as defined in the
        configuration by the ``is_name`` parameter.
        """
        question_keyword = None
        questiongroup_keyword = None
        for questiongroup in self.get_questiongroups():
            for question in questiongroup.questions:
                if question.is_name is True:
                    question_keyword = question.keyword
                    questiongroup_keyword = questiongroup.keyword
        return question_keyword, questiongroup_keyword

    def get_geometry_keywords(self):
        """
        Return the keywords of the question and questiongroup which
        contain the name of the questionnaire as defined in the
        configuration by the ``is_geometry`` parameter.
        """
        question_keyword = None
        questiongroup_keyword = None
        for questiongroup in self.get_questiongroups():
            for question in questiongroup.questions:
                if question.is_geometry is True:
                    question_keyword = question.keyword
                    questiongroup_keyword = questiongroup.keyword
        return question_keyword, questiongroup_keyword

    def get_description_keywords(self, keys):
        """
        Get a list of tuples in the form of 'questiongroup': 'keyword' for
        given keys.

        Args:
            keys: list
        Returns:
            list of namedtuples
        """
        question_keywords = []
        keyword = collections.namedtuple('Keyword', 'questiongroup question')
        for questiongroup in self.get_questiongroups():
            for question in questiongroup.questions:
                if question.keyword in keys:
                    question_keywords.append(
                        keyword(questiongroup.keyword, question.keyword)
                    )
        return question_keywords

    def get_questionnaire_name(self, questionnaire_data):
        """
        Return the value of the key flagged with ``is_name`` of a
        Questionnaire.

        Args:
            ``questionnaire_data`` (dict): A translated questionnaire
            data dictionary.

        Returns:
            ``str``. Returns the value of the key or ``Unknown`` if the
            key was not found in the data dictionary.
        """
        question_keyword, questiongroup_keyword = self.get_name_keywords()
        if question_keyword:
            for x in questionnaire_data.get(questiongroup_keyword, []):
                return x.get(question_keyword)
        # fixme: what should happen in case no name is set? as of now, "{'en': 'Unknown name'}" is displayed, which is
        # fixme: ugly, but should not happen, as the name is validated by the publishers.
        return {'en': _('Unknown name')}

    def get_questionnaire_geometry(self, questionnaire_data):
        question_keyword, questiongroup_keyword = self.get_geometry_keywords()
        if question_keyword:
            for x in questionnaire_data.get(questiongroup_keyword, []):
                return x.get(question_keyword)
        return None

    def get_questionnaire_description(self, questionnaire_data, keys):
        """
        Get the contents of given strings

        Args:
            keys: list
            questionnaire_data: dict

        Returns:
            dict: language as key, concatenated content as value.
        """
        keywords = self.get_description_keywords(keys)
        excerpt_data = collections.defaultdict(str)

        for keyword in keywords:
            for x in questionnaire_data.get(keyword.questiongroup, []):
                if x.get(keyword.question):
                    for language, text in x[keyword.question].items():
                        excerpt_data[language] += '{} '.format(text)
        return excerpt_data

    def get_user_fields(self):
        """
        [0]: questiongroup keyword
        [1]: key keyword (id)
        [2]: key keyword (displayname)
        [3]: user role
        """
        user_fields = []
        for questiongroup in self.get_questiongroups():
            user_role = questiongroup.form_options.get('user_role')
            if user_role is None:
                continue
            for question in questiongroup.questions:
                if question.field_type != 'user_id':
                    continue
                user_fields.append(
                    (questiongroup.keyword, question.keyword,
                        question.form_options.get('display_field'), user_role))
        return user_fields

    def read_configuration(self):
        """
        This function reads an active configuration of a Questionnaire.
        If a configuration is found, it loads the configuration of all
        its sections.

        The configuration of the questionnaire needs to have the
        following format::

          {
            # See class QuestionnaireSection for the format of sections.
            "sections": [
              # ...
            ]
          }

        .. seealso::
            :class:`configuration.configuration.QuestionnaireSection`

        .. seealso::
            :doc:`/configuration/questionnaire`
        """
        if self.configuration_object is None:
            raise ConfigurationErrorNoConfigurationFound(self.keyword)

        self.configuration = self.configuration_object.data
        self.validate_options()

        conf_sections = self.configuration.get('sections')
        validate_type(
            conf_sections, list, 'sections', 'list of dicts', '-')

        for conf_section in conf_sections:
            self.sections.append(QuestionnaireSection(self, conf_section))
        self.children = self.sections

        self.modules = self.configuration.get('modules', [])

        inherited_data = {}
        for qg in self.get_questiongroups():
            if qg.inherited_configuration:
                inherited_by_configuration = inherited_data.get(
                    qg.inherited_configuration, {})
                inherited_by_configuration.update(
                    {qg.inherited_questiongroup: qg.keyword})
                inherited_data[
                    qg.inherited_configuration] = inherited_by_configuration
        self.inherited_data = inherited_data


def validate_type(obj, type_, conf_name, type_name, parent_conf_name):
    """
    Validate a type of object.

    Args:
        ``obj`` (obj): The object to validate.

        ``type_`` (type): A Python type (e.g. ``list``, ``dict``).

        ``conf_name`` (str): The name of the configuration entry (used
        for the error message)

        ``type_name`` (str): The name of the expected type (used for the
        error message)

        ``parent_conf_name`` (str): The name of the parent configuration
        entry (used for the error message)

    Raises:
        :class:`qcat.errors.ConfigurationErrorInvalidConfiguration`
    """
    if not isinstance(obj, type_):
        raise ConfigurationErrorInvalidConfiguration(
            conf_name, type_name, parent_conf_name)


class DateInput(forms.DateInput):
    template_name = 'form/field/dateinput.html'

    def get_context_data(self):
        ctx = super(DateInput, self).get_context_data()
        ctx.update({
            'options': self.options,
            'date_format': 'dd/mm/yy',
        })
        return ctx


class NumberInput(forms.NumberInput):
    template_name = 'form/field/numberinput.html'

    def get_context_data(self):
        ctx = super(NumberInput, self).get_context_data()
        ctx.update({
            'options': self.options,
        })
        return ctx


class TextInput(forms.TextInput):
    template_name = 'form/field/textinput.html'

    def get_context_data(self):
        ctx = super(TextInput, self).get_context_data()
        ctx.update({
            'options': self.options,
        })
        return ctx


class HiddenInput(forms.TextInput):
    template_name = 'form/field/hidden.html'

    def get_context_data(self):
        ctx = super(HiddenInput, self).get_context_data()
        if hasattr(self, 'css_class'):
            ctx.update({
                'css_class': self.css_class
            })
        return ctx


class ConditionalMixin:

    def get_context_data(self):
        ctx = super().get_context_data()
        ctx.update({
            'questiongroup_conditions': self.attrs['questiongroup_conditions'],
            'conditional': self.attrs['conditional'],
        })
        return ctx


class RadioSelect(ConditionalMixin, forms.RadioSelect):
    """
    A custom form class for a Radio Select field. Allows to overwrite
    the template used.
    """
    template_name = 'form/field/radio.html'

    def get_context_data(self):
        """
        Add the questiongroup conditions to the context data so they are
        available within the template of the widget.
        """
        ctx = super(RadioSelect, self).get_context_data()
        ctx.update({
            'options': self.options,
        })
        return ctx


class Select(ConditionalMixin, forms.Select):
    template_name = 'form/field/select.html'

    def get_context_data(self):
        """
        Add a variable (searchable or not) to the context data so it is
        available within the template of the widget.
        """
        ctx = super(Select, self).get_context_data()
        try:
            options_order = self.options_order
        except AttributeError:
            options_order = []
        ctx.update({
            'searchable': self.searchable,
            'options_order': options_order,
            'options': self.options,
        })
        return ctx


class MeasureSelect(ConditionalMixin, forms.RadioSelect):
    template_name = 'form/field/measure.html'

    def get_context_data(self):
        """
        Add the questiongroup conditions to the context data so they are
        available within the template of the widget.
        """
        ctx = super(MeasureSelect, self).get_context_data()
        ctx.update({
            'options': self.options,
        })
        return ctx


class MeasureSelectStacked(ConditionalMixin, forms.RadioSelect):
    template_name = 'form/field/measure_stacked.html'

    def get_context_data(self):
        """
        Add the questiongroup conditions to the context data so they are
        available within the template of the widget.
        """
        ctx = super(MeasureSelectStacked, self).get_context_data()
        ctx.update({
            'options': self.options,
        })
        return ctx


class MultiSelect(ConditionalMixin, forms.SelectMultiple):
    template_name = 'form/field/select.html'

    def get_context_data(self):
        ctx = super(MultiSelect, self).get_context_data()
        ctx.update({
            'options': self.options,
            'searchable': True,
        })
        return ctx


class Checkbox(ConditionalMixin, forms.CheckboxSelectMultiple):
    template_name = 'form/field/checkbox.html'

    def get_context_data(self):
        """
        Add the questiongroup conditions to the context data so they are
        available within the template of the widget.
        """
        ctx = super(Checkbox, self).get_context_data()
        ctx.update({
            'options': self.options,
        })
        return ctx


class ImageCheckbox(ConditionalMixin, forms.CheckboxSelectMultiple):
    template_name = 'form/field/image_checkbox.html'

    def get_context_data(self):
        """
        Add the image paths to the context data so they are available
        within the template of the widget.
        """
        ctx = super(ImageCheckbox, self).get_context_data()
        ctx.update({
            'images': self.images,
            'options': self.options,
        })
        return ctx


class ConditionalQuestiongroupChoiceField(ConditionalMixin, forms.ChoiceField):
    """
    A Choice field whose choices are based on the presence of certain
    questiongroups in the data JSON.
    """
    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop('question')
        super(ConditionalQuestiongroupChoiceField, self).__init__(*args, **kwargs)

    def validate(self, value):
        questiongroups = self.question.form_options.get(
            'options_by_questiongroups', [])
        return value in questiongroups


class FileUpload(forms.FileInput):
    template_name = 'form/field/file_upload.html'


class RequiredFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        super(RequiredFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = True


class MeasureCheckbox(forms.CheckboxSelectMultiple):
    template_name = 'form/field/checkbox_measure.html'
