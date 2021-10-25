import unicodedata

from django.forms import fields


class XMLCompatCharField(fields.CharField):
    """
    Strip 'control characters', as XML 1.0 does not allow them and the API may
    return data in XML.
    """

    def to_python(self, value):
        value = super().to_python(value=value)
        return self.remove_control_characters(value)

    @staticmethod
    def remove_control_characters(input):
        valid_chars = ['\n', '\r']
        return "".join(ch for ch in input if
                       unicodedata.category(ch)[0] != "C" or ch in valid_chars)
