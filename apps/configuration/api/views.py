from collections import OrderedDict
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apps.api.views import PermissionMixin, LogUserMixin
from apps.configuration.structure import ConfigurationStructure
from apps.configuration.models import Configuration


class ConfigurationStructureView(PermissionMixin, LogUserMixin, GenericAPIView):
    """
    Get the structure of the configuration of a questionnaire.

    Return information about the categories, questiongroups and questions that
    build a questionnaire.

    ``code``: The code of the configuration (e.g. "technologies").

    ``edition``: The edition of the configuration (e.g. "2018").

    Optional request params:

    ``flat``: If present, the structure will be a flat list of questions.
    """

    def get(self, request, *args, **kwargs) -> Response:
        flat = request.GET.get('flat', False)

        structure_obj = ConfigurationStructure(
            code=kwargs['code'],
            edition=kwargs['edition'],
            flat=flat,
        )

        if structure_obj.error:
            # No configuration was found for this code and edition.
            raise Http404()

        return Response(structure_obj.structure)


class ConfigurationView(PermissionMixin, LogUserMixin, GenericAPIView):
    """
    Get available configurations.

    Return the available configurations codes.

    Optional request params:
    ``flat``: If present, the structure will be a flat list of configurations.
    """

    def get(self, request) -> Response:
        flat = request.GET.get('flat', False)
        configurations_obj = Configuration.objects.all()

        if not configurations_obj:
            # No configurations were found
            raise Http404()

        configurations_obj = configurations_obj.values_list('code', flat=flat).distinct().order_by('code')
        data = {"configurations": list(configurations_obj)}

        # Return all available configurations
        return Response(data)


class ConfigurationEditionView(PermissionMixin, LogUserMixin, GenericAPIView):
    """
    Get available editions for the configuration.

    Return the available editions in the configuration.

    ``code``: The code of the configuration (e.g. "technologies").

    Optional request params:
    ``flat``: If present, the structure will be a flat list of questions.
    """

    def get(self, request, *args, **kwargs) -> Response:
        flat = request.GET.get('flat', False)
        editions_obj = Configuration.objects.filter(code=kwargs['code'])

        if not editions_obj:
            # No editions were found for the code
            raise Http404()

        editions_obj = editions_obj.values_list('edition', flat=flat).distinct().order_by('edition')
        data = {"editions": list(editions_obj)}

        # Return all available configurations
        return Response(data)
