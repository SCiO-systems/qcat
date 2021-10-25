Introduction
============

Settings
--------

Please refer to the :doc:`/configuration/settings` of QCAT.


Questionnaires
--------------

A questionnaire consists of several objects which themselves can have multiple child objects. This represents the hierarchy of the questionnaire.

The elements of a Questionnaire are:

#.  :doc:`Questionnaire</configuration/questionnaire>`: The top node of
    the questionnaire, represents the entire questionnaire.
#.  :doc:`Category </configuration/category>`: A (thematic) group,
    corresponds to a single step in the questionnaire form.
#.  :doc:`Subcategory </configuration/subcategory>`: Another element for
    grouping inside the category.
#.  :doc:`Questiongroup </configuration/questiongroup>`: A group of
    questions which belong together.
#.  :doc:`Question </configuration/question>`: A single question
    consisting of a key and value(s).
#.  :doc:`Key </configuration/key>`: The key of a question.
#.  :doc:`Value </configuration/value>`: The value of a question.
#.  :doc:`Links </configuration/links>`: Links to other questionnaires.

Most of the elements of a questionnaire can have a configuration of
their own, stored in their ``configuration`` field in the database.
However, some of the elements allow overwriting part of their
configuration in the
:doc:`Questionnaire configuration </configuration/questionnaire>`.

The following table indicates which objects allow configuration in the
database and which can have their configuration defined or overwritten
in the Questionnaire configuration.

+--------------------------+---------------------+----------------------------+
|                          | Configuration in DB | In Questionnaire           |
+==========================+=====================+============================+
| Category                 | No                  | Yes                        |
+--------------------------+---------------------+----------------------------+
| Subcategory              | No                  | Yes                        |
+--------------------------+---------------------+----------------------------+
| Questiongroup            | Yes                 | Yes                        |
+--------------------------+---------------------+----------------------------+
| Question                 | No                  | Yes (only in questionnaire |
|                          |                     | configuration)             |
+--------------------------+---------------------+----------------------------+
| Key                      | Yes                 | No                         |
+--------------------------+---------------------+----------------------------+
| Value                    | Yes                 | No                         |
+--------------------------+---------------------+----------------------------+


.. todo::
    Questionnaire configurations can inherit from another one. This
    needs further documentation.
