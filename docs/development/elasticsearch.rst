Elasticsearch
=============

`Elasticsearch`_ is used as a search engine to query the questionnaires.

.. _Elasticsearch: https://www.elastic.co/products/elasticsearch

.. important::
    The indices in Elasticsearch only contain public Questionnaires (
    with status = ``active``). If pending questionnaires (eg. the
    pending changes of the current user) are to be displayed, use a
    database query instead of Elasticsearch.


Administration
--------------

There is an administration panel available for superusers. It allows to
create and update indices. The panel can be accessed in the user menu or
directly via ``/search/admin/``.


Structure
---------

The different indices in QCAT are structured as follows:

``/[index]/[type]/[id]``

* **index**: ``[prefix][questionnaire_type]`` (examples:
  ``qcat_technologies``, ``qcat_approaches``).

  * The prefix can be set in the settings.
  * The index is actually an *alias* pointing to an index in behind (for
    example ``qcat_technologies_1``). This allows to update the mapping
    of an index without any downtime (see also
    https://www.elastic.co/blog/changing-mapping-with-zero-downtime).

* **type**: ``questionnaire``. This is currently always set to
  ``questionnaire``.

* **id**:  ``identifier``. The identifier of the questionnaire.


Document format
---------------

A document in elasticsearch contains the following entries (in ``_source``)::

  {
    "data": {
      # A copy of the data dictionary as stored in the JSONB-Field of
      # questionnaire in the database.
    },
    "list_data": {
      # A dictionary containing the entries used for the list
      # representation (as specified in the questionnaire configuration)
    },
    "created": "[timestamp]",
    "updated": "[timestamp]",
    "code": "[code of the questionnaire]",
    "name": {
      # A dictionary containing the translations of the name field (as
      # specified in the questionnaire configuration)
    },
    "configurations": [
      # A list of the configurations in which this questionnaire is
      # available
    ],
    "translations": [
      # A list of the translations in which this questionnaire is
      # available
    ]
  }


Example
-------

Example of a document stored in Elasticsearch::

  {
    "_index": "qcat_test_technologies_1",
    "_type": "questionnaire",
    "_id": "101",
    "_score": 1,
    "_source": {
       "translations": [
          "fr",
          "en"
       ],
       "data": {
          "tech_qg_2": [
             {
                "tech_definition": {
                   "fr": "Ceci est la déscription 1 en français.",
                   "en": "This is the definition of the first WOCAT practice."
                }
             }
          ],
          "qg_name": [
             {
                "name": {
                   "fr": "WOCAT 1 en français",
                   "en": "WOCAT practice 1"
                }
             }
          ]
       },
       "list_data": {
          "name": {
             "fr": "WOCAT 1 en français",
             "en": "WOCAT practice 1"
          },
          "tech_definition": {
             "fr": "Ceci est la déscription 1 en français.",
             "en": "This is the definition of the first WOCAT practice."
          }
       },
       "code": "tech_1",
       "updated": "2015-02-10T16:07:20.847000+00:00",
       "name": {
          "en": "Unknown name"
       },
       "created": "2015-02-10T16:07:20.847000+00:00",
       "configurations": [
          "technologies"
       ]
    }
  }


Helper functions
----------------

The helper functions for Elasticsearch are inside the Django app ``search``.

* :func:`search.search.advanced_search`: The main function used to query
  questionnaires based on their configurations, codes, name and other
  attributes.
