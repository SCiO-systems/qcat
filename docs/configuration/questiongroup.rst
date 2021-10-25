Questiongroup Configuration
===========================

Contains the configuration of a questiongroup.

The configuration of a Questiongroup is stored in a JSON format in the
``configuration`` field of :class:`configuration.models.Questiongroup`.
It can also be overwritten in the :doc:`/configuration/questionnaire`.

.. seealso::
    :class:`configuration.configuration.QuestionnaireQuestiongroup`

+-----------------+----------------------------------------------------+
| Parent element: | :doc:`/configuration/subcategory`                  |
+-----------------+----------------------------------------------------+
| Child element:  | :doc:`/configuration/question`                     |
+-----------------+----------------------------------------------------+


Format
------

The basic format of the configuration is as follows::

  {
    # The keyword of the questiongroup.
    "keyword": "QUESTIONGROUP_KEYWORD",

    # (optional)
    "view_options": {
      # Default: "default"
      "template": "TEMPLATE_NAME",

      # Default: ""
      "conditional_question": "KEY_KEYWORD",

      # Default: ""
      "layout": "before_table"
    },

    # (optional)
    "form_options": {
      # Default: "default"
      "template": "TEMPLATE_NAME",

      # Default: 1
      "min_num": 2,

      # Default: 1
      "max_num: 3,

      # Default: ""
      "numbered": "NUMBERED",

      # Default: ""
      "detail_level": "DETAIL_LEVEL",

      # Default: ""
      "questiongroup_condition": "CONDITION_NAME",

      # Default: "" - can also be a list!
      "layout": "before_table",

      # Default: ""
      "row_class": "no-top-margin".

      # Default: "h4"
      "label_tag": "h5",

      # Default: ""
      "label_class": "",

      # Default: ""
      "table_columns": 2
    },

    # A list of questions.
    "questions": [
      # ...
    ]
  }

.. seealso::
    For more information on the configuration of its child elements,
    please refer to their respective documentation:

    * :doc:`/configuration/question`

    Also refer to the :ref:`configuration_questionnaire_example` of a
    Questionnaire configuration.


``keyword``
^^^^^^^^^^^

The keyword of the questiongroup.

.. hint::
    Each keyword of a questiongroup needs to be unique throughout all
    questionnaires. This is because questionnaire data is stored by
    their questiongroup keyword and when queried it needs to be mapped
    to the correct questiongroup.


``view_options``
^^^^^^^^^^^^^^^^

(Optional). An optional object containing configuration options for the
view representation of the questiongroup.

  * ``template``: An optional template name. Must be a valid file name
    with ``.html`` ending in folder ``templates/details/questiongroup/``.

  * ``conditional_question`` (str): For conditional questiongroups, the name of
    the key for which the questiongroup will be rendered next to. Works for
    example with subcategory template "image_questiongroups"

  * ``layout`` (str): Additional indications used for the layout. These depend
    largely on the template used. Known values are "before_table" or "label".

  * ``raw_questions`` (bool): If set to ``true``, raw questions are added to the
    template under the variable ``raw_questions``.

  * ``with_keys`` (bool): If set to ``true``, a list with all the key labels of
    the questiongroup is added to the template (variable ``keys``).


``form_options``
^^^^^^^^^^^^^^^^

(Optional). An optional object containing configuration options for the
form representation of the question.

  * ``template``: An optional template name. Must be a valid file name
    with ``.html`` ending in folder ``templates/form/questiongroup/``. If not
    specified, the default layout (``default.html``) is used.

  * ``min_num``: The minimum for repeating questiongroups to appear.
    Defaults to 1.

  * ``max_num``: The maximum for repeating questiongroups to appear. If
    larger than ``min_num``, buttons to add or remove questiongroups
    will be rendered in the form. Defaults to ``min_num``.

  * ``numbered``: An optional parameter if the questiongroup is to be
    numbered. Currently, mainly the value ``display`` is used.

  .. Possible values are ``inline`` (numbering inside field
    label) or ``prefix`` (numbering indented before fields). If not
    specified, no numbering is used.

    .. .. hint::
        If possible, ``prefix`` should be used.

  * ``detail_level``: An optional parameter if the questiongroup
    contains additional, mostly more detailed questions which are only
    visible after clicking on a link. This is used for the
    "Plus"-Questions. The value of the parameter can be freely chosen.

  * ``questiongroup_condition``: An optional name of a condition valid
    for this questiongroup. The name must correspond to one of
    ``questiongroup_conditions`` of a Question configuration.

    .. seealso::
        :doc:`/configuration/question`

  * ``layout`` (str): General layout indications for the layout of the
    questiongroup inside the subcategory. This depends a lot on the subcategory
    template. Known values are for example "before_table" used in template
    "questionnaire/templates/form/subcategory/table_input.html" or
    "no_label_row" for tables.

  * ``columns_custom`` (list): A nested list indicating the distribution of the
    columns, eg. [["12"], ["8", "4"]]. This is valid for template
    "columns_custom".

  * ``user_role`` (str): A specific configuration used only for template
    ``select_user``.

  * ``row_class`` (str): An additional CSS class for the ``<div class="row">``
    element containing all the questions of the questiongroup.
    Example: "no-top-margin".

  * ``label_tag`` (str): Specifies the tag used for the label. Default is
    ``h4``.

  * ``label_class`` (str): Specifies an additional class name for the label tag.

  * ``column_widths`` (list): Specify the column widths for the table. Used in
    template ``table``. Example::

        "column_widths": ["60%", "40%"]

  * ``table_columns`` (int): Indicate the number of columns of the table. Used
    by template ``table_columns``.

  * ``helptext_length`` (int): Overwrite the default length (number of words) of
    the helptext shown initially (without the "See more" button).

  * ``link`` (str): Required if the questiongroup is a link to other
    questionnaires. In this case, this value must contain the name of the
    configuration which is linked (eg. ``technologies``).


``questions``
^^^^^^^^^^^^^

A list of :doc:`/configuration/question`.


Form templates
--------------

Templates for questiongroups are situated in the folder
``templates/form/questiongroup/``. They have access to the following variables:

  * ``formset``: A Django FormFormSet object, containing the (repeating) forms
    (``formset.forms``) as well as the management form
    (``formset.management_form``) which needs to be rendered in order for the
    form to be submitted correctly.

  * ``config`` (dict): A dictionary containing the configuration of the
    questiongroup. All of the ``form_options`` specified in the configuration
    are available, as well as the following keys:

    * ``has_changes`` (bool): A boolean indicating whether there are changes in
      this questiongroup compared the older version of the questionnaire.

    * ``helptext`` (str): The helptext for the questiongroup.

    * ``keyword`` (str): The keyword of the questiongroup.

    * ``label`` (str): The label of the questiongroup (if available).

    * ``options`` (dict): The options of the keys, (``{"key_1": {}}``), to be
      passed to the template of the question.

    * ``template`` (str): The name of the current questiongroup template.

    * ``templates`` (dict): A dictionary of the templates of the questions
      (``{"key_1": {}}``), to be passed to their templates
