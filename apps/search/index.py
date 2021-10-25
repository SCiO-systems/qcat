import elasticsearch
from django.conf import settings
from elasticsearch.helpers import reindex, bulk

from apps.configuration.configuration import QuestionnaireConfiguration
from apps.questionnaire.models import Questionnaire
from apps.questionnaire.serializers import QuestionnaireSerializer
from .utils import get_analyzer, get_alias, force_strings, ElasticsearchAlias


def get_elasticsearch():
    """
    Return an instance of the elastic search with the connection as
    specified in the settings (``ES_HOST`` and ``ES_PORT``).

    Returns:
        ``elasticsearch.Elasticsearch``.
    """
    return elasticsearch.Elasticsearch(
        [{'host': settings.ES_HOST, 'port': settings.ES_PORT}])


es = get_elasticsearch()


def get_mappings():
    """
    Return the mappings of the questiongroups of a Questionnaire. This
    is used to identify the types of fields, making it possible to query
    them properly.

    String values are objects themselves with a key for each language
    available.

    Args:
        ``questionnaire_configuration`` (
        :class:`configuration.configuration.QuestionnaireConfiguration`)

    Returns:
        ``dict``. A dict containing the mappings of a questionnaire
        fields.
    """
    language_codes = [l[0] for l in settings.LANGUAGES]

    name_properties = {}
    for language_code in language_codes:
        q = {'type': 'text'}
        analyzer = get_analyzer(language_code)
        if analyzer:
            q.update({'analyzer': analyzer})
            name_properties[language_code] = q

    multilanguage_string_properties = {}
    for language_code in language_codes:
        multilanguage_string_properties[language_code] = {
            'type': 'text'
        }
    link_structure = {
        'code': {
            'type': 'text',
        },
        'configuration': {
            'type': 'text',
        },
        'name': {
            'properties': multilanguage_string_properties,
        },
        'url': {
            'properties': multilanguage_string_properties,
        }
    }

    mappings = {
        'questionnaire': {
            'properties': {
                'created': {
                    'type': 'date'
                },
                'updated': {
                    'type': 'date'
                },
                'translations': {
                    'type': 'text'
                },
                'configurations': {
                    'type': 'text'
                },
                'code': {
                    'type': 'text'
                },
                'name': {
                    'properties': name_properties
                },
                'compilers': {
                    'type': 'nested',
                    'properties': {
                        'id': {
                            'type': 'integer',
                        },
                        'name': {
                            'type': 'text',
                        },
                    }
                },
                'editors': {
                    'type': 'nested',
                    'properties': {
                        'id': {
                            'type': 'integer',
                        },
                        'name': {
                            'type': 'text',
                        },
                    }
                },
                'reviewers': {
                    'type': 'nested',
                    'properties': {
                        'id': {
                            'type': 'integer',
                        },
                        'name': {
                            'type': 'text',
                        },
                    }
                },
                'links': {
                    'type': 'nested',
                    'properties': link_structure,
                },
                'flags': {
                    'type': 'nested',
                    'properties': {
                        'flag': {
                            'type': 'text',
                        },
                        'name': {
                            'type': 'text',
                        },
                    }
                },
                # The rest of 'list_data' is added dynamically, but 'country'
                # needs to be present because of the default sort order.
                # Otherwise, questionnaires which do not have a 'country'
                # question (e.g. CCA) would throw an error.
                'list_data': {
                    'properties': {
                        'country': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'type': 'keyword',
                                    'ignore_above': 256,
                                }
                            }
                        }
                    }
                }
                # 'filter_data' is added dynamically (automatic mapping)
            }
        }
    }

    return mappings


