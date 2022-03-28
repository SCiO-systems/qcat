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
    url(r'^geo/',
        views.get_places,
        name='slm_places'),
    url(r'^update/',
        views.get_places,
        name='update_slm_places'),
    path('', include(('apps.sample.urls', 'sample'), namespace='sample')),
]
