from django.conf.urls.defaults import *

urlpatterns = patterns('satchmo.product',
    (r'^view/recent/$', 'filterviews.display_recent', {}, 'satchmo_product_recently_added'),
    (r'^view/bestrated/$', 'filterviews.display_bestratings', {}, 'satchmo_product_best_rated'),
    (r'^view/bestsellers/$', 'filterviews.display_bestsellers', {}, 'satchmo_product_best_selling'),
    (r'^(?P<product_slug>[-\w]+)/$', 'views.get_product', {}, 'satchmo_product'),
    (r'^(?P<product_slug>[-\w]+)/prices/$', 'views.get_price', {}, 'satchmo_product_prices'),
    (r'^(?P<product_slug>[-\w]+)/price_detail/$', 'views.get_price_detail', {}, 'satchmo_product_price_detail'),
    (r'^inventory/edit/$', 'adminviews.edit_inventory', {}, 'satchmo_admin_edit_inventory'),
    (r'^inventory/export/$', 'adminviews.export_products', {}, 'satchmo_admin_product_export'),
    (r'^inventory/import/$', 'adminviews.import_products', {}, 'satchmo_admin_product_import'),
    (r'^inventory/report/$', 'adminviews.product_active_report', {}, 'satchmo_admin_product_report'),
    (r'^admin/(?P<product_slug>[-\w]+)/variations/$', 'adminviews.variation_manager', {}, 'satchmo_admin_variation_manager'),
    (r'^admin/variations/$', 'adminviews.variation_list', {}, 'satchmo_admin_variation_list'),
)
