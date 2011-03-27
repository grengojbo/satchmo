# Django settings for satchmo project.
# If you have an existing project, then ensure that you modify local_settings-customize.py
# and import it from your main settings file. (from local_settings import *)
import os

DIRNAME = os.path.dirname(__file__)

DJANGO_PROJECT = 'simple'
DJANGO_SETTINGS_MODULE = 'simple.settings'

ADMINS = (
     ('', ''),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'NAME': 'dbname',
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'username',
        'PASSWORD': 'passwd',
        'HOST': 'localhost',
        'PORT': '3306',
        #'OPTIONS': { "init_command": "SET FOREIGN_KEY_CHECKS = 0",},
    }
}

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'US/Pacific'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
#Image files will be stored off of this path
MEDIA_ROOT = os.path.normpath(os.path.join(DIRNAME, 'media/'))
STATIC_ROOT = os.path.normpath(os.path.join(DIRNAME, 'media/static/'))
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.normpath(os.path.join(DIRNAME, '../../static/')),
)
# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = '/media/'
ADMIN_MEDIA_PREFIX = STATIC_URL + "grappelli/"
ADMIN_MEDIA_ROOT = os.path.join(DIRNAME, 'media/static/grappelli/')

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.doc.XViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "threaded_multihost.middleware.ThreadLocalMiddleware",
    "satchmo_store.shop.SSLMiddleware.SSLRedirect",
    #"satchmo_ext.recentlist.middleware.RecentProductMiddleware",
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

#this is used to add additional config variables to each request
# NOTE: overridden in local_settings.py
# NOTE: If you enable the recent_products context_processor, you MUST have the
# 'satchmo_ext.recentlist' app installed.
TEMPLATE_CONTEXT_PROCESSORS = ('satchmo_store.shop.context_processors.settings',
                               'django.contrib.auth.context_processors.auth',
                               'django.core.context_processors.i18n',
                                'django.core.context_processors.media',
                                'django.core.context_processors.static',
                               #'satchmo_ext.recentlist.context_processors.recent_products',
                               )

#ROOT_URLCONF = 'satchmo.urls'
ROOT_URLCONF = 'simple.urls'

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.sites',
    'satchmo_store.shop',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.comments',
    'django.contrib.sessions',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'registration',
    'sorl.thumbnail',
    'south',
    'keyedcache',
    'livesettings',
    'l10n',
    'satchmo_utils.thumbnail',
    'satchmo_store.contact',
    'tax',
    'tax.modules.no',
    'tax.modules.area',
    'tax.modules.percent',
    #
    'shipping',
    #'satchmo_store.contact.supplier',
    #'shipping.modules.tiered',
    #'satchmo_ext.newsletter',
    #'satchmo_ext.recentlist',
    #'testimonials',         # dependency on  http://www.assembla.com/spaces/django-testimonials/
    'product',
    'product.modules.configurable',
    #'product.modules.custom',
    #'product.modules.downloadable',
    #'product.modules.subscription',
    #'satchmo_ext.product_feeds',
    #'satchmo_ext.brand',
    'payment',
    'payment.modules.dummy',
    'payment.modules.paypal',
    #'payment.modules.giftcertificate',
    #'satchmo_ext.wishlist',
    #'satchmo_ext.upsell',
    #'satchmo_ext.productratings',
    'satchmo_ext.satchmo_toolbar',
    'satchmo_utils',
    #'shipping.modules.tieredquantity',
    'django_extensions',    # dependency on  https://github.com/django-extensions/django-extensions/
    #'satchmo_ext.tieredpricing',
    #'typogrify',            # dependency on  http://code.google.com/p/typogrify/
    #'debug_toolbar',
    'app_plugins',
    'simple.localsite',
)

AUTHENTICATION_BACKENDS = (
    'satchmo_store.accounts.email-auth.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

#DEBUG_TOOLBAR_CONFIG = {
#    'INTERCEPT_REDIRECTS' : False,
#}

L10N_SETTINGS = {
}

#### Satchmo unique variables ####
#from django.conf.urls.defaults import patterns, include
SATCHMO_SETTINGS = {
    'SHOP_BASE' : '',
    'MULTISHOP' : False,
    #'SHOP_URLS' : patterns('satchmo_store.shop.views',)
}

SKIP_SOUTH_TESTS=True

# Load the local settings
from local_settings import *
