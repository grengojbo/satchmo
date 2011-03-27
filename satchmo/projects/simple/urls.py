from django.conf.urls.defaults import *

from satchmo_store.urls import urlpatterns

urlpatterns += patterns('',
    (r'^grappelli/', include('grappelli.urls')),
    (r'test/', include('simple.localsite.urls'))
)
