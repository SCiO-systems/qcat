from django.conf.urls import url

from .views import SummaryPDFCreateView


urlpatterns = [
    url(r'^(?P<id>[\d]+)/$',
        SummaryPDFCreateView.as_view(),
        name='questionnaire_summary'),
]
