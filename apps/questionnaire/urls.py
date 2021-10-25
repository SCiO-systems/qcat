from django.urls import include, path
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^upload/$',
        views.generic_file_upload,
        name='file_upload'),
    url(r'^file/(?P<action>\w+)/(?P<uid>[^/]+)/$',
        views.generic_file_serve,
        name='file_serve'),
    url(r'^edit/(?P<identifier>[^/]+)/lock/$',
        views.QuestionnaireLockView.as_view(),
        name='lock_questionnaire'),
    path('', include(('apps.sample.urls', 'sample'), namespace='sample')),
]
