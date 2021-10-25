Link Configuration
==================

Links to other questionnaires (eg. from Technologies to Approaches) can be
configured within the questiongroup. However, some options need to be specified
at subcategory level.

Example::

  {
    "keyword": "SUBCAT_KEYWORD",
    "form_options": {
      "has_links": true
    },
    "questiongroups": [
      {
        "keyword": "QUESTIONGROUP_KEYWORD__CONFIGURATION_OF_LINK",
        "form_options": {
          "template": "select_link",
          "link": "CONFIGURATION_OF_LINK",
          "max_num": 3
        },
        "view_options": {
          "template": "links"
        },
        "questions": [
          {
            "keyword": "link_id"
          }
        ]
      }
    ]
  }


Or more concrete::

  {
    "keyword": "app__1__4",
    "form_options": {
      "has_links": true
    },
    "questiongroups": [
      {
        "keyword": "app_qg__technologies",
        "form_options": {
          "template": "select_link",
          "link": "technologies",
          "max_num": 3
        },
        "view_options": {
          "template": "links"
        },
        "questions": [
          {
            "keyword": "link_id"
          }
        ]
      }
    ]
  }


Please note that the keyword of the questiongroup is crucial, it needs to
contain the name of the configuration to be linked at the end, separated by
``__``. Examples: ``app_qg__technologies`` linking to technologies or
``tech_qg__approaches`` linking to approaches.


For more information, please look at :doc:`/configuration/subcategory` or
:doc:`/configuration/questiongroup`
