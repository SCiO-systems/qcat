import collections
import contextlib
import itertools

from django.utils.translation import ugettext_lazy as _, pgettext

from apps.configuration.configuration import QuestionnaireQuestion, \
    QuestionnaireQuestiongroup
from apps.summary.parsers.questionnaire import QuestionnaireParser


class Technology2015Parser(QuestionnaireParser):
    """
    Specific methods for technologies 2015.
    """

    def get_human_env_access(self, child: QuestionnaireQuestion):
        # e.g. 5.9 - get all info from parent questiongroup
        # combine children from questiongroup with 'other'
        children = itertools.chain(
            *[qg.children for qg in child.questiongroup.parent_object.questiongroups]
        )
        for child in children:
            try:
                value = int(self._get_qg_selected_value(child))
            except (ValueError, TypeError):
                continue

            if not child.keyword.startswith('tech_access_other_'):
                # defined fields
                yield from self._qg_scale_format(
                    child=child,
                    value=value,
                    label_left=child.choices[0][1],
                    label_right=child.choices[-1][1]
                )
            elif child.keyword == 'tech_access_other_measure':
                # 'other'
                yield from self._qg_scale_format(
                    child=child,
                    label=self._get_qg_selected_value(
                        child, all_values=True
                    ).get('tech_access_other_specify'),
                    value=value,
                    label_left=child.choices[0][1],
                    label_right=child.choices[-1][1]
                )

    def get_tech_costbenefit(self, child: QuestionnaireQuestion):
        # e.g. 6.4. - all info from radio buttons
        values = self._get_qg_selected_value(child, all_values=True)

        for child in child.questiongroup.children:
            str_value = values.get(child.keyword, '')
            # in the template, the numeric position of the value in the
            # 'range' is required.
            try:
                choice_keys = dict(child.choices).keys()
                value = list(choice_keys).index(str_value) + 1
            except ValueError:
                continue

            yield from self._qg_scale_format(
                child=child,
                value=value,
                label_left=child.choices[0][1],
                label_right=child.choices[-1][1]
            )

    def get_impact(self, child: QuestionnaireQuestion, has_siblings: False):
        """
        The last block (off-site impacts) has no siblings, all other blocks
        have nested questiongroups.
        Also, as 'other' may be repeating, 'other_spefify' is in a loop as well.
        Sorry!
        """
        if has_siblings:
            categories = child.questiongroup.parent_object.parent_object.subcategories
            questiongroups = itertools.chain(
                *[category.questiongroups for category in categories]
            )
        else:
            questiongroups = child.questiongroup.parent_object.questiongroups

        for group in questiongroups:
            if len(group.children) < 3:
                # omit 'tech_specify'
                continue
            if group.children[0].keyword == 'tech_impacts_other_specify':
                for items in self.values.get(group.keyword, []):
                    value_child = 2
                    label = items.get(group.children[0].keyword)
                    value = items.get(group.children[value_child].keyword)
                    label_left = items.get(group.children[1].keyword)
                    label_right = items.get(group.children[3].keyword)
                    before_label = _(group.children[4].label)
                    before_value = items.get(group.children[4].keyword)
                    after_label = _(group.children[5].label)
                    after_value = items.get(group.children[5].keyword)
                    comment_value = items.get(group.children[6].keyword)
                    yield from self._get_impact_row(
                        child=group.children[value_child], label=label,
                        value=value, label_left=label_left,
                        label_right=label_right, before_value=before_value,
                        before_label=before_label, after_value=after_value,
                        after_label=after_label, comment_value=comment_value
                    )
            else:
                value_child = 0
                label = group.children[value_child].label
                value = self._get_qg_selected_value(group.children[value_child])
                label_left = group.children[0].additional_translations.get('label_left')
                label_right = group.children[0].additional_translations.get('label_right')
                before_label = _(group.children[1].label)
                before_value = self._get_qg_selected_value(group.children[1])
                after_label = _(group.children[2].label)
                after_value = self._get_qg_selected_value(group.children[2])
                comment_value = self._get_qg_selected_value(group.children[3])
                yield from self._get_impact_row(
                    child=group.children[value_child], label=label,
                    value=value, label_left=label_left, label_right=label_right,
                    before_value=before_value, before_label=before_label,
                    after_value=after_value, after_label=after_label,
                    comment_value=comment_value,
                )

    def _get_impact_row(self, child: QuestionnaireQuestion, label: str,
                        value: int, label_left: str, label_right: str,
                        before_value: str, before_label: str, after_value: str,
                        after_label: str, comment_value: str):
        if value and isinstance(value, int):
            comment = ''
            if before_value or after_value:
                comment = f'{before_label}: {before_value}\n{after_label}: {after_value}'

            # if a comment is set, add it
            if comment_value:
                comment += '\n' + (comment_value or '')

            yield from self._qg_scale_format(
                child=child,
                value=value,
                label=label,
                label_left=label_left,
                label_right=label_right,
                comment=comment
            )

    def get_climate_change(self, child: QuestionnaireQuestion):
        # based on this first question, get all questiongroups with at least
        # one filled in question.
        climate_change_categories = child.questiongroup.parent_object. \
            parent_object.parent_object
        groups = []

        for main_category in filter(self._subcategory_has_value,
                                    climate_change_categories.subcategories):

            # A store for all 'lines' for the main groups
            items = []
            questiongroups = [subcategory.questiongroups for subcategory in
                              main_category.subcategories]
            for group in itertools.chain(*questiongroups):

                values = self.values.get(group.keyword, [])
                # if more than one element is available, a set of 'sibling'
                # questions was filled in. Duplicate this question, resulting
                # in one line per value/answer.
                for value in values:
                    items.append(self._prepare_climate_change_row(group, **value))

            groups.append({
                'title': main_category.label,
                'items': items
            })

        return groups

    def _prepare_climate_change_row(self, group: QuestionnaireQuestiongroup, **values):
        """
        Create elements for a single line. The structure of questions varies
        between all elements, regarding number of questions and content/scale of
        questions.
        """
        label = group.label
        comment = ''

        # One set of questions equals one line in the summary. The field names
        # are stable/repeating so string comparison is nasty but semi-ok.
        for question in group.questions:

            if question.keyword == 'tech_exposure_incrdecr':
                # Indicator for direction of development (increased/decreased)
                question_label = values.get(question.keyword)
                if question_label:
                    # context is important here; a label may be named differently according to
                    # configuration,
                    translated = pgettext(f'{self.config_object.keyword} label', question_label)
                    label = f'{label} {translated}'

            elif question.keyword == 'tech_exposure_sensitivity':
                # The actual value for our range-field.
                # The first and the last choice are irrelevant to this
                # mode of layout. If the selected value is empty or unknown,
                # this is added as comment.
                choice_keys = list(
                    collections.OrderedDict(question.choices).keys()
                )
                with contextlib.suppress(ValueError):
                    choice_keys.remove('')
                    choice_keys.remove('cope_unknown')

                value = values.get(question.keyword)
                if value not in choice_keys:
                    string_value = dict(question.choices).get(value)
                    if string_value:
                        comment += _(' Answer: {}').format(string_value)
                else:
                    value = choice_keys.index(value)

            elif 'other' in question.keyword:
                label = values.get(question.keyword, '')

            else:
                # All other fields, such as 'season' go into the comments.
                comment_key = values.get(question.keyword)
                if not group.label.startswith('other'):
                    comment_key = dict(question.choices).get(comment_key)
                if comment_key:
                    comment += '{label}: {value}'.format(
                        label=question.label,
                        value=comment_key
                    )

        return {
            'label': label,
            'range': range(0, len(choice_keys)),
            'min': question.choices[1][1],
            'max': question.choices[-2][1],
            'selected': value,
            'comment': comment
        }

    def _subcategory_has_value(self, subcategory):
        """
        Filter only questiongroups with at least one filled in question.
        """
        questiongroups = itertools.chain(
            *[subcategory.questiongroups for subcategory in subcategory.subcategories]
        )
        qg_keywords = [qg.keyword for qg in questiongroups]
        return not set(qg_keywords).isdisjoint(set(self.values.keys()))
