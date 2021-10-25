import collections

from django.utils.translation import ugettext_lazy as _

from apps.configuration.configuration import QuestionnaireQuestion, \
    QuestionnaireQuestiongroup
from apps.summary.parsers.technologies_2015 import Technology2015Parser


class Technology2018Parser(Technology2015Parser):
    """
    Specific methods for technologies 2018.
    """

    def get_landuse_2018_values(self, child: QuestionnaireQuestion):
        """
        Get selected element with parents and pictos. The given question may
        be a child of several nested questiongroups.

        This is basically a variant of get_picto_and_nested_values.
        """
        try:
            selected = self.get_value(child)[0]['values']
        except (KeyError, IndexError):
            return None

        # get all nested elements in the form '==question|nested'...
        nested_elements_config = child.form_options.get(
            'questiongroup_conditions', []
        )
        # ..and split the strings to a more usable dict. A difference to
        # get_picto_and_nested_values here: There can be multiple values for the
        # same key.
        nested_elements = collections.defaultdict(list)
        for el in self.split_raw_children(*nested_elements_config):
            nested_elements[el[0]].append(el[1])

        default_picto_subquestions = [
            'tech_lu_settlements',
            'tech_lu_waterways',
            'tech_lu_mines',
            'tech_lu_unproductive',
            'tech_lu_other',
        ]

        for value in selected:

            # These subquestions are handled the same as in
            # get_picto_and_nested_values. There is always only one value per
            # key, we need to prepare the data correspondingly.
            if value[3] in default_picto_subquestions:
                nested = {value[3]: nested_elements.get(value[3], [{}])[0]}
                yield self.get_default_picto_values(
                    value_tuple=value,
                    nested_children=nested
                )
            else:
                child_text = f'<strong>{value[0]}</strong>'
                # 'value' is a tuple of four elements: title, icon-url, ?, keyword
                # this represents the 'parent' question with an image
                selected_children_keyword_list = nested_elements.get(value[3], [])

                # selected_children are the 'sub-selections' of given 'value'
                for selected_children_keyword in selected_children_keyword_list:
                    # To keep ordering as defined on the questiongroup, loop over
                    # the children, skipping the ones not filled in.
                    selected_qg = self.config_object.get_questiongroup_by_keyword(
                        selected_children_keyword
                    )

                    child_values_list = self.values.get(selected_children_keyword, [])
                    if not child_values_list:
                        continue

                    children_dict = [
                        self._as_keyword_dict(
                            filter(lambda child: child.keyword in child_values,
                                   selected_qg.children)
                        )
                        for child_values in child_values_list
                    ]

                    # Call the corresponding function.
                    fn = getattr(self, f'get_{value[3]}_picto_values_text')
                    child_text = fn(
                        question_dict=children_dict[0],
                        value_dict_list=child_values_list,
                        render_text=child_text,
                    )

                yield {
                    'url': value[1],
                    'text': child_text,
                }

    def get_tech_lu_cropland_picto_values_text(
            self, question_dict: dict, value_dict_list: list, render_text: str):
        """
        Return the nested subquestions of land use "cropland" (edition 2018).
        """
        value_dict = value_dict_list[0]
        if 'tech_lu_cropland_sub' in question_dict:
            cropland_bullets = []
            choices_labels = dict(
                question_dict['tech_lu_cropland_sub'].choices)
            value_list = value_dict.get('tech_lu_cropland_sub', [])

            # Add subquestions (e.g. which annual crops).
            sub_values_mapping = {
                'lu_cropland_ca': {
                    'keyword': 'tech_lu_cropland_annual_cropping_crops',
                    'other_keyword': 'tech_lu_cropland_annual_cropping_crops_other'
                },
                'lu_cropland_cp': {
                    'keyword': 'tech_lu_cropland_perennial_cropping_crops',
                    'other_keyword': 'tech_lu_cropland_perennial_cropping_crops_other'
                },
                'lu_cropland_ct': {
                    'keyword': 'tech_lu_cropland_tree_shrub_cropping_crops',
                    'other_keyword': 'tech_lu_cropland_tree_shrub_cropping_crops_other'
                },
            }
            for value in value_list:
                cropland_sub_text = f'{choices_labels[value]}'
                mapping = sub_values_mapping.get(value, {})
                if mapping:
                    sub_values = self._get_concatenated_values(
                        question=question_dict.get(mapping['keyword']),
                        values=value_dict.get(mapping['keyword'], []),
                        other_value=value_dict.get(mapping['other_keyword']),
                    )
                    if sub_values:
                        cropland_sub_text += f': {sub_values}'

                # Annual cropping has an additional question
                if value == 'lu_cropland_ca':
                    annual_system = self._get_concatenated_values(
                        question=question_dict.get('tech_lu_cropland_cropping_system'),
                        values=[value_dict.get('tech_lu_cropland_cropping_system')],
                    )
                    if annual_system:
                        cropland_sub_text += f'. {_("Cropping system:")} {annual_system}'

                cropland_bullets.append(cropland_sub_text)

            # Add "other"
            cropland_other = value_dict.get('tech_lu_sub_other')
            if cropland_other:
                cropland_bullets.append(cropland_other)

            cropland_bullets = ''.join(
                [f'<li>{b}</li>' for b in cropland_bullets])
            render_text += f'<br><ul class="bullets">{cropland_bullets}</ul>'

        additional_questions = [
            'tech_growing_seasons',
            'tech_intercropping',
            'tech_crop_rotation',
        ]
        # Don't add a line break for the first line after the <li>.
        linebr = ''
        for i, additional in enumerate(additional_questions):
            val = self._get_concatenated_values(
                question=question_dict.get(additional),
                values=[value_dict.get(additional)],
                add_label=True,
            )
            if val:
                render_text += f'{linebr}{val}'
                linebr = '<br>'

        return render_text

    def get_tech_lu_grazingland_picto_values_text(
            self, question_dict: dict, value_dict_list: list, render_text: str):
        """
        Return the nested subquestions of land use "grazing land" (edition 2018)
        """
        value_dict = value_dict_list[0]
        type_keywords = [
            'tech_lu_grazingland_extensive',
            'tech_lu_grazingland_intensive',
        ]

        bullets = []
        for keyword in type_keywords:
            values = value_dict.get(keyword)
            if not values:
                continue
            choices_labelled = dict(question_dict[keyword].choices)
            for val in values:
                bullets.append(choices_labelled[val])

        # Add "other"
        other = value_dict.get('tech_lu_sub_other')
        if other:
            bullets.append(other)
        bullets = ''.join(
            [f'<li>{b}</li>' for b in bullets])
        render_text += f'<br><ul class="bullets">{bullets}</ul>'

        questions = [
            ('tech_lu_grazingland_animals', 'tech_lu_grazingland_animals_other'),
            ('tech_crop_livestock_management', None),
            ('tech_lu_grazingland_products', 'tech_lu_grazingland_products_other'),
        ]
        line_br = ''
        for kw, kw_other in questions:
            val = self._get_concatenated_values(
                question=question_dict.get(kw),
                values=value_dict.get(kw),
                other_value=value_dict.get(kw_other),
                add_label=True,
            )
            if val:
                render_text += f'{line_br}{val}'
                line_br = '<br>'

        # Species and count, use list values.
        if 'tech_lu_grazingland_pop_species' in value_dict:
            headers = [q.label_view for q in question_dict.values()]
            labels = dict(question_dict['tech_lu_grazingland_pop_species'].choices)
            # rows = []
            rows = ''
            for values in value_dict_list:
                species = labels.get(values.get('tech_lu_grazingland_pop_species'), self.n_a)
                count = values.get('tech_lu_grazingland_pop_count', self.n_a)
                rows += f'<tr><td>{species}</td><td>{count}</td></tr>'
            render_text += f'<table class="technology_table species_table"><tbody><tr><td class="td_category_title"><b>{headers[0]}</b></td><td class="td_category_title"><b>{headers[1]}</b></td></tr>{rows}</tbody></table>'

        return render_text

    def get_tech_lu_forest_picto_values_text(
            self, question_dict: dict, value_dict_list: list, render_text: str):
        """
        Return the nested subquestions of land use "forest" (edition 2018).
        """
        value_dict = value_dict_list[0]
        if 'tech_lu_forest_type' in question_dict:
            forest_bullets = []
            choices_labels = dict(
                question_dict['tech_lu_forest_type'].choices)
            value_list = value_dict.get('tech_lu_forest_type', [])

            # Add subquestions (e.g. management type)
            sub_values_mapping = {
                'lu_forest_natural': {
                    'type_origin': 'tech_lu_forest_natural',
                    'type_origin_label': _('Management: '),
                    'keyword': 'tech_lu_forest_natural_type',
                    'other_keyword': 'tech_lu_forest_natural_type_other'
                },
                'lu_forest_plantation': {
                    'type_origin': 'tech_lu_forest_plantation',
                    'type_origin_label': _('Varieties: '),
                    'keyword': 'tech_lu_forest_plantation_type',
                    'other_keyword': 'tech_lu_forest_plantation_type_other'
                }
            }
            for value in value_list:
                forest_sub_text = f'{choices_labels[value]}'

                mapping = sub_values_mapping.get(value, {})
                if mapping:
                    sub_values = self._get_concatenated_values(
                        question=question_dict.get(mapping['keyword']),
                        values=value_dict.get(mapping['keyword'], []),
                        other_value=value_dict.get(mapping['other_keyword']),
                    )
                    if sub_values:
                        forest_sub_text += f': {sub_values}'

                    # Management type or Type/origin
                    type_origin = self._get_concatenated_values(
                        question=question_dict.get(mapping['type_origin']),
                        values=value_dict.get(mapping['type_origin']),
                    )
                    if type_origin:
                        forest_sub_text += f'. {mapping["type_origin_label"]}' \
                                           f'{type_origin}'

                forest_bullets.append(forest_sub_text)

            # Add "other"
            forest_other = value_dict.get('tech_lu_sub_other')
            if forest_other:
                forest_bullets.append(forest_other)

            forest_bullets = ''.join(
                [f'<li>{b}</li>' for b in forest_bullets])
            render_text += f'<br><ul class="bullets">{forest_bullets}</ul>'

        # Type of trees and decidious/evergreen
        tree_type = self._get_concatenated_values(
            question=question_dict.get('tech_lu_forest_tree_type'),
            values=value_dict.get('tech_lu_forest_tree_type'),
            other_value=value_dict.get('tech_lu_forest_tree_type_other'),
        )
        decidious = self._get_concatenated_values(
            question=question_dict.get('tech_lu_forest_deciduous'),
            values=[value_dict.get('tech_lu_forest_deciduous')],
        )
        line_br = ''
        if tree_type or decidious:
            decidious_text = f' ({decidious})' if decidious else ''
            tree_type_text = tree_type or self.n_a
            render_text += f'{line_br}{_("Tree types")}{decidious_text}: {tree_type_text}'
            line_br = '<br>'

        # Products and services
        products_services = self._get_concatenated_values(
            question=question_dict.get('tech_lu_forest_products'),
            values=value_dict.get('tech_lu_forest_products'),
            other_value=value_dict.get('tech_lu_forest_other'),
            add_label=True,
        )
        if products_services:
            render_text += f'{line_br}{products_services}'
            line_br = '<br>'

        return render_text

    def get_landuse_mixed_values(self, child: QuestionnaireQuestion) -> str:

        selected_values = self._get_qg_selected_value(child, all_values=True)
        if selected_values.get('tech_lu_mixed') is None:
            return ''

        value = self._get_choice_label(child, selected_values['tech_lu_mixed'])
        ret = f'{child.label_view} {value}'
        if selected_values['tech_lu_mixed'] == 1 \
                and 'tech_lu_mixed_select' in selected_values:
            select_child = child.questiongroup.get_question_by_key_keyword(
                'tech_lu_mixed_select')
            select_value = self._get_choice_label(
                select_child, selected_values['tech_lu_mixed_select'])
            ret += f' - {select_value}'

        return ret

    def get_initial_landuse_changed(self, child: QuestionnaireQuestion) -> dict:
        selected = self._get_qg_selected_value(child)
        if selected is not None:
            selected = selected == 'initial_landuse_changed_yes'
        return {
            'label': child.label_view,
            'bool': selected,
        }

    def get_classification_measures(self, child: QuestionnaireQuestion):
        """
        Get selected element with parents and pictos. The given question may
        be a child of several nested questiongroups.

        This is basically a variant of get_picto_and_nested_values.
        """
        try:
            selected = self.get_value(child)[0]['values']
        except (KeyError, IndexError):
            return None

        # get all nested elements in the form '==question|nested'...
        nested_elements_config = child.form_options.get(
            'questiongroup_conditions', []
        )
        # ..and split the strings to a more usable dict. A difference to
        # get_picto_and_nested_values here: There can be multiple values for the
        # same key.
        nested_elements = collections.defaultdict(list)
        for el in self.split_raw_children(*nested_elements_config):
            nested_elements[el[0]].append(el[1])

        default_picto_subquestions = [
            'tech_measures_vegetative',
            'tech_measures_structural',
            'tech_measures_management',
        ]

        for value in selected:
            # These subquestions are handled the same as in
            # get_picto_and_nested_values. There is always only one value per
            # key, we need to prepare the data correspondingly.
            if value[3] in default_picto_subquestions:
                nested = {value[3]: nested_elements.get(value[3], [{}])[0]}
                yield self.get_default_picto_values(
                    value_tuple=value,
                    nested_children=nested
                )
            else:
                child_text = f'<strong>{value[0]}</strong>'
                # 'value' is a tuple of four elements: title, icon-url, ?, keyword
                # this represents the 'parent' question with an image
                selected_children_keyword_list = nested_elements.get(value[3], [])

                # selected_children are the 'sub-selections' of given 'value'
                for selected_children_keyword in selected_children_keyword_list:
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
                        continue

                    if selected_qg:
                        # Agronomic measures
                        if selected_qg.keyword == 'tech_qg_21':
                            child_text = self.get_agronomic_measures_picto_values(
                                questiongroup=selected_qg,
                                values=child_values,
                                render_text=child_text,
                            )

                        # Other: Add text
                        elif selected_qg.keyword == 'tech_qg_25':
                            other = child_values.get('tech_measures_other')
                            if other:
                                child_text = f'{child_text} - {other}'

                yield {
                    'url': value[1],
                    'text': child_text,
                }

    def get_agronomic_measures_picto_values(
            self, questiongroup: QuestionnaireQuestiongroup, values: dict,
            render_text: str):
        """
        Return a comma-separated list of values. If there is a sub-question, add
        it in brackets right after the corresponding value.
        """
        render_list = []

        main_question = questiongroup.get_question_by_key_keyword(
            'tech_measures_agronomic_sub')
        main_value_labels = dict(main_question.choices)

        sub_question_mapping = {
            'measures_agronomic_a3': 'tech_agronomic_tillage',
            'measures_agronomic_a6_residue_management': 'tech_residue_management',
        }

        for main_value in values.get('tech_measures_agronomic_sub', []):
            rendered_value = main_value_labels[main_value]
            if main_value in sub_question_mapping.keys():
                sub_keyword = sub_question_mapping[main_value]
                sub_question = questiongroup.get_question_by_key_keyword(
                    sub_keyword)
                sub_value = self._get_choice_label(
                    sub_question, values.get(sub_keyword))
                if sub_value:
                    rendered_value += f' ({sub_value})'
            render_list.append(rendered_value)
        return render_text + ' - ' + ', '.join(render_list)

    def _get_concatenated_values(
            self, question: QuestionnaireQuestion, values: list,
            other_value: str=None, add_label: bool=None) -> str:

        ret = ''
        if not question:
            return ret

        if add_label is True:
            label = question.label_view
            suffix = '' if label[-1] in ['.', ':', '?'] else ':'
            ret += f'{label}{suffix} '

        labels = dict(question.choices)
        if not isinstance(values, list):
            values = [values]
        ret += ', '.join([labels[v] for v in values])

        if other_value:
            ret += f', {other_value}'

        return ret

    def _as_keyword_dict(self, question_list: collections.Iterator) -> dict:
        return {el.keyword: el for el in question_list}
