from .base import Edition, Operation


class Sample(Edition):
    """
    Sample questionnaire update for testing.
    """
    code = 'sample'
    edition = 2018

    @property
    def operations(self):
        return [
            Operation(
                transform_configuration=self.remove_qg_2_key_2,
                transform_questionnaire=self.delete_qg_2_key_2,
                release_note='cat_1: Removed "key_2" of questiongroup "qg_2", leaving "key_3" as only key in this questiongroup.'
            ),
            Operation(
                transform_configuration=self.remove_qg_5,
                transform_questionnaire=self.delete_qg_5,
                release_note='cat_3: Removed questiongroup "qg_5" which contained "key_7".'
            ),
            Operation(
                transform_configuration=self.add_key_68_to_qg_12,
                release_note='cat_4: Added key "key_68" to questiongroup "qg_12".'
            ),
            Operation(
                transform_configuration=self.rename_qg_1_key_1,
                release_note='cat_1: Renamed "key_1" of questiongroup "qg_1" (previously "Key 1", now "Key 1 (edition 2018)".'
            )
        ]

    def rename_qg_1_key_1(self, **data) -> dict:
        self.update_translation(
            update_pk=11001,
            **{
                'label': {
                    'en': 'Key 1 (edition 2018)',
                    'es': 'Clave 1 (edicion 2018)'
                }
            }
        )
        return data

    def add_key_68_to_qg_12(self, **data) -> dict:
        qg_path = ('section_2', 'cat_4', 'subcat_4_1', 'qg_12')
        qg_data = self.find_in_data(path=qg_path, **data)
        self.create_new_question(
            keyword='key_68',
            translation={
                'label': {
                    'en': 'Key 68',
                    'es': 'Clave 68'
                }
            },
            question_type='char'
        )
        qg_data['questions'] = qg_data['questions'] + [{
            'keyword': 'key_68'
        }]
        return self.update_config_data(path=qg_path, updated=qg_data, **data)

    def remove_qg_5(self, **data) -> dict:
        subcat_path = ('section_1', 'cat_3', 'subcat_3_1')
        subcat_data = self.find_in_data(path=subcat_path, **data)
        subcat_data['questiongroups'] = [
            qg for qg in subcat_data['questiongroups']
            if qg['keyword'] != 'qg_5']
        return self.update_config_data(
            path=subcat_path, updated=subcat_data, **data)

    def delete_qg_5(self, **data) -> dict:
        if 'qg_5' in data:
            del data['qg_5']
        return data

    def remove_qg_2_key_2(self, **data) -> dict:
        qg_path = ('section_1', 'cat_1', 'subcat_1_1', 'qg_2')
        qg_data = self.find_in_data(path=qg_path, **data)
        qg_data['questions'] = [
            q for q in qg_data['questions'] if q['keyword'] != 'key_2']
        return self.update_config_data(path=qg_path, updated=qg_data, **data)

    def delete_qg_2_key_2(self, **data) -> dict:
        return self.update_data(
            qg_keyword='qg_2', q_keyword='key_2', updated=None, **data)
