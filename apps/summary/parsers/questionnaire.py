"""
Parse data of combined configuration and questionnaire-data and provide some
additional methods to extract data as required for the summary.
"""
import collections
import contextlib
import itertools
import logging
import operator

from django.conf import settings

from apps.configuration.configuration import QuestionnaireQuestion, \
    QuestionnaireSubcategory
from apps.configuration.configured_questionnaire import ConfiguredQuestionnaire
from apps.qcat.errors import ConfigurationError
from apps.questionnaire.models import Questionnaire
from apps.questionnaire.templatetags.questionnaire_tags import get_static_map_url

logger = logging.getLogger(__name__)


class QuestionnaireParser(ConfiguredQuestionnaire):
    """
    Get only data which is configured to appear in the summary. This is defined
    by the configuration-field: 'summary', which specifies the section
    of the summary for given field for the chosen summary-config (e.g. 'full',
    'one page', 'four page').
    """

    def __init__(self, config, summary_type: str, n_a: str,
                 questionnaire: Questionnaire, **data):
        self.summary_type = summary_type
        self.data = {}
        self.n_a = n_a
        self.config_object = config
        super().__init__(questionnaire=questionnaire, config=config, **data)

    def put_question_data(self, child: QuestionnaireQuestion):
        """
        Put the value to self.data, using the name as defined in the config
        ('summary': {'this_type': <key_name>}}.
        As some key names are duplicated by virtue (config may use the same
        question twice), but represent different and important content, some
        keys are overridden with the help of the questions questiongroup.

        This cannot be solved on the config as the same question is listed
        twice, so the key-name overriding setting must be ready for versioning.
        """
        if child.summary and self.summary_type in child.summary['types']:
            options = {
                **child.summary['default'],
                **child.summary.get(self.summary_type, {})
            }
            if 'field_name' not in options:
                raise ConfigurationError(
                    'At least a unique field name must be set for "summary" '
                    'config for the question {}.'.format(child.keyword)
                )
            field_name = self.get_configured_field_name(
                child=child,
                field_name=options['field_name']
            )

            if field_name not in self.data:
                self.data[field_name] = self.get_configured_value(
                    child=child, **options
                )

    def get_configured_value(self, child: QuestionnaireQuestion, **kwargs):
        configured_fn = kwargs.get('get_value')
        if not configured_fn:
            return self.get_value(child=child)
        else:
            fn = getattr(self, configured_fn['name'])
            return fn(child=child, **configured_fn.get('kwargs', {}))

    def get_configured_field_name(self, child: QuestionnaireQuestion,
                                  field_name: str) -> str:
        if not isinstance(field_name, dict):
            return field_name
        else:
            qg_field = '{questiongroup}.{field}'.format(
                questiongroup=child.questiongroup.keyword,
                field=child.keyword
            )
            try:
                return field_name[qg_field]
            except KeyError:
                raise ConfigurationError('No field_name for '
                                         'summary field {}'.format(qg_field))

    def get_map_values(self, child: QuestionnaireQuestion) -> dict:
        """
        Configured function (see ConfigurationConf) for special preparation of
        data to display map data.
        """
        if not self.questionnaire.geom:
            return {'img_url': '', 'coordinates': []}
        else:
            return {
                'img_url': get_static_map_url(self.questionnaire),
                'coordinates': [
                    '{}, {}'.format(round(coords[0], 5), round(coords[1], 5))
                    for coords in self.questionnaire.geom.coords
                ]
            }

    def get_full_range_values(self, child: QuestionnaireQuestion,
                              is_radio=False):
        """
        Get all available elements, with the selected ones highlighted.
        """
        values = self.values.get(child.parent_object.keyword)
        # elements without a selected value must be shown, if more than one list
        # of values exists, this method must be extended.
        if values and len(values) == 1:
            selected = values[0].get(child.keyword, [])
        else:
            if settings.DEBUG:
                logger.warning('No or more than one list of values is set for '
                               '{keyword}'.format(keyword=child.keyword))
            selected = []

        # default is 'checkbox', where multiple elements can be selected.
        is_highlighted = operator.eq if is_radio else operator.contains

        for choice in child.choices:
            yield {
                'highlighted': is_highlighted(selected, choice[0]),
                'text': choice[1]
            }

    def get_picto_and_nested_values(self, child: QuestionnaireQuestion):
        """
        Get selected element with parents and pictos. The given question may
        be a child of several nested questiongroups.
        """
        try:
            selected = self.get_value(child)[0]['values']
        except (KeyError, IndexError):
            return None

        # get all nested elements in the form '==question|nested'...
        nested_elements_config = child.form_options.get(
            'questiongroup_conditions', []
        )
        # ..and split the strings to a more usable dict.
        nested_elements = dict(self.split_raw_children(*nested_elements_config))
        for value in selected:
            yield self.get_default_picto_values(
                value_tuple=value,
                nested_children=nested_elements
            )

    def get_default_picto_values(
            self, value_tuple: tuple, nested_children: dict):
        """
        Return the nested picto values (subquestions) as concatenated string.
        """
        is_in_child_list = lambda child: child.keyword in child_values
        child_text = '<strong>{title}</strong> - '.format(title=value_tuple[0])
        # 'value_tuple' is a tuple of four elements: title, icon-url, ?, keyword
        # this represents the 'parent' question with an image
        selected_children_keyword = nested_children.get(value_tuple[3])
        # selected_children are the 'sub-selections' of given 'value'
        if selected_children_keyword:
            # To keep ordering as defined on the questiongroup, loop over
            # the children, skipping the ones not filled in.
            selected_qg = self.config_object.get_questiongroup_by_keyword(
                selected_children_keyword
            )
            try:
                child_values = self.values.get(
                    selected_children_keyword, {}
                )[0]
            except (IndexError, KeyError):
                return {
                    'url': value_tuple[1],
                    'text': child_text
                }

            # Load the configured question for the children and get their
            # labels - they will be concatenated as 'text' below.
            # the structure is nested as follows:
            # [{'keyword': 'value'}, {'keyword', 'value'}]
            for child in filter(is_in_child_list, selected_qg.children):
                child_value = child_values.get(child.keyword)
                child_text += self._concatenate_child_question_texts(
                    child_question=child,
                    selected_child_len=len(child_values),
                    values=child_value
                )
        return {
            'url': value_tuple[1],
            'text': child_text
        }

    def _get_choice_label(
            self, child: QuestionnaireQuestion, value: any) -> str or None:
        return dict(child.choices).get(value)

    def _get_qg_selected_value(self, child: QuestionnaireQuestion,
                               all_values=False, index=0):
        values = {}
        with contextlib.suppress(IndexError):
            values = self.values.get(child.questiongroup.keyword, [])[index]
        return values.get(child.keyword) if not all_values else values

    def _qg_scale_format(self, child: QuestionnaireQuestion, value: int,
                         **kwargs):
        yield {
            'label': kwargs.get('label', child.label),
            'range': range(0, kwargs.get('range', len(child.choices))),
            'min': kwargs.get('label_left'),
            'max': kwargs.get('label_right'),
            'selected': value - 1 if value else None,
            'comment': kwargs.get('comment', '')
        }

    def _concatenate_child_question_texts(
            self, child_question: QuestionnaireQuestion,
            selected_child_len: int, values: list) -> str:
        """
        Helper to print nice concatenated strings
        """
        choices_labels = dict(child_question.choices)
        # Show label only if it is configured to be shown
        has_label = child_question.view_options.get('label_position') != 'none'
        # If more than one element is selected for the current
        # group, add a newline
        if isinstance(values, str) or isinstance(values, int):
            text = values
        elif values:
            text = ', '.join([choices_labels[choice] for choice in values])
        else:
            text = ''

        text_parts = dict(
            label='{}: '.format(child_question.label) if has_label else '',
            multi_line='<br>' if selected_child_len > 1 else '',
            text=text,
        )
        return '{label}{text}{multi_line}'.format_map(text_parts)

    def split_raw_children(self, *children):
        """
        Split the list of raw strings and strip the unnecessary chars
        """
        for child in children:
            lhs, rhs = child.split('|')
            yield self.stripchars(lhs), self.stripchars(rhs)

    @staticmethod
    def stripchars(raw: str) -> str:
        strip = ['=', "'"]
        return ''.join([c for c in raw if c not in strip])

    def get_table(self, child: QuestionnaireQuestion):
        """
        Table-like format for maintenance and establishment cost.
        """
        table = {
            'head': collections.defaultdict(dict),
            'partials': []
        }
        questiongroups = self.get_questiongroups_in_table(
            section=child.questiongroup.parent_object
        )
        has_content = False
        # structure:
        # a questiongroup consists of typically 6 questions. these are the
        # columns. the number of columns is fixed for all questiongroups in
        # the table.
        # the rows are the values that the user has filled in (0-n).
        # so always print the 'header' row, and 0-n rows with values
        for questiongroup in questiongroups:
            partials = collections.OrderedDict()

            for column, question in enumerate(questiongroup.questions):
                column = str(column)
                values = self.get_value(child=question)
                if not values:
                    continue

                # Special case: the total is saved in the last question. Skip
                # creating the table header and such, and only fill in the
                # minimal necessary values.
                special_cases = (
                    ('_total_costs', 'total'),
                    ('_total_costs_usd', 'total_usd'),
                )
                is_special = False
                for sc in special_cases:
                    if question.keyword.endswith(sc[0]):
                        # Try to format it a bit nicer
                        val = values[0].get('value')
                        try:
                            val = '{:,}'.format(val).replace(',', "'")
                        except ValueError:
                            pass
                        table[sc[1]] = {
                            'label': values[0].get('key'),
                            'value': val,
                        }
                        is_special = True

                if is_special:
                    continue

                for row, value in enumerate(values):
                    if not table['head'][column] and value.get('key'):
                        table['head'][column] = value['key']
                    element = partials.setdefault(row, {})
                    element[column] = value.get('value') or ''

            if partials:
                table['partials'].append({
                    'head': questiongroup.label,
                    'items': partials.values()
                })
                has_content = True

        return table if has_content else {}

    def get_questiongroups_in_table(self, section: QuestionnaireSubcategory):
        """
        Get only questiongroups that are configured to be shown in the table.
        """
        used = list(itertools.chain(*section.table_grouping))
        for questiongroup in section.questiongroups:
            if questiongroup.keyword in used:
                yield questiongroup

    def get_qg_values_with_label_scale(self, child: QuestionnaireQuestion):
        items = []
        for group in child.questiongroup.parent_object.questiongroups:
            values = self._get_qg_selected_value(group.children[0], all_values=True)

            # 'other' values have no choices.
            if group.questions[0].choices:
                label = group.label
                selected_question = 0
                text_question = 1
            else:
                group_values = self.values.get(group.keyword)
                if not group_values:
                    continue
                label = group_values[0].get(group.questions[0].keyword)
                selected_question = 1
                text_question = 2

            value = values.get(group.questions[selected_question].keyword)
            if not value:
                continue

            items.append({
                'label': label,
                'range': range(0, len(group.questions[selected_question].choices)),
                'selected':  list(dict(group.questions[selected_question].choices).keys()).index(value),
                'text': values.get(group.questions[text_question].keyword)
            })
        return {
            "labels": dict(child.questiongroup.questions[0].choices).values(),
            "items2": items
        }
