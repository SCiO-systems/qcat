from apps.configuration.cache import get_configuration
from apps.configuration.configuration import QuestionnaireQuestion
from apps.configuration.models import Configuration


class ConfigurationStructure:
    """
    Create a representation of the configuration structure.
    """

    def __init__(self, code: str, edition: str, flat: bool=False):
        self.structure = []
        self.error = None

        try:
            configuration = get_configuration(code=code, edition=edition)
        except Configuration.DoesNotExist:
            self.error = 'No configuration found for this code and edition.'
            return

        for section in configuration.sections:
            for category in section.categories:

                if flat:
                    self.build_flat_structure(category)
                else:
                    self.structure.append(self.get_nested_structure(category))

    def get_nested_structure(
            self, configuration_obj, structure: dict=None) -> dict:
        if structure is None:
            structure = {}

        current_obj_level = configuration_obj.name_current
        structure_function = self.get_structure_function(current_obj_level)
        structure.update(structure_function(configuration_obj))

        if current_obj_level != 'questions':
            children_structures = []
            for child in configuration_obj.children:
                children_structures.append(self.get_nested_structure(child, {}))
            structure[
                f'{configuration_obj.name_children}'] = children_structures

        return structure

    def build_flat_structure(
            self, configuration_obj, structure: dict=None) -> None:
        if structure is None:
            structure = {}

        current_obj_level = configuration_obj.name_current
        structure_function = self.get_structure_function(current_obj_level)
        structure.update(structure_function(configuration_obj))

        if isinstance(configuration_obj, QuestionnaireQuestion):
            self.structure.append(structure)
            return

        for child in configuration_obj.children:
            self.build_flat_structure(child, structure)

    def get_structure_function(self, current_obj_level: str):
        return getattr(
            self,
            f'get_{current_obj_level}_structure',
            self.get_basic_structure_values
        )

    def get_questions_structure(self, configuration_obj) -> dict:
        choices = [
            [c[0], str(c[1])] for c in configuration_obj.choices]
        return {
            'questions_label': self.get_label(configuration_obj),
            'questions_keyword': configuration_obj.keyword,
            'questions_type': configuration_obj.field_type,
            'questions_choices': choices,
            'conditions': self.get_conditions(configuration_obj.form_options),
            **self.get_basic_structure_values(configuration_obj),
        }

    def get_questiongroups_structure(self, configuration_obj) -> dict:
        return {
            'questiongroups_repeating': configuration_obj.form_options.get(
                'max_num'),
            'conditions': self.get_conditions(configuration_obj.form_options),
            **self.get_basic_structure_values(configuration_obj),
        }

    def get_basic_structure_values(self, configuration_obj) -> dict:
        current_obj_name = configuration_obj.name_current
        return {
            f'{current_obj_name}_label': self.get_label(configuration_obj),
            f'{current_obj_name}_keyword': configuration_obj.keyword,
        }

    @staticmethod
    def get_label(configuration_obj) -> str:
        numbering = configuration_obj.form_options.get('numbering', '')
        label = configuration_obj.label or ''
        return f'{numbering} {label}'.strip()

    @staticmethod
    def get_conditions(form_options):
        # Remap the conditions as they are defined in the configuration JSON to
        # make them more understandable in the output/API.
        conditions_remapped = [
            # ('as_in_configuration', 'new_key_in_output'),
            ('questiongroup_conditions', 'questiongroup_triggers'),
            ('question_conditions', 'question_triggers'),
            ('question_condition', 'trigger_keyword'),
            ('questiongroup_condition', 'trigger_keyword'),
        ]
        conditions = {}
        for configuration_keyword, output_keyword in conditions_remapped:
            if configuration_keyword in form_options:
                conditions[output_keyword] = form_options[configuration_keyword]
        return conditions
