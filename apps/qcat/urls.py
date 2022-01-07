from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from . import views


# The following urls are created with the locale as prefix, eg.
urlpatterns = [
    url(r'^about/$', views.about, name='about'),
    url(r'^about/imprint/$',
        TemplateView.as_view(template_name='qcat/imprint.html'),
        name='imprint'),
    url(r'^about/terms-of-agreement/$',
        TemplateView.as_view(template_name='qcat/terms-of-agreement.html'),
        name='terms-of-agreement'),
    url(r'^about/privacy-policy/$',
        TemplateView.as_view(template_name='qcat/privacy-policy.html'),
        name='privacy-policy'),
    url(r'^admin/login/?$', views.AdminLoginView.as_view(), name='admin:login'),
    # url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': views.static_sitemap},
        name='django.contrib.sitemaps.views.sitemap'),
    url(r'^robots\.txt', TemplateView.as_view(template_name='robots.txt'))
]
# en/questionnaire
urlpatterns += i18n_patterns(
    url(r'^$', RedirectView.as_view(
        url=reverse_lazy('wocat:home'),
        permanent=False
    ), name='home'),
    url(r'^accounts/', include(('apps.accounts.urls','accounts'),namespace='accounts')),
    url(r'^api/', include(('apps.api.urls','api'),namespace='api')),
    url(r'^configuration', include(('apps.configuration.urls','configuration'), namespace='configuration')),
    url(r'^notifications/', include('apps.notifications.urls')),
    url(r'^qcat/facts_teaser', views.FactsTeaserView.as_view(), name='facts_teaser'),
    url(r'^questionnaire/', include('apps.questionnaire.urls')),
    url(r'^search/', include(('apps.search.urls','search'), namespace='search')),
    url(r'^samplemulti/', include(('apps.samplemulti.urls','search'), namespace='samplemulti')),
    url(r'^summary/', include('apps.summary.urls')),
    url(r'^unccd/', include(('apps.unccd.urls','unccd'), namespace='unccd')),
    url(r'^wocat/', include(('apps.wocat.urls','wocat'), namespace='wocat')),
    url(r'^wocat/approaches/', include(('apps.approaches.urls','approaches'),
        namespace='approaches')),
    url(r'^wocat/cca/', include(('apps.cca.urls','cca'), namespace='cca')),
    url(r'^wocat/cbp/', include(('apps.cbp.urls','cbp'), namespace='cbp')),
    url(r'^wocat/technologies/', include(('apps.technologies.urls','technologies'),
        namespace='technologies')),
    url(r'^wocat/watershed/', include(
        ('apps.watershed.urls','watershed'), namespace='watershed')),
)

if settings.DEBUG:
    urlpatterns += i18n_patterns(
        # url(r'^sample/', include(('apps.sample.urls','sample'), namespace='sample')),
        # url(r'^samplemulti/', include(('apps.samplemulti.urls','samplemulti'),
        #     namespace='samplemulti')),
        url(r'^samplemodule/',
            include(('apps.samplemodule.urls','samplemodule'), namespace='samplemodule')),
        url(r'^404/', TemplateView.as_view(template_name='404.html')),
        url(r'^500/', TemplateView.as_view(template_name='500.html')),
        url(r'^503/', TemplateView.as_view(template_name='503.html')),
    ) + static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
