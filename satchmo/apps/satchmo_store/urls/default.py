from django.conf import settings
from django.conf.urls.defaults import patterns, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import logging
import os

log = logging.getLogger('satchmo_store.urls')

# discover all admin modules - if you override this for your
# own base URLs, you'll need to autodiscover there.
admin.autodiscover()

urlpatterns = getattr(settings, 'URLS', [])

adminpatterns = patterns('',
     (r'^admin/', include(admin.site.urls)),
)

if urlpatterns:
    urlpatterns += adminpatterns
else:
    urlpatterns = adminpatterns

#The following is used to serve up local media files like images
if getattr(settings, 'LOCAL_DEV', False):
    log.debug("Adding local serving of static files at: %s", settings.STATIC_ROOT)
    log.debug("Adding local serving of media files at: %s", settings.MEDIA_ROOT)
    baseurlregex = r'^static/(.*)$'
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('',
        #(baseurlregex, 'django.views.static.serve',
        #{'document_root':  settings.MEDIA_ROOT}),

        (r'^media/(.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
    )


