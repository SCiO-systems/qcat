Subcategory Configuration
=========================

Contains the configuration of a subcategory.

The configuration of a Subcategory is only part of the
:doc:`/configuration/questionnaire`.

.. seealso::
    :class:`configuration.configuration.QuestionnaireSubcategory`

+-----------------+----------------------------------------------------+
| Parent element: | :doc:`/configuration/category`                     |
+-----------------+----------------------------------------------------+
| Child element:  | :doc:`/configuration/questiongroup`                |
+-----------------+----------------------------------------------------+


Format
------

The basic format of the configuration is as follows::

  {
    # The keyword of the subcategory.
    "keyword": "SUBCAT_KEYWORD",

    # (optional)
    "view_options": {
      # Default: "default"
      "template": "TEMPLATE_NAME",

      # Default: false
      "raw_questions": true,

      # Default: None
      "table_grouping": []
    },

    # (optional)
    "form_options": {
      # Default: "default"
      "template": "TEMPLATE_NAME",

      # Default: ""
      "label_tag": "h3",

      # Default: ""
      "label_class": "top-margin",

      # Default: []
      "questiongroup_conditions": [],

      # Default: ""
      "questiongroup_conditions_template": ""
    },

    # A list of questiongroups.
    "questiongroups": [
      # ...
    ],

    # A list of subcategories.
    "subcategories": [
      # ...
    ]
  }

.. seealso::
    For more information on the configuration of its child elements,
    please refer to their respective documentation:

    * :doc:`/configuration/questiongroup`

    Also refer to the :ref:`configuration_questionnaire_example` of a
    Questionnaire configuration.


``keyword``
^^^^^^^^^^^

The keyword of the category.


``view_options``
^^^^^^^^^^^^^^^^

(Optional). An optional object containing configuration options for the
view representation of the question.

  * ``template``: An optional template name. Must be a valid file name
    with ``.html`` ending in folder ``templates/details/subcategory/``.

  * ``raw_questions`` (bool): An optional boolean indicating whether to
    (additionally) render the questions in their raw format.

  * ``table_grouping``: A nested array to define the layout of the table
    based on the keywords of the questiongroups of the subcategory.

    Example::

      "table_grouping": [
        ["qg_25", "qg_27"],
        ["qg_26", "qg_28"]
      ]

    Creates the following table (with ``"view_template": "table_1"``):

    +------------+------------+
    | ``qg_25``  | ``qg_26``  |
    +            +------------+
    |            | ``qg_26``  |
    +------------+------------+


``form_options``
^^^^^^^^^^^^^^^^

(Optional). An optional object containing configuration options for the
form representation of the question.

  * ``template``: An optional name of a template to be used for the
    rendering of the subcategory form. The name of the template needs to
    match a file with the ending ``.html`` inside
    ``questionnaire/templates/form/subcategory/``. If not specified, the
    default layout (``default.html``) is used.

    Please note that some templates require additional options to be set.

  * ``label_tag`` (str): Specifies the tag used for the label (eg. ``h3``). Used
    only for template ``has_subcategories``.

  * ``label_class`` (str): Specifies an (additional) class name for the label
    tag. Currently only used for template ``has_subcategories``.

  * ``questiongroup_conditions`` (list): A list of questiongroup conditions to
    be passed to the subcategory template in case of special rendering. Must
    correspond to the list of ``questiongroup_conditions`` set in the
    ``form_options`` of the first key of the first questiongroup.

  * ``questiongroup_conditions_template`` (str): Indicate a field template to be
    used for the rendering of the question which renders the conditional
    question (eg. ``checkbox_with_questiongroup``). Must be used in combination
    with ``questiongroup_conditions``. Template must exist in
    ``form/fields/{}.html``.

  * ``helptext_length`` (int): Overwrite the default length (number of words) of
    the helptext shown initially (without the "See more" button).

  * ``numbering`` (str): An optional numbering of the subcategory.

  * ``has_links`` (bool): This is only required if a questiongroup within the
    subcategories is used to link to other questionnaires. Defaults to false.

    .. seealso::
        :doc:`/configuration/links`


``questiongroups``
^^^^^^^^^^^^^^^^^^

A list of :doc:`/configuration/questiongroup`.

.. important::
    The options ``questiongroups`` and ``subcategories`` are exclusive,
    they should not be set both at the same time.


``subcategories``
^^^^^^^^^^^^^^^^^

A list of :doc:`/configuration/subcategory`.

.. important::
    The options ``questiongroups`` and ``subcategories`` are exclusive,
    they should not be set both at the same time.


Form templates
--------------

Every subcategory should render a ``<fieldset>`` and its label as ``<legend>``.
Inside the fieldset, the questiongroups are to be rendered.

For nested subcategories, use template ``has_subcategories``.

Templates for subcategories are situated in the folder
``templates/form/subcategory/``. They have access to the following variables:

  * ``formsets`` (list): A list of tuples containing the configuration and the
    Django FormFormSet objects of the questiongroups (``[({}, <FormFormSet>)]``).

  * ``config`` (dict): A dictionary containing the configuration of the
    subcategory. All of the ``form_options`` specified in the configuration
    are available, as well as the following keys:

    * ``form_template`` (str): The name of the template to be rendered next.

    * ``has_changes`` (bool): A boolean indicating whether there are changes in
      this subcategory compared the older version of the questionnaire.

    * ``helptext`` (str): The helptext for the subcategory.

    * ``label`` (str): The label of the subcategory.

    * ``next_level`` (str): Indicates whether the next child to be rendered is
      another subcategory or a questiongroup. Possible values are
      ``subcategories`` or ``questiongroups``.

    * ``numbering`` (str): The numbering of the subcategory.

    * ``table_grouping`` (from view_options)

    * ``table_headers`` (from view_options)

    * ``table_helptexts`` (from view_options)

    * ``template`` (str): The name of the current subcategory template.
