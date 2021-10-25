Key Configuration
=================

The configuration of a Key is stored in a JSON format in the
``configuration`` field of :class:`configuration.models.Key`.

.. hint::
    The configuration of the key in the database **cannot** be
    overwritten in the questionnaire configuration. The same key can
    be used multiple times and in several questionnaires so any changes
    should be done carefully.

Format
------

The basic format of the configuration is as follows::

  {
    "type": "TYPE"
  }

``type``
^^^^^^^^

The following options are valid for ``type``. Default type is ``char``.

+--------------------+--------------------------------------------------------+
| ``char``           | A simple textfield for short text, with the label      |
|                    | above the field.                                       |
+--------------------+--------------------------------------------------------+
| ``text``           | A textarea for larger text                             |
+--------------------+--------------------------------------------------------+
| ``bool``           | A field for boolean values Yes (stored as ``True``)    |
|                    | and No (stored as ``False``). Renders as radio         |
|                    | buttons.                                               |
+--------------------+--------------------------------------------------------+
| ``measure``        | A field to select measure values (e.g. low, medium,    |
|                    | high). Also allows null values. Renders as button      |
|                    | group.                                                 |
|                    |                                                        |
|                    | The values of ``measure`` fields are stored as         |
|                    | integers in the database. This allows easier queries   |
|                    | such as "greater than 'low'".                          |
|                    |                                                        |
|                    | *This type requires values related to the key to be    |
|                    | present in the database.*                              |
+--------------------+--------------------------------------------------------+
| ``checkbox``       | A simple checkbox list to allow the selection of       |
|                    | multiple values. Renders as checklist.                 |
|                    |                                                        |
|                    | *This type requires values related to the key to be    |
|                    | present in the database.*                              |
+--------------------+--------------------------------------------------------+
| ``image_checkbox`` | A checkbox list with images to allow the selection of  |
|                    | multiple values. Renders as checklist with images.     |
|                    |                                                        |
|                    | *This type requires values related to the key to be    |
|                    | present in the database and to have a valid*           |
|                    | :ref:`value_configuration_image_name` *configuration.* |
+--------------------+--------------------------------------------------------+
| ``select_type``    | A select field which allows selection by typing.       |
|                    | Renders the field with `Chosen`_.                      |
+--------------------+--------------------------------------------------------+
| ``select``         | A simple select field without typing.                  |
+--------------------+--------------------------------------------------------+
| ``cb_bool``        | Basically a boolean field but rendered as a single     |
|                    | checkbox (selected = true, not selected = false).      |
+--------------------+--------------------------------------------------------+
| ``date``           | A datepicker field.                                    |
+--------------------+--------------------------------------------------------+
| ``file``           | A field to upload any file (as opposed to ``image``    |
+--------------------+--------------------------------------------------------+
| ``image``          | A field to upload an image.                            |
+--------------------+--------------------------------------------------------+
| ``hidden``         | A hidden input field.                                  |
+--------------------+--------------------------------------------------------+
| ``radio``          | A set of radio buttons, needs values.                  |
+--------------------+--------------------------------------------------------+
| ``user_id``        | A special field which allows to select a user.         |
+--------------------+--------------------------------------------------------+
| ``link_id``        | A special field which allows to select another         |
|                    | questionnaire.                                         |
+--------------------+--------------------------------------------------------+
| ``int``            | A field rendered as input type="number", the           |
|                    | validation makes sure it contains only integers.       |
+--------------------+--------------------------------------------------------+
| ``float``          | A field rendered as input type="number", can contain   |
|                    | decimal numbers                                        |
+--------------------+--------------------------------------------------------+
| ``select_model``   | A select field similar to ``select_type`` which lets   |
|                    | you select an instance of a model which has to be      |
|                    | specified in the ``form_options``.                     |
+--------------------+--------------------------------------------------------+
| ``display_only``   | A field rendered as hidden in the form, but displayed  |
|                    | like a textfield in the details.                       |
+--------------------+--------------------------------------------------------+

.. _Chosen: http://harvesthq.github.io/chosen/
