from django.conf.urls import url

from apps.questionnaire import views

from . import views as cca_views


urlpatterns = [
    # The 'home' route points to the list
    url(r'^view/(?P<identifier>[^/]+)/$',
        views.QuestionnaireView.as_view(url_namespace=__package__),
        name='questionnaire_details'),
    url(r'^view/(?P<identifier>[^/]+)/map/$',
        views.QuestionnaireMapView.as_view(url_namespace=__package__),
        name='questionnaire_view_map'),
    url(r'^view/(?P<identifier>[^/]+)/(?P<step>\w+)/$',
        cca_views.questionnaire_view_step,
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
]
