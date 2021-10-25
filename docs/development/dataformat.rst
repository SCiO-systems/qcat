Data Format
===========

Questionnaire Storage
---------------------

The data of questionnaires is stored in a JSON format in the ``data``
field of the :class:`questionnaire.models.Questionnaire` model.

Questiongroups
^^^^^^^^^^^^^^

* The data is stored **grouped by questiongroups**. Questiongroups are
  formed based on thematic coherence of similar questions or if
  questions can be repeated multiple times.
* The **keyword** of :class:`configuration.models.Questiongroup` (e.g.
  ``qg_1``, ``qg_2``, ...) is required as an identifier of the
  questiongroup. This way it is not necessary to identify questiongroups
  based on their questions.

The basic format of the data is as follows::

  {
    "qg_1": [
      {
        # Keys and values of qg_1
      },
      {
        # Repeated keys and values of qg_1
      },
      # ...
    ],
    "qg_2": [
      # (Repeated) Keys and values of qg_2
    ],
    # Further questiongroup data
    # ...
  }


Keys and Values
^^^^^^^^^^^^^^^

Keys and values are in general stored as ``"key": "value"`` pair inside
the questiongroup dictionary. However, some of the values are stored a
bit differently, based on the type of the value.

* **Predefined values**: Predefined values (e.g. from dropdowns) are
  stored only as the keyword of the
  :class:`configuration.models.Value`::

    {
      "key": "value_1"
    }

  The translation of the value can then be looked up through the relation
  of the value to :class:`configuration.models.Translation`.

* **Multiple predefined values**: Multiple predefined values (e.g. from
  checkboxes) are stored as an array of keywords of the
  :class:`configuration.models.Value`::

    {
      "key": [
        "value_1",
        "value_2"
      ]
    }

  The translation of the values can then be looked up through the
  relation of the values to :class:`configuration.models.Translation`.

* **Freetext**: Freetext values (e.g. from textfields) can be translated
  and are stored as dictionary with the locale in which they were
  entered as key::

    {
      "key": {
        "en": "Value 1",
        "es": "Valor 1"
      }
    }

  This allows multiple translations for freetext. Each questionnaire has
  a many-to-many relation (
  :class:`questionnaire.models.QuestionnaireTranslation`) to languages.
  This allows easy access to the languages in which a questionnaire is
  available (without having to look inside the data JSON). This relation
  has an additional field to flag the original language in which the
  questionnaire was filled out first.


Example
^^^^^^^

A concrete example of how the questionnaires are stored::

  {
    # Specification of SLM Technology (Part 1)
    "tech_specification_1": [
      {
        # 2.1 Definition of Technology (in one sentence)
        "tech_definition": {
          "en": "Continuous breeding of earthworms in boxes for production of high quality organic compost.",
          "es": "Hacer una crianza permanente de lombrices para producir abono orgánico de alta calidad."
        },
        # 2.2 Description of the SLM Technology
        "tech_description": {
          "en": "Vermiculture is a simple and cheap way to produce a continuous supply of organic compost of high quality. Eisenia foetida, the Red Californian earthworm (also called ‘the red wiggler’) is ideal for vermiculture since it is adapted to a wide range of environmental conditions. Under culture, the worms are kept under shade, in long wooden boxes filled with earth, cattle manure and an absorbent material (eg straw). The box is covered by sheet metal (or wood, thick plastic sheeting, or banana leaves) to protect the worms against UV radiation and birds/chickens, and also to maintain a favourably humid microclimate. Fresh cattle manure is a perfect food for the worms, but rotten coffee pulp can also be fed. Chopped crop residues (eg cowpeas, leucaena leaves or other legumes) may be added.",
          "es": "Se construye una canoa de madera en un lugar con sombra (ej. debajo de árboles). La canoa se tapa con zinc, madera o otros materiales para protejer las lombrices contra sus enemigos y para conservar la humedad. Un alimento adecuado para las lombrices es el estiércol fresco de vaca, también se les puede echar material vegetal verde (Terciopelo, Gandúl, Leucaena, etc.), preferiblemente picada o semidescompuesta ya que las lombrices no tienen dientes más bien chupan partículas de materia orgánica en el suelo. El abono se aplica como fertilizante a cultivos, ha demostrado ser muy eficiente en sus efectos al aumentar la producción de los cultivos. Es importante darle un mantenimiento continua a la lombricultura (mantener humedad, dar alimento cada tres dias), de esta manera se produce abono constantemente con cantidades cada vez más crecientes ya que las lombrices se reproducen rápidamente en un ambiente adecuado. Se utiliza en la mayoría de los casos la Lombriz Roja de California, la cual es un híbrido de varias especies, criado en los años 50 en California para tener una lombriz prolífica, fácil a criar en cautiverio y adaptado a diferentes medios. También se puede utilizar la Cubana roja. Las lombrices son unos de los organismos principales en la cadena de la descomposición de la materia orgánica y en la formación de humus estable en el suelo."
        }
      }
    ],
    # Specification of SLM Technology (Part 2)
    "tech_specification_2": [
      {
        # 2.4 Land use
        "cropland": 5,  # High
        "forest_woodlands": 1,  # Low
        "cropland_sub": [
          "cropland_annual_cropping",
          "cropland_rainfed"
        ]
      }
    ]
  }


.. todo::
    This does not really belong here

Service output:

* With hierarchy (categories and subcategories)
