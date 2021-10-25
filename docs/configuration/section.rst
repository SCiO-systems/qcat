Section Configuration
=====================

Contains the configuration of a section.

The configuration of a Section is only part of the
:doc:`/configuration/questionnaire`.

.. seealso::
    :class:`configuration.configuration.QuestionnaireSection`

+-----------------+----------------------------------------------------+
| Parent element: | :doc:`/configuration/questionnaire`                |
+-----------------+----------------------------------------------------+
| Child element:  | :doc:`/configuration/category`                     |
+-----------------+----------------------------------------------------+


Format
------

The basic format of the configuration is as follows::

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
    For more information on the configuration of its child elements,
    please refer to their respective documentation:

    * :doc:`/configuration/category`

    Also refer to the :ref:`configuration_questionnaire_example` of a
    Questionnaire configuration.


``keyword``
^^^^^^^^^^^

The keyword of the section.


``view_options``
^^^^^^^^^^^^^^^^

(Optional). An optional object containing configuration options for the
view representation of the section.

  * ``template``: An optional template name. Must be a valid file name
    with ``.html`` ending in folder ``templates/details/section/``.

  * ``media_gallery``: An optional boolean indicating whether to include
    a media gallery at the top of the section or not. The gallery
    contains all images attached to the questionnaire.


``categories``
^^^^^^^^^^^^^^

A list of :doc:`/configuration/category`.
