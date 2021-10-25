Translations
============

The source language of this project is *English*. Refer to the `django docs`_
for translations within django.

All fixtures for configurations and questionnaires are expected in English.
Additional languages in the fixtures will not be used.


Basics
------

* Translations are handled separately for the texts from django (i18n in python
  files) and questionnaires (i18n in models; see
  ``questionnaire.models.Translation``).
* Historically, a jsonb field stores all translations. The structure is:
  ``{'configuration_type': {'keyword': {'en': 'string ahoy'}}}``
* This is caused by the way configurations are created: as fixtures.
* Translation changes are expected to happen often, occasionally new languages
  will be introduced. Managing translations should require minimal effort from
  developers.
* These preconditions and the requirement for one system to
  handle all translations result in a workaround.
* gettext is the 'default' way to handle translations.


Workflow
--------

* A `string freeze`_ is announced for before deploying to production.
* Creation of new .po files is therefore only allowed on the develop branch
* The command ``makemessages`` handles the following:

  * Get latest resources from Transifex
  * If the -fp flag is set, the pull is 'forced'. This means that local
    translation files are overwritten. By default, local files are not
    overwritten if they are newer than the version on Transifex.
  * If new files are pulled, the po files are compiled (to mo files)
  * Check, if new translations for configurations are available. If so, the
    content is written into a separate model. A temporary file based on this
    model is created, this temporary file is then parsed by djangos own
    makemessages command.
  * Djangos ``makemessages`` creates .po files
  * The user is asked if the new files should be uploaded to Transifex.


Recipe
------

* (evtl.: backup translations from Transifex): https://www.transifex.com/university-of-bern-cde/qcat/website/
* Activate virtual environment
* ``python manage.py makemessages -fp``
* Release develop branch on master

Todo
----

* Check if `txgh`_ would be helpful.
* The current workflow is rather strict (no translations on feature branches,
  workaround with temporary file). Reviewing this workflow is recommended.

.. _django docs: https://docs.djangoproject.com/en/1.8/topics/i18n/translation/
.. _Transifex: https://www.transifex.com/university-of-bern-cde/qcat/
.. _txgh: https://github.com/transifex/txgh
.. _string freeze: https://wiki.openstack.org/wiki/StringFreeze
