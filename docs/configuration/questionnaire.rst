Questionnaire Configuration
===========================

Contains the configuration of an entire questionnaire. It allows to
overwrite certain default configurations of its child elements.

The configuration of a Questionnaire is stored in a JSON format in the
``configuration`` field of :class:`configuration.models.Configuration`.

.. seealso::
    :class:`configuration.configuration.QuestionnaireConfiguration`

+-----------------+----------------------------------------------------+
| Parent element: | (None)                                             |
+-----------------+----------------------------------------------------+
| Child element:  | :doc:`/configuration/category`                     |
+-----------------+----------------------------------------------------+

Format
------

The basic format of the configuration is as follows::

  {
    # See class QuestionnaireSection for the format of sections.
    "sections": [
      {
        # See class QuestionnaireCategory for the format of categories.
        "categories": [
          {
            # The keyword of the category.
            "keyword": "CAT_KEYWORD",

            # See class QuestionnaireSubcategory for the format of subcategories.
            "subcategories": [
              {
                # The keyword of the subcategory.
                "keyword": "SUBCAT_KEYWORD",

                # See class QuestionnaireQuestiongroup for the format of
                # questiongroups.
                "questiongroups": [
                  {
                    # The keyword of the questiongroup.
                    "keyword": "QUESTIONGROUP_KEYWORD",

                    # (optional)
                    "template": "TEMPLATE_NAME",

                    # (optional)
                    "min_num": 1,

                    # (optional)
                    "max_num": 1,

                    # See class QuestionnaireQuestion for the format of questions.
                    "questions": [
                      {
                        # The key of the question.
                        "key": "KEY"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }

.. seealso::
    For more information on the configuration of its child elements,
    please refer to their respective documentation:

    * :doc:`/configuration/category`
    * :doc:`/configuration/subcategory`
    * :doc:`/configuration/questiongroup`
    * :doc:`/configuration/question`
    * :doc:`/configuration/key`
    * :doc:`/configuration/value`

``sections``
^^^^^^^^^^^^

A list of :doc:`/configuration/section`.

``links``
^^^^^^^^^

A dictionary with the configuration of the links which are possible from
this questionnaire. Please note that only base_configurations should be
linked.


.. _configuration_questionnaire_example:

Example
-------

The following is an arbitrary example of how a configuration could look like::

  {
    "sections": [
      {
        "keyword": "section_1",
        "categories": [
          {
            "keyword": "cat_0",
            "subcategories": [
              {
                "keyword": "subcat_0_1",
                "questiongroups": [
                  {
                    "keyword": "qg_14",
                    "questions": [
                      {
                        "keyword": "key_19",
                        "in_list": true
                      }
                    ]
                  },
                  {
                    "keyword": "qg_15",
                    "questions": [
                      {
                        "keyword": "key_20"
                      }
                    ]
                  }
                ]
              }
            ]
          },
          {
            "keyword": "cat_1",
            "subcategories": [
              {
                "keyword": "subcat_1_1",
                "questiongroups": [
                  {
                    "questions": [
                      {
                        "keyword": "key_1",
                        "in_list": true,
                        "is_name": true
                      },
                      {
                        "keyword": "key_3",
                        "form_template": "inline_2",
                        "max_length": 50
                      }
                    ],
                    "keyword": "qg_1"
                  },
                  {
                    "questions": [
                      {
                        "keyword": "key_2",
                        "max_length": 50,
                        "num_rows": 2
                      },
                      {
                        "keyword": "key_3"
                      }
                    ],
                    "keyword": "qg_2"
                  }
                ]
              },
              {
                "keyword": "subcat_1_2",
                "questiongroups": [
                  {
                    "questions": [
                      {
                        "keyword": "key_4"
                      },
                      {
                        "keyword": "key_11",
                        "questiongroup_conditions": [
                          ">0|sample_qg_22"
                        ]
                      }
                    ],
                    "keyword": "qg_3"
                  },
                  {
                    "keyword": "qg_22",
                    "questiongroup_condition": "sample_qg_22",
                    "questions": [
                      {
                        "keyword": "key_27",
                        "questiongroup_conditions": [
                          "=='value_27_3'|sample_qg_23"
                        ]
                      }
                    ]
                  },
                  {
                    "keyword": "qg_23",
                    "questiongroup_condition": "sample_qg_23",
                    "questions": [
                      {
                        "keyword": "key_28"
                      }
                    ]
                  },
                  {
                    "keyword": "qg_29",
                    "detail_level": "sample_plus",
                    "questions": [
                      {
                        "keyword": "key_37"
                      },
                      {
                        "keyword": "key_38"
                      }
                    ]
                  }
                ]
              }
            ]
          },
          {
            "keyword": "cat_2",
            "subcategories": [
              {
                "keyword": "subcat_2_1",
                "questiongroups": [
                  {
                    "questions": [
                      {
                        "keyword": "key_13",
                        "questiongroup_conditions": [
                          "=='value_13_5'|sample_qg_18"
                        ]
                      }
                    ],
                    "keyword": "qg_10"
                  },
                  {
                    "keyword": "qg_18",
                    "questiongroup_condition": "sample_qg_18",
                    "questions": [
                      {
                        "keyword": "key_24"
                      }
                    ]
                  }
                ]
              },
              {
                "keyword": "subcat_2_2a",
                "subcategories": [
                  {
                    "keyword": "subcat_2_2b",
                    "questiongroups": [
                      {
                        "questions": [
                          {
                            "keyword": "key_12",
                            "view_template": "textinput"
                          }
                        ],
                        "keyword": "qg_9"
                      }
                    ]
                  }
                ]
              },
              {
                "keyword": "subcat_2_3a",
                "subcategories": [
                  {
                    "keyword": "subcat_2_3b",
                    "subcategories": [
                      {
                        "keyword": "subcat_2_3c",
                        "questiongroups": [
                          {
                            "keyword": "qg_19",
                            "questions": [
                              {
                                "keyword": "key_5",
                                "in_list": true
                              }
                            ]
                          }
                        ]
                      }
                    ]
                  }
                ]
              },
              {
                "keyword": "subcat_2_4",
                "subcategories": [
                  {
                    "keyword": "subcat_2_4a",
                    "questiongroups": [
                      {
                        "keyword": "qg_20",
                        "questions": [
                          {
                            "keyword": "key_25"
                          }
                        ]
                      }
                    ]
                  },
                  {
                    "keyword": "subcat_2_4b",
                    "subcategories": [
                      {
                        "keyword": "subcat_2_4b1",
                        "subcategories": [
                          {
                            "keyword": "subcat_2_4b2",
                            "questiongroups": [
                              {
                                "keyword": "qg_21",
                                "questions": [
                                  {
                                    "keyword": "key_26"
                                  }
                                ]
                              }
                            ]
                          }
                        ]
                      }
                    ]
                  }
                ]
              }
            ]
          },
          {
            "keyword": "cat_3",
            "subcategories": [
              {
                "keyword": "subcat_3_1",
                "questiongroups": [
                  {
                    "questions": [
                      {
                        "keyword": "key_7"
                      }
                    ],
                    "keyword": "qg_5"
                  },
                  {
                    "questions": [
                      {
                        "keyword": "key_8"
                      }
                    ],
                    "keyword": "qg_6"
                  },
                  {
                    "keyword": "qg_13",
                    "numbered": "inline",
                    "questions": [
                      {
                        "keyword": "key_17"
                      },
                      {
                        "keyword": "key_18"
                      }
                    ]
                  }
                ]
              },
              {
                "keyword": "subcat_3_2",
                "questiongroups": [
                  {
                    "keyword": "qg_7",
                    "numbered": "prefix",
                    "questions": [
                      {
                        "keyword": "key_9"
                      }
                    ]
                  },
                  {
                    "questions": [
                      {
                        "keyword": "key_10"
                      }
                    ],
                    "keyword": "qg_8",
                    "max_num": 3,
                    "min_num": 2
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        "keyword": "section_2",
        "categories": [
          {
            "keyword": "cat_4",
            "subcategories": [
              {
                "keyword": "subcat_4_1",
                "questiongroups": [
                  {
                    "questions": [
                      {
                        "keyword": "key_14",
                        "filter_options": {
                            "order": 1
                        }
                      }
                    ],
                    "keyword": "qg_11"
                  },
                  {
                    "questions": [
                      {
                        "keyword": "key_16",
                        "conditional": true
                      },
                      {
                        "keyword": "key_15",
                        "conditions": [
                          "value_15_1|True|key_16"
                        ]
                      }
                    ],
                    "keyword": "qg_12"
                  }
                ]
              },
              {
                "keyword": "subcat_4_2",
                "questiongroups": [
                  {
                    "keyword": "qg_16",
                    "questions": [
                      {
                        "keyword": "key_21",
                        "view_template": "textinput",
                        "questiongroup_conditions": [
                          ">1|questiongroup_17",
                          "<3|questiongroup_17"
                        ]
                      }
                    ]
                  },
                  {
                    "keyword": "qg_17",
                    "questiongroup_condition": "questiongroup_17",
                    "questions": [
                      {
                        "keyword": "key_22"
                      },
                      {
                        "keyword": "key_23"
                      }
                    ]
                  }
                ]
              },
              {
                "keyword": "subcat_4_3",
                "questiongroups": [
                  {
                    "keyword": "qg_24",
                    "view_template": "bars",
                    "questions": [
                      {
                        "keyword": "key_29"
                      },
                      {
                        "keyword": "key_30"
                      },
                      {
                        "keyword": "key_31"
                      },
                      {
                        "keyword": "key_32"
                      }
                    ]
                  }
                ]
              }
            ]
          },
          {
            "keyword": "cat_5",
            "subcategories": [
              {
                "keyword": "subcat_5_1",
                "form_template": "table_1",
                "view_template": "table_1",
                "table_grouping": [
                  [
                    "qg_25",
                    "qg_27"
                  ],
                  [
                    "qg_26",
                    "qg_28"
                  ]
                ],
                "questiongroups": [
                  {
                    "keyword": "qg_25",
                    "questions": [
                      {
                        "keyword": "key_33"
                      },
                      {
                        "keyword": "key_34"
                      }
                    ]
                  },
                  {
                    "keyword": "qg_26",
                    "min_num": 3,
                    "questions": [
                      {
                        "keyword": "key_35"
                      },
                      {
                        "keyword": "key_36"
                      }
                    ]
                  },
                  {
                    "keyword": "qg_27",
                    "questions": [
                      {
                        "keyword": "key_33"
                      },
                      {
                        "keyword": "key_34"
                      }
                    ]
                  },
                  {
                    "keyword": "qg_28",
                    "min_num": 3,
                    "questions": [
                      {
                        "keyword": "key_35"
                      },
                      {
                        "keyword": "key_36"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      }
    ],
    "links": [
      {
        "keyword": "samplemulti"
      }
    ]
  }

