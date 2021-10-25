"""
This module contains the URL routing patterns for the :mod:`accounts`
app.
"""
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^search/$', views.user_search, name='user_search'),
    url(r'^update/$', views.user_update, name='user_update'),
    url(r'^user/(?P<pk>\d+)/$', views.UserDetailView.as_view(), name='user_details'),
    url(r'^questionnaires/$',
        views.ProfileView.as_view(),
        name='account_questionnaires'
        ),
    url(r'^questionnaires/status/(?P<user_id>\d+)/$',
        views.PublicQuestionnaireListView.as_view(),
        name='questionnaires_public_list'
        ),
    url(r'^questionnaires/status/$',
        views.QuestionnaireStatusListView.as_view(),
        name='questionnaires_status_list'
        ),
    url(r'^questionnaires/search/$',
        views.QuestionnaireSearchView.as_view(),
        name='staff_questionnaires_search'
        ),

]