def create_or_update_index(configuration: QuestionnaireConfiguration, mappings: dict) -> tuple:
    """
    Create or update an index for a configuration.

    New indices are created with an alias pointing to it. The alias is
    composed of the prefix as specified in the settings
    (``ES_INDEX_PREFIX``) followed by the ``configuration_code`` as
    provided.

    .. seealso::
        :func:`search.utils.get_alias`

    Updates of indices happen by creating a new index, replacing link of
    the alias and deleting the old index.

    .. seealso::
        https://www.elastic.co/blog/changing-mapping-with-zero-downtime

    Args:
        ``configuration_code`` (str): The code of the configuration.

        ``mappings`` (dict): A dictionary containing the mapping of the
        fields of the Questionnaire.

        .. seealso::
            :func:`get_mappings`

    Returns:
        ``bool``. A boolean indicating whether the creation/update of
        the index was successful or not.

        ``list``. A list of strings containing the logs of the actions
        performed.

        ``str``. An optional error message.
    """
    logs = []
    body = {
        'mappings': mappings,
        'settings': {
            'index': {
                'mapping': {
                    'nested_fields': {
                        'limit': settings.ES_NESTED_FIELDS_LIMIT,
                    },
                    'total_fields': {
                        'limit': 6000
                    }
                }
            }
        }
    }

    # Check if there is already an alias pointing to the index.
    alias = get_alias(ElasticsearchAlias.from_configuration(configuration=configuration))
    alias_exists = es.indices.exists_alias(name=alias)

    if alias_exists is not True:
        # If there is no alias yet, create an index and an alias
        # pointing to it.
        logs.append(
            'Alias "{}" does not exist, an index is being created'.format(
                alias))
        index = '{}_1'.format(alias)
        index_created = es.indices.create(index=index, body=body)
        if index_created.get('acknowledged') is not True:
            return False, logs, 'Index could not be created: {}'.format(
                index_created)
        logs.append('Index "{}" was created'.format(index))
        try:
            alias_created = es.indices.put_alias(index=index, name=alias)
            if alias_created.get('acknowledged') is not True:
                return False, logs, 'Alias could not be created: {}'.format(
                    alias_created)
        except elasticsearch.RequestError:
            pass
        logs.append('Alias "{}" was created'.format(alias))
    else:
        logs.append('Alias "{}" found'.format(alias))
        old_index, new_index = get_current_and_next_index(alias)
        index_created = es.indices.create(index=new_index, body=body)
        if index_created.get('acknowledged') is not True:
            return (False, logs,
                    'Updated Index could not be created: "{}"'.format(
                        index_created))
        logs.append('Index "{}" was created'.format(new_index))
        data_transfer, data_error = reindex(es, old_index, new_index)
        logs.append('Data transferred: "{}", data error: "{}"'.format(
            data_transfer, data_error))
        es.indices.refresh(index=new_index)
        logs.append('Index "{}" was refreshed'.format(new_index))
        alias_created = es.indices.put_alias(index=new_index, name=alias)
        if alias_created.get('acknowledged') is not True:
            return (
                False, logs, 'Updated Alias could not be created: {}'.format(
                    alias_created))
        logs.append('Alias to "{}" was created'.format(new_index))
        alias_deleted = es.indices.delete_alias(index=old_index, name=alias)
        if alias_deleted.get('acknowledged') is not True:
            return False, logs, 'Old Alias could not be deleted: {}'.format(
                alias_deleted)
        logs.append('Alias to "{}" was deleted'.format(old_index))
        index_deleted = es.indices.delete(index=old_index)
        if index_deleted.get('acknowledged') is not True:
            return False, logs, 'Old Index could not be deleted: {}'.format(
                index_deleted)
        logs.append('Index "{}" was deleted'.format(old_index))

    return True, logs, ''


def put_questionnaire_data(questionnaire_objects, **kwargs):
    """
    Add a list of documents to the index. New documents will be created,
    existing documents will be updated.

    Args:
        ``configuration_code`` (str): The code of the Questionnaire
        configuration corresponding to the data.

        ``questionnaire_objects`` (list): A list (queryset) of
        :class:`questionnaire.models.Questionnaire` objects.

    Returns:
        ``int``. Count of objects created or updated.

        ``list``. A list of errors occurred.
    """
    refresh_aliases = set()

    actions = []
    for obj in questionnaire_objects:

        alias = get_alias(
            ElasticsearchAlias.from_configuration(configuration=obj.configuration_object)
        )
        refresh_aliases.add(alias)

        serialized = QuestionnaireSerializer(instance=obj).data

        # The serializer calls a method (get_list_data) on the configuration
        # object, which returns values that are prepared to be presented on the
        # frontend and include lazy translation objects. Cast them to strings.
        serialized['list_data'] = force_strings(serialized['list_data'])

        # The country field is used as default order of the list and needs to be
        # set in the ES data. Set it manually if not available.
        if 'country' not in serialized['list_data']:
            serialized['list_data']['country'] = None

        # Collect the filter values as specified in the configuration
        # Global filter keys first
        filter_paths = [
            (f'{qg}__{key}', key, qg)
            for qg, key in settings.QUESTIONNAIRE_GLOBAL_FILTER_PATHS]
        # Extend with specific filter keys for this configuration.
        filter_paths.extend([
            (filter_key.path, filter_key.key, filter_key.questiongroup)
            for filter_key in obj.configuration_object.get_filter_keys()])

        filter_data = {}
        for path, key, questiongroup in filter_paths:
            q_data = [
                qg_data.get(key) for qg_data in obj.data.get(questiongroup, [])]
            # Remove None values and add only if not empty.
            q_data = [v for v in q_data if v is not None]
            if q_data:
                filter_data[path] = q_data
        serialized['filter_data'] = filter_data

        # Add ordered values to document data
        for ordered_filter in get_ordered_filter_values(obj.configuration_object):
            ordered_qg_data = serialized.get(
                'data', {}).get(ordered_filter[0], [])

            for ordered_data in ordered_qg_data:
                values = ordered_data.get(ordered_filter[1], [])
                values_order = [
                    o[0] for o in ordered_filter[2] if o[1] in values]
                ordered_data[f'{ordered_filter[1]}_order'] = values_order

        action = {
            '_index': alias,
            '_type': 'questionnaire',
            '_id': obj.id,
            '_source': serialized,
        }
        actions.append(action)

    actions_executed, errors = bulk(es, actions, **kwargs)

    es.indices.refresh(index=','.join(refresh_aliases))
    return actions_executed, errors


