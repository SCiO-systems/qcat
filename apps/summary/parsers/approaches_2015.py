from apps.configuration.models import Value
from django.utils.translation import ugettext_lazy as _

from apps.configuration.configuration import QuestionnaireQuestion
from apps.summary.parsers.questionnaire import QuestionnaireParser


class Approach2015Parser(QuestionnaireParser):
    """
    Specific methods for approaches 2015.
    """

    def get_aims_enabling(self, child: QuestionnaireQuestion, name: str):
        """
        Get enabling/hindering values only.
        """
        field_name = 'app_condition_{}_specify'.format(name)
        for group in child.questiongroup.parent_object.questiongroups:
            try:
                text = self.values[group.keyword][0][field_name]
            except (KeyError, IndexError):
                continue

            yield group.label, text

    def get_stakeholders_roles(self, child: QuestionnaireQuestion):
        groups = child.questiongroup.parent_object.questiongroups
        # the first element in the group contains the labels of the selected
        # questiongroups, so get the values.
        label_values = self.values.get(groups[0].keyword)
        if not label_values:
            return
        labels = label_values[0].get('app_stakeholders')

        # use only groups that are selected (i.e. in the labels-list)
        selected_group_keywords = [
            group.keyword for group in groups
            if group.view_options.get('conditional_question') in labels
        ]
        first_children = self.config_object.get_questiongroup_by_keyword(
            selected_group_keywords[0]
        ).children
        # Get the headers first.
        yield from self._get_stakeholder_row(
            label=groups[0].children[0].label,
            app_stakeholders_roles=first_children[1].label,
            app_stakeholders_comments=first_children[0].label
        )

        for index, group_keyword in enumerate(selected_group_keywords):
            # Always display translated label ('NGO', 'local land users')
            label = Value.objects.get(keyword=labels[index]).get_translation(
                keyword='label', configuration='approaches'
            )
            # If additional info is specified (role, specify), append this.
            values = self.values[group_keyword][0] if group_keyword in self.values else {}

            yield from self._get_stakeholder_row(label=label, **values)

        # Also include 'other' stakeholders
        other_group = next(group for group in groups if group.children[0].keyword == 'app_stakeholders_other')
        other = self.values.get(other_group.keyword, [])
        if other and len(other) == 1 and 'app_stakeholders_other' in other[0]:
            values = other[0]
            yield from self._get_stakeholder_row(
                label=values[other_group.children[0].keyword], **values
            )

    def _get_stakeholder_row(self, label: str, **kwargs):
        roles = kwargs.get('app_stakeholders_roles')
        comments = kwargs.get('app_stakeholders_comments')
        yield label, comments or '', roles or ''

    def get_involvement(self, child: QuestionnaireQuestion):
        for qg in child.questiongroup.parent_object.questiongroups:
            try:
                comment = self.values[qg.keyword][0]['app_involvement_who']
            except (KeyError, IndexError):
                comment = ''

            yield {
                'title': qg.label,
                'comment': comment,
                'items': self.get_full_range_values(qg.questions[0])
            }

    def get_highlight_element(self, child: QuestionnaireQuestion):
        return {
            'highlighted': bool(self._get_qg_selected_value(child) == 1),
            'text': child.questiongroup.parent_object.label
        }

    def get_highlight_element_with_text(self, child: QuestionnaireQuestion):
        """
        Really specific method for question 4.3.
        """
        selected = self._get_qg_selected_value(child)
        return {
            'value': self.get_full_range_values(child),
            'bool': {
                'highlighted': selected and selected != 'app_institutions_no',
                'text': child.questiongroup.parent_object.label
            }
        }

    def get_financing_subsidies(self, child: QuestionnaireQuestion):
        """
        Get the 'selected' questiongroups from the questiongroups condition
        and build a scale with vertical label from it.
        Also, the 'is_subsidised' info for the first element in the financing
        part is gathered.
        The structure is very nested and complex, but follows the config.
        """
        none_selected = 'app_subsidies_inputs_none'
        other_question = 'app_subsidies_inputs_other'
        selected_groups = self._get_qg_selected_value(child) or []
        nested_elements_config = child.form_options.get('questiongroup_conditions') or []
        # A dict with the mapping of questiongroup-name and identifier.
        nested_elements = dict(self.split_raw_children(*nested_elements_config))
        labels = dict(child.choices)
        items = []

        # Prepare 'other' questiongroup if filled in (usually the last question)
        for questiongroup in reversed(child.questiongroup.parent_object.questiongroups):
            if other_question in [question.keyword for question in questiongroup.questions]:
                if self.values.get(questiongroup.keyword):
                    selected_groups.append(questiongroup.keyword)
                    nested_elements[questiongroup.keyword] = questiongroup.keyword
                    labels[questiongroup.keyword] = self.values[questiongroup.keyword][0].get(
                        other_question, ''
                    )
                break

        for group in selected_groups:
            # Skip the group for 'none'
            if group == none_selected:
                continue

            qg = self.config_object.get_questiongroup_by_keyword(
                nested_elements[group]
            )
            label = labels[group]
            columns = qg.form_options.get('table_columns', 3)
            try:
                row = self.get_subsidies_row(qg, **self.values[qg.keyword][0])
            except (KeyError, IndexError):
                continue

            # if there are only two columns, there is no additional label.
            if columns == 2:
                items.append(row.make_row(label, 0, 1))
            else:
                # split questions into rows according to defined columns.
                index = 0
                while index + columns <= len(qg.questions):
                    if qg.questions[index + 1].keyword in row.values:
                        # 'other' / custom labels: label text is set as value.
                        if qg.questions[index].keyword.endswith('other'):
                            label = row.values.get(qg.questions[index].keyword, '')
                        else:
                            label = f'{label}: {qg.questions[index].choices[0][1]}'

                        items.append(
                            row.make_row(
                                label=label,
                                selected=index + 1,
                                text=index + 2
                            )
                        )
                    index += columns

        return {
            "is_subsidised": {
                "highlighted": selected_groups and none_selected not in selected_groups,
                "text": _("Subsidies for specific inputs")
            },
            "subsidies": {
                "title": child.questiongroup.parent_object.label,
                "items": items
            }
        }

    def get_subsidies_row(self, questiongroup, **values):

        class SubsidiesRow:

            def __init__(self, questiongroup, **values):
                self.qg = questiongroup
                self.values = values
                self.labels = None

            def make_row(self, label, selected, text):
                self.labels = dict(self.qg.questions[selected].choices)
                selected = values.get(self.qg.questions[selected].keyword)
                return {
                    'label': label,
                    'range': range(0, len(self.labels)),
                    'selected': list(self.labels.keys()).index(selected) if selected else '',
                    'text': values.get(self.qg.questions[text].keyword) or '',
                    'scale': self.labels.values()
                }

        return SubsidiesRow(questiongroup, **values)

    def get_impacts_motivation(self, child: QuestionnaireQuestion):
        selected_values = self.values.get(child.questiongroup.keyword)
        if not selected_values:
            return
        selected = selected_values[0].get(child.keyword)
        for keyword, label in dict(child.choices).items():
            yield {
                'highlighted': keyword in selected,
                'text': label
            }

    def get_impacts(self, child: QuestionnaireQuestion):

        for qg in child.questiongroup.parent_object.questiongroups:
            selected = self._get_qg_selected_value(qg.questions[0])
            if not selected:
                continue

            # no choices = this is an 'other' input
            if not qg.questions[0].choices:
                label = selected
                selected = self._get_qg_selected_value(qg.questions[1])
                select = 1
                text = 2
            else:
                # this works for english only. discussed and okey-d.
                label = qg.questions[0].label
                select = 0
                text = 1

            yield {
                'label': label,
                'range': range(0, len(qg.questions[select].choices)),
                'selected': selected - 1 if selected else None,
                'text': self._get_qg_selected_value(qg.questions[text]) or '',
                'scale': dict(qg.questions[select].choices).values()
            }
