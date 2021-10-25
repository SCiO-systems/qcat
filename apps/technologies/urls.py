from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from apps.questionnaire import views

from . import views as technologies_views


urlpatterns = [
    # The 'home' route points to the list
    url(r'^view/(?P<identifier>[^/]+)/$',
        views.QuestionnaireView.as_view(url_namespace=__package__),
        name='questionnaire_details'),
    url(r'^view/permalink/(?P<pk>[^/]+)/$',
        views.QuestionnairePermaView.as_view(url_namespace=__package__),
        name='questionnaire_permalink'),
    url(r'^view/(?P<identifier>[^/]+)/map/$',
        views.QuestionnaireMapView.as_view(url_namespace=__package__),
        name='questionnaire_view_map'),
    url(r'^view/(?P<identifier>[^/]+)/(?P<step>\w+)/$',
        technologies_views.questionnaire_view_step,
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
    url(r'^add_module/$',
        login_required(TemplateView.as_view(template_name="technologies/add_module.html")),
        name='add_module'),
    url(r'^add_module_action/$',
        views.QuestionnaireAddModule.as_view(url_namespace=__package__),
        name='add_module_action'),
    url(r'^check_modules/$',
        views.QuestionnaireCheckModulesView.as_view(),
        name='check_modules')
]
