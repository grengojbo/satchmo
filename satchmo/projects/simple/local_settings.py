# this is an extremely simple Satchmo standalone store.

import logging
import os, os.path

LOCAL_DEV = True
DEBUG = True
TEMPLATE_DEBUG = DEBUG

if LOCAL_DEV:
    INTERNAL_IPS = ('127.0.0.1',)

DIRNAME = os.path.dirname(os.path.abspath(__file__))

# trick to get the two-levels up directory, which for the "simple" project should be the satchmo dir
# for most "normal" projects, you should directly set the SATCHMO_DIRNAME, and skip the trick
_parent = lambda x: os.path.normpath(os.path.join(x, '..'))
SATCHMO_DIRNAME = _parent(_parent(DIRNAME))
    
TIME_ZONE = 'Europe/Kiev'
LANGUAGE_CODE = 'ru-ru'

gettext_noop = lambda s:s

LANGUAGE_CODE = 'en-us'
LANGUAGES = (
   ('en', gettext_noop('English')),
   ('ru', gettext_noop('Russian')),
)

# Only set these if Satchmo is part of another Django project
#These are used when loading the test data
SITE_NAME = "simple"
DJANGO_PROJECT = 'simple'
DJANGO_SETTINGS_MODULE = 'simple.settings'

# "simple" doesn't have any custom templates, usually you'd have one here for your site.
TEMPLATE_DIRS = (
    os.path.join(DIRNAME, "templates"),
)

DATABASES = {
    'default': {
        'NAME': os.path.join(DIRNAME, 'simple.db'),
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

SECRET_KEY = 'EXAMPLE SECRET KEY'

##### For Email ########
# If this isn't set in your settings file, you can set these here
#EMAIL_HOST = 'host here'
#EMAIL_PORT = 587
#EMAIL_HOST_USER = 'your user here'
#EMAIL_HOST_PASSWORD = 'your password'
#EMAIL_USE_TLS = True
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

#These are used when loading the test data
SITE_DOMAIN = "localhost"
SITE_NAME = "Simple Satchmo"

# not suitable for deployment, for testing only, for deployment strongly consider memcached.
CACHE_BACKEND = "locmem:///"
CACHE_TIMEOUT = 60*5
CACHE_PREFIX = "Z"

ACCOUNT_ACTIVATION_DAYS = 7

#Configure logging
LOGFILE = "satchmo.log"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

#fileLog = logging.FileHandler(os.path.join(DIRNAME, LOGFILE), 'w')
#fileLog.setLevel(logging.DEBUG)
# add the handler to the root logger
#logging.getLogger('').addHandler(fileLog)
LOGGING = {
  'version': 1,
  'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
  'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            #'filters': ['special']
        }
    },
  'loggers': {
#        'django': {
#            'handlers':['null'],
#            'propagate': True,
#            'level':'INFO',
#        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
            #'filters': ['special']
        },
        'keyedcache': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            #'filters': ['special']
        },
        'l10n': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            #'filters': ['special']
        }
    }
}
#logging.getLogger('keyedcache').setLevel(logging.INFO)
#logging.getLogger('l10n').setLevel(logging.INFO)
logging.info("Satchmo Started")
