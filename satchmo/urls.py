from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from satchmo.shop import get_satchmo_setting
from satchmo.shop.views.sitemaps import sitemaps

shop_base = get_satchmo_setting('SHOP_BASE')
if shop_base == '':
    shopregex = '^'
else:
    shopregex = '^' + shop_base[1:] + '/'

# discover all admin modules - if you override this for your
# own base URLs, you'll need to autodiscover there.
admin.autodiscover()

urlpatterns = getattr(settings, 'URLS', [])

urlpatterns += patterns('',
    (r'^admin/print/(?P<doc>[-\w]+)/(?P<id>\d+)', 'satchmo.shipping.views.displayDoc'),
    (r'^admin/product/configurableproduct/(?P<id>\d+)/getoptions/', 'satchmo.product.views.get_configurable_product_options'),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^accounts/', include('satchmo.accounts.urls')),
    (shopregex, include('satchmo.shop.urls')),
    (r'sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    (r'settings/', include('satchmo.configuration.urls')),
    (r'cache/', include('satchmo.caching.urls')),
)

#The following is used to serve up local media files like images
if settings.LOCAL_DEV:
    baseurlregex = r'^static/(?P<path>.*)$'
    urlpatterns += patterns('',
        (baseurlregex, 'django.views.static.serve',
        {'document_root':  settings.MEDIA_ROOT}),
    )

def remove_duplicate_urls(urls, names):
    """Remove any URLs whose names are already in use."""
    for pattern in urls:
        if hasattr(pattern, 'url_patterns'):
            remove_duplicate_urls(pattern.url_patterns, names)
        elif hasattr(pattern, 'name') and pattern.name:
            if pattern.name in names:
                urls.remove(pattern)
            else:
                names.append(pattern.name)

remove_duplicate_urls(urlpatterns, [])