def get_ordered_filter_values(configuration: QuestionnaireConfiguration) -> list:
    """
    Get a list of all (checkbox) values which are ordered. This (may) be used for filters (?).
    """
    ordered_filter_values = []
    for filter_key in configuration.get_filter_keys():
        if filter_key.filter_type not in [
                'checkbox', 'image_checkbox', 'select_type', 'select_model',
                'radio', 'bool']:
            continue

        filter_question = configuration.get_question_by_keyword(
            filter_key.questiongroup, filter_key.key)
        if filter_question is None:
            continue

        values = [(v.order_value, v.keyword) for v in
                  filter_question.value_objects]
        ordered_values = sorted(values, key=lambda v: v[0])

        ordered_filter_values.append((filter_key.questiongroup, filter_key.key, ordered_values))

    return ordered_filter_values


def put_all_data():
    """
    Put data from all configurations to the es index.
    """
    put_questionnaire_data(
        questionnaire_objects=Questionnaire.with_status.public(),
        request_timeout=60
    )


def delete_questionnaires_from_es(questionnaire_objects):
    """
    Remove specific Questionnaires from the index.

    Args:
        ``questionnaire_objects`` (list): A list (queryset) of
        :class:`questionnaire.models.Questionnaire` objects to be
        removed.
    """

    for questionnaire in questionnaire_objects:
        alias = get_alias(
            ElasticsearchAlias.from_configuration(configuration=questionnaire.configuration_object)
        )
        try:
            es.delete(
                index=alias, doc_type='questionnaire', id=questionnaire.id)
        except:
            pass


def delete_all_indices(prefix=settings.ES_INDEX_PREFIX):
    """
    Delete all the indices starting with the prefix as specified in the
    settings (``ES_INDEX_PREFIX``).

    Returns:
        ``bool``. A boolean indicating whether the operation was carried
        out successfully or not.

        ``str``. An optional error message if the operation was not
        successful.
    """
    deleted = es.indices.delete(index=f'{prefix}*')
    if deleted.get('acknowledged') is not True:
        return False, 'Indices could not be deleted'

    return True, ''


def delete_single_index(index):
    """
    Delete a specific index.

    Args:
        ``ìndex`` (str): The name of the index to be deleted.

    Returns:
        ``bool``. A boolean indicating whether the operation was carried
        out successfully or not.

        ``str``. An optional error message if the operation was not
        successful.
    """
    deleted = es.indices.delete(index=index, ignore=[404])
    if deleted.get('acknowledged') is not True:
        return False, 'Index could not be deleted'

    return True, ''


def get_current_and_next_index(alias):
    """
    Get the current and next index of an alias. Both the currently
    linked index and the next index to be used (by increasing the
    suffix) are returned.

    Returns:
        ``str``. The name of the index currently linked by the alias.

        ``str``. The name of the next index to be used by the alias.
    """
    if es.indices.exists_alias(name=alias) is not True:
        return None, None
    aliased_index = es.indices.get_alias(name=alias)
    found_index = next(iter(aliased_index.keys()))
    found_version = found_index.split('{}_'.format(alias))
    try:
        found_version = int(found_version[1])
    except:
        found_version = 1
    next_index = '{}_{}'.format(alias, found_version + 1)
    return found_index, next_index
