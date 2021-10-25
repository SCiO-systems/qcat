class ConfigurationError(Exception):
    pass


class ConfigurationErrorNoConfigurationFound(ConfigurationError):

    def __init__(self, keyword):
        self.keyword = keyword

    def __str__(self):
        return 'No active configuration found for keyword "{}"'.format(
            self.keyword)


class ConfigurationErrorNotInDatabase(ConfigurationError):

    def __init__(self, Model, keyword):
        self.Model = Model
        self.keyword = keyword

    def __str__(self):
        return 'No database entry found for keyword "{}" in model {}'.format(
            self.keyword, self.Model)


class ConfigurationErrorInvalidOption(ConfigurationError):

    def __init__(self, option, configuration, object_):
        self.option = option
        self.configuration = configuration
        self.object_ = object_

    def __str__(self):
        return 'Option "{}" is not valid for configuration "{}" of object {}.'\
            .format(self.option, self.configuration, self.object_)


class ConfigurationErrorInvalidCondition(ConfigurationError):

    def __init__(self, condition, error):
        self.condition = condition
        self.error = error

    def __str__(self):
        return 'Condition "{}" is not valid. Reason: "{}"'.format(
            self.condition, self.error)


class ConfigurationErrorInvalidQuestiongroupCondition(ConfigurationError):

    def __init__(self, condition, error):
        self.condition = condition
        self.error = error

    def __str__(self):
        return 'Questiongroup condition "{}" is not valid. Reason: "{}"'.\
            format(self.condition, self.error)


class ConfigurationErrorInvalidConfiguration(ConfigurationError):

    def __init__(self, configuration, format, parent):
        self.configuration = configuration
        self.format = format
        self.parent = parent

    def __str__(self):
        return 'Configuration "{}" (part of "{}") is missing or is not of '\
            'format "{}"'.format(self.configuration, self.parent, self.format)


class ConfigurationErrorTemplateNotFound(ConfigurationError):

    def __init__(self, template, object_):
        self.template = template
        self.object_ = object_

    def __str__(self):
        return 'Template "{}" for object "{}" not found.'.format(
            self.template, self.object_)


class QuestionnaireFormatError(Exception):

    def __init__(self, questionnaire_data):
        self.questionnaire_data = questionnaire_data

    def __str__(self):
        return 'The questionnaire format is invalid: "{}"'.format(
            self.questionnaire_data)
