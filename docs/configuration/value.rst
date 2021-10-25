Value Configuration
===================

The configuration of a Value is stored in a JSON format in the
``configuration`` field of :class:`configuration.models.Value`.

.. hint::
    The configuration of the value in the database **cannot** be
    overwritten in the questionnaire configuration. The same value can
    be used in several questionnaires and for multiple keys so any
    changes should be done carefully.

Format
------

The basic format of the configuration is as follows::

  {
    # (optional)
    "image_name": ""
  }


.. _value_configuration_image_name:

``image_name``
^^^^^^^^^^^^^^

The ``image_name`` defines the filename of the image associated with
this value. This is in particular required for values belonging to a key
with type ``image_checklist``.
