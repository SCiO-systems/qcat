from django.conf.urls import url

from apps.questionnaire import views

from . import views as samplemodule_views


urlpatterns = [
    url(r'^view/(?P<identifier>[^/]+)/$',
        views.QuestionnaireView.as_view(url_namespace=__package__),
        name='questionnaire_details'),
    url(r'^view/(?P<identifier>[^/]+)/(?P<step>\w+)/$',
        samplemodule_views.questionnaire_view_step,
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
]
