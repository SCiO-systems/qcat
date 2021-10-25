from django.conf.urls import url

from .views import EditionNotesView


urlpatterns = [
    # The 'home' route points to the list
    url(r'^$', EditionNotesView.as_view(), name='release_notes'),
]
