Data flow
=========

* All data is saved in the Postgres database.
* Public questionnaires are put into the elasticsearch index.
* Converting a model instance into JSON (for elasticsearch) is handled by the
  serializer: ``questionnaire.serializers.QuestionnaireSerializer``
* All relevant data (see below) must be available for objects from the model
  and elasticsearch; serializing and deserializing must work in both ways.


Website
-------
* The list view on qcat.wocat.net accesses eleasticsearch only.
* The detail view on qcat.wocat.net calls the method ``get_details`` on
  the configuration of the serialized questionnaire.


API
---
* The list view lists all data from elasticsearch.
* The detail view on qcat.wocat.net calls the method ``get_details`` on
  the configuration of the serialized questionnaire.


Serializing
-----------
* If possible, the serializer calls model properties.
* All data which is depending on the config calls a method on the serializer
* The configuration is loaded when the serializer is instantiated.
