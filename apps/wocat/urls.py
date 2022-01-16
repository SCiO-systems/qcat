from django.urls import include, path
from django.conf.urls import url
from django.views.generic import TemplateView

from apps.questionnaire.views import QuestionnaireListView, QuestionnaireFilterView

urlpatterns = [
    url(r'^$',
        TemplateView.as_view(template_name='wocat/home.html'),
        name='home'),
    url(r'^help/questionnaire/$',
        TemplateView.as_view(template_name='wocat/help/questionnaire_introduction.html'),
        name='help_questionnaire_introduction'),
    url(r'^faq/$',
        TemplateView.as_view(template_name='wocat/faq.html'),
        name='faq'),
    url(r'^add/$',
        TemplateView.as_view(template_name='wocat/add.html'),
        name='add'),
    url(r'^list/$',
        QuestionnaireListView.as_view(configuration_code=__package__),
        name='questionnaire_list'),
    url(r'^list_partial/$',
        QuestionnaireListView.as_view(configuration_code=__package__),
        name='questionnaire_list_partial'),
    url(r'^filter/$',
        QuestionnaireFilterView.as_view(
        configuration_code=__package__), name='questionnaire_filter'),
    url(r'^filter_partial/$',
        QuestionnaireFilterView.as_view(configuration_code=__package__),
        name='questionnaire_filter_partial'),
    path('', include(('apps.accounts.urls', 'accounts'), namespace='accounts')),
    path('', include(('apps.sample.urls', 'sample'), namespace='sample')),
    path('', include(('apps.api.urls.v1', 'v1'), namespace='v1')),
    path('', include(('apps.samplemulti.urls', 'samplemulti'), namespace='samplemulti')),
    path('', include(('apps.samplemodule.urls', 'samplemodule'), namespace='samplemodule')),
]
