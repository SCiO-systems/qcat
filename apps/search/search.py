from functools import lru_cache

from django.conf import settings
from elasticsearch import TransportError

from apps.questionnaire.models import Questionnaire
from .index import get_elasticsearch
from .utils import get_alias, ElasticsearchAlias

es = get_elasticsearch()


def get_es_query(
        filter_params: list=None, query_string: str='',
        match_all: bool=True) -> dict:
    """
    Kwargs:
        ``filter_params`` (list): A list of filter parameters. Each
        parameter is a tuple consisting of the following elements:

            [0]: questiongroup

            [1]: key

            [2]: values (list)

            [3]: operator

            [4]: type (eg. checkbox / text)

        ``query_string`` (str): A query string for the full text search.

        ``match_all`` (bool): Whether the query MUST match all filters or not.
        If not all filters must be matched, the results are ordered by relevance
        to show hits matching more filters at the top. Defaults to False.

    Returns:
        ``dict``. A dictionary containing the query to be passed to ES.
    """
    if filter_params is None:
        filter_params = []

    es_queries = []

    def _get_terms(qg, k, v):
        return {
            'terms': {
                f'filter_data.{qg}__{k}': [v.lower()]
            }
        }

    # Filter parameters: Nested subqueries to access the correct
    # questiongroup.
    for filter_param in list(filter_params):

        if filter_param.type in [
                'checkbox', 'image_checkbox', 'select_type', 'select_model',
                'radio', 'bool']:

            # So far, range operators only works with one filter value. Does it
            # even make sense to have multiple of these joined by OR with the
            # same operator?
            if filter_param.operator in ['gt', 'gte', 'lt', 'lte']:
                raise NotImplementedError(
                    'Filtering by range is not yet implemented.')
            else:
                if len(filter_param.values) > 1:
                    matches = [
                        _get_terms(filter_param.questiongroup,
                                          filter_param.key, v) for v in
                        filter_param.values]
                    query = {
                        'bool': {
                            'should': matches
                        }
                    }
                else:
                    query = _get_terms(
                        filter_param.questiongroup, filter_param.key,
                        filter_param.values[0])

            es_queries.append(query)

        elif filter_param.type in ['text', 'char']:
            raise NotImplementedError(
                'Filtering by text or char is not yet implemented/supported.')

        elif filter_param.type in ['_date']:
            raise NotImplementedError('Not yet implemented.')

        elif filter_param.type in ['_flag']:
            raise NotImplementedError('Not yet implemented.')

        elif filter_param.type in ['_lang']:
            es_queries.append({
                'terms': {
                    'translations': [filter_param.values]
                }
            })

        elif filter_param.type == '_edition':
            es_queries.append({
                'terms': {
                    'serializer_edition': [filter_param.values]
                }
            })

    if query_string:
        es_queries.append({
            'multi_match': {
                'query': get_escaped_string(query_string),
                'fields': [
                    'list_data.name.*^4',
                    'list_data.definition.*',
                    'list_data.country'
                ],
                'type': 'cross_fields',
                'operator': 'and',
            }
        })

    es_bool = 'must' if match_all is True else 'should'

    if query_string == '':
        # Default sort: By country, then by score.
        sort = [
            {
                'list_data.country.keyword': {
                    'order': 'asc'
                }
            },
            '_score',
        ]
    else:
        # If a phrase search is done, then only use the score to sort.
        sort = ['_score']

    return {
        'query': {
            'bool': {
                es_bool: es_queries
            }
        },
        'sort': sort,
    }


def advanced_search(
        filter_params: list=None, query_string: str='',
        configuration_codes: list=None, limit: int=10,
        offset: int=0, match_all: bool=True) -> dict:
    """
    Kwargs:
        ``filter_params`` (list): A list of filter parameters. Each
        parameter is a tuple consisting of the following elements:

            [0]: questiongroup

            [1]: key

            [2]: values (list)

            [3]: operator

            [4]: type (eg. checkbox / text)

        ``query_string`` (str): A query string for the full text search.

        ``configuration_codes`` (list): An optional list of
        configuration codes to limit the search to certain indices.

        ``limit`` (int): A limit of query results to return.

        ``offset`` (int): The number of query results to skip.

        ``match_all`` (bool): Whether the query MUST match all filters or not.
        If not all filters must be matched, the results are ordered by relevance
        to show hits matching more filters at the top. Defaults to False.

    Returns:
        ``dict``. The search results as returned by
        ``elasticsearch.Elasticsearch.search``.
    """
    query = get_es_query(
        filter_params=filter_params, query_string=query_string,
        match_all=match_all)

    if configuration_codes is None:
        configuration_codes = []

    alias = get_alias(*ElasticsearchAlias.from_code_list(*configuration_codes))

    return es.search(index=alias, body=query, size=limit, from_=offset)


def get_aggregated_values(
        questiongroup, key, filter_type, filter_params: list=None,
        query_string: str='', configuration_codes: list=None,
        match_all: bool=True) -> dict:

    if filter_params is None:
        filter_params = []

    # Remove the filter_param with the current questiongroup and key from the
    # list of filter_params
    relevant_filter_params = [
        f for f in filter_params if
        f.questiongroup != questiongroup and f.key != key]

    query = get_es_query(
        filter_params=relevant_filter_params, query_string=query_string,
        match_all=match_all)

    # For text values, use the keyword. This does not work for integer values
    # (the way boolean values are stored).
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/fielddata.html
    if filter_type == 'bool':
        field = f'filter_data.{questiongroup}__{key}'
    else:
        field = f'filter_data.{questiongroup}__{key}.keyword'

    query.update({
        'aggs': {
            'values': {
                'terms': {
                    'field': field,
                    # Limit needs to be high enough to include all values.
                    'size': 1000,
                }
            }
        },
        'size': 0,  # Do not include the actual hits
    })

    alias = get_alias(*ElasticsearchAlias.from_code_list(*configuration_codes))
    es_query = es.search(index=alias, body=query)

    buckets = es_query.get('aggregations', {}).get('values', {}).get('buckets', [])

    return {b.get('key'): b.get('doc_count') for b in buckets}


def get_element(questionnaire: Questionnaire) -> dict:
    """
    Get a single element from elasticsearch.
    """
    alias = get_alias(
        ElasticsearchAlias.from_configuration(configuration=questionnaire.configuration_object)
    )
    try:
        return es.get_source(index=alias, id=questionnaire.pk, doc_type='questionnaire')
    except TransportError:
        return {}


def get_escaped_string(query_string: str) -> str:
    """
    Replace all reserved characters when searching the ES index.
    """
    for char in settings.ES_QUERY_RESERVED_CHARS:
        query_string = query_string.replace(char, '\\{}'.format(char))
    return query_string


@lru_cache(maxsize=1)
def get_indices_alias() -> list:
    """
    Return a list of all elasticsearch index aliases. Only ES indices which
    start with the QCAT prefix are respected. Editions are stripped away, only the 'type' of the
    index / configuration is relevant.

    """
    indices = []
    for aliases in es.indices.get_alias('*').values():
        for alias in aliases.get('aliases', {}).keys():
            if settings.ES_INDEX_PREFIX not in alias:
                continue
            indices.append(alias.replace(settings.ES_INDEX_PREFIX, '').rsplit('_', 1)[0])
    return indices
