from django.conf.urls import url

from apps.configuration import views as configuration_views
from . import views


urlpatterns = [
    url(r'^admin/$', views.admin, name='admin'),
    url(r'^delete/$', views.delete_all, name='delete_all'),
    url(r'^delete/(?P<configuration>\w+)/(?P<edition>\w+)/$',
        views.delete_one,
        name='delete_one'),
    url(r'^index/(?P<configuration>\w+)/(?P<edition>\w+)/$',
        views.index,
        name='index'),
    url(r'^update/(?P<configuration>\w+)/(?P<edition>\w+)/$',
        views.update,
        name='update'),
    # This does not necessarily belong here
    url(r'^cache/delete/$',
        configuration_views.delete_caches,
        name='delete_caches'),
    url(r'^cache/build/$',
        configuration_views.BuildAllCachesView.as_view(),
        name='build_caches'),
    url(r'^value/$',
        views.FilterValueView.as_view(),
        name='filter_value'),
]

