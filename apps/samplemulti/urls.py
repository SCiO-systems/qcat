from django.conf.urls import url
from django.views.generic import TemplateView

from apps.questionnaire import views

from . import views as samplemulti_views


urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='samplemulti/home.html'), name='home'),
    url(r'^view/(?P<identifier>[^/]+)/$',
        views.QuestionnaireView.as_view(url_namespace=__package__),
        name='questionnaire_details',
        ),
    url(r'^view/(?P<identifier>[^/]+)/(?P<step>\w+)/$',
        samplemulti_views.questionnaire_view_step,
        name='questionnaire_view_step'),
    url(r'^edit/new/$',
        views.QuestionnaireEditView.as_view(url_namespace=__package__),
        name='questionnaire_new'),
    url(r'^edit/(?P<identifier>[^/]+)/$',
        views.QuestionnaireEditView.as_view(url_namespace=__package__),
        name='questionnaire_edit'),
    url(r'^edit/(?P<identifier>[^/]+)/(?P<step>\w+)/$',
        views.QuestionnaireStepView.as_view(url_namespace=__package__),
        name='questionnaire_new_step'),
    url(r'^search/links/$',
        views.QuestionnaireLinkSearchView.as_view(configuration_code=__package__),
        name='questionnaire_link_search'),
    url(r'^list/$',
        views.QuestionnaireListView.as_view(configuration_code=__package__),
        name='questionnaire_list'),
    url(r'^list_partial/$',
        views.QuestionnaireListView.as_view(configuration_code=__package__),
        name='questionnaire_list_partial'),
]
