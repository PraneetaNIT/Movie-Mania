from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^movies/', include('movies.urls')),
)

if settings.DEBUG:
        urlpatterns += patterns(
                'django.views.static',
                (r'media/(?P<path>.*)',
                'serve',
                {'document_root': settings.MEDIA_ROOT}), )

# /usr/local/lib/python2.7/dist-packages/django/contrib/auth/views.py
# Anita  (amit) ----   +919829356969
# J@home (Jatin) ----- 07820834476
# m...  ---------- +919667370614
# khelu(Kanav) ---------- +918952882438
