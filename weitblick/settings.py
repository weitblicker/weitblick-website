"""
Django settings for weitblick project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""
from django.utils.translation import gettext_lazy as _
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+k(vot$ur$u-anq(+u-35=ves6(luzr$q+uwv+5!gn$(mk05ms'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["new.weitblicker.org", "new.weitblick.ngo", "new.weitblick.ong", 'localhost', '127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django_countries',
    'schedule',
    'sass_processor',
    'martor',
    'tinymce',
    'photologue',
    'sortedm2m',
    'rest_framework',
    'rest_framework.authtoken',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_auth',
    'rest_auth.registration',
    'haystack',
    'elasticsearch',
    'localflavor',
    'django_google_maps',
    'microsoft_auth',
    'wbcore.apps.WbcoreConfig',
    'form_designer',
    'admin_ordering',
    'el_pagination',
    'rules',
    'django_instagram',
    'django.contrib.humanize',
    'captcha',
    'honeypot',
    'easy_thumbnails',
    'location_field.apps.DefaultConfig',
    'django_cleanup.apps.CleanupConfig',  # should be at the bottom
]

AUTH_USER_MODEL = 'wbcore.User'

ADMINS = [('Sebastian Pütz', 'sebastian.puetz@weitblicker.org')]

EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT')) if os.environ.get('EMAIL_PORT') is not None else None
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_USE_TLS = True

PHOTOLOGUE_DIR = 'images'

def get_storage_path(instance, filename):
    fn = filename.lower()
    if hasattr(instance, 'type'):
        dir = instance.type
        return os.path.join(PHOTOLOGUE_DIR, dir, fn)

    return os.path.join(PHOTOLOGUE_DIR, 'photos', fn)


PHOTOLOGUE_PATH = get_storage_path

SUMMERNOTE_THEME = 'bs4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'weitblick.urls'

import markdown_fenced_code_tabs

from photologue import PHOTOLOGUE_APP_DIR
TEMPLATE_DIRS = [PHOTOLOGUE_APP_DIR,  markdown_fenced_code_tabs]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['markdown_fenced_code_tabs'],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'microsoft_auth.context_processors.microsoft',
                'django.template.context_processors.request',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

WSGI_APPLICATION = 'weitblick.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'weitblick_website',
        'USER': 'weitblick_website',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}
'''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


AUTHENTICATION_BACKENDS = [
    'rules.permissions.ObjectPermissionBackend',
    'microsoft_auth.backends.MicrosoftAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

MICROSOFT_AUTH_CLIENT_ID = '461a1fd8-9c6d-42b1-a74f-5dcdb912d89d'
MICROSOFT_AUTH_CLIENT_SECRET = '-Klk0zF]9EIxDG6@s7gMwM/v:ha.cB2]'
MICROSOFT_AUTH_LOGIN_TYPE = 'ma'

MARTOR_ENABLE_CONFIGS = {
    'imgur': 'true',     # to enable/disable imgur/custom uploader.
    'mention': 'false',  # to enable/disable mention
    'jquery': 'true',    # to include/revoke jquery (require for admin default django)
    'living': 'true',   # to enable/disable live updates in preview
    'spellcheck': 'false',  # to enable/disable spellcheck in form textareas
}

MARTOR_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',
    'markdown.extensions.nl2br',
    'markdown.extensions.smarty',
    'markdown.extensions.fenced_code',
    # Custom markdown extensions.
    'wbcore.markdown.content_image',
    'wbcore.markdown.content_tabs',
    'martor.extensions.urlize',
    'martor.extensions.del_ins',    # ~~strikethrough~~ and ++underscores++
    'martor.extensions.mention',    # to parse markdown mention
    'martor.extensions.emoji',      # to parse markdown emoji
    'martor.extensions.mdx_video',  # to parse embed/iframe video
]

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False

MARTOR_MARKDOWN_EXTENSION_CONFIGS = {
    'markdown_fenced_code_tabs': {
        'single_block_as_tab': False,
        'active_class': 'active',
        'template': 'default',
    },
    'martor.extensions.mdx_video': {
        'youtube_nocookie': True
    }
}

import time
MARTOR_UPLOAD_PATH = 'images/uploads/{}'.format(time.strftime("%Y/%m/%d/"))
MARTOR_UPLOAD_URL = '/rest/upload/'  # change to local uploader

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = (
    ('de', _('German')),
    ('en', _('English')),
    ('fr', _('French')),
    ('es', _('Spanish')),
)
MODELTRANSLATION_LANGUAGES = ('de', 'en', 'fr', 'es')
MODELTRANSLATION_DEFAULT_LANGUAGE = 'de'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
ENV_PATH = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(ENV_PATH, 'media/')

# Maximum Upload Image
# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 50MB - 5242880
# 100MB 104857600
# 250MB - 214958080
# 500MB - 429916160
MAX_IMAGE_UPLOAD_SIZE = 5242880  # 5MB

LOCAL_STATIC_ROOT = os.path.join(ENV_PATH, 'static/')
SERVER_STATIC_ROOT = '/var/www/weitblick-new/static/'
STATIC_ROOT = LOCAL_STATIC_ROOT if DEBUG else SERVER_STATIC_ROOT

LOCALE_PATH = os.path.join(ENV_PATH, 'locale/')
SASS_PROCESSOR_ROOT = STATIC_ROOT
SITE_ID=1 #has fixed 'site not found' error when accessing admin page

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ]
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}

GOOGLE_MAPS_API_KEY = 'AIzaSyCtEff9Z-Kl_nRc5GU28LvwzXFlz-6ltHc'

REST_AUTH_SERIALIZERS = {
  'USER_DETAILS_SERIALIZER': 'wbcore.serializers.UserSerializer',
}

CAPTCHA_LENGTH = 6
CAPTCHA_LETTER_ROTATION = (-50, 50)
HONEYPOT_FIELD_NAME = "phone"

THUMBNAIL_ALIASES = {
    '': {
        'profile_list_view': {'size': (48, 48), 'crop': ','},
        'profile_post_view': {'size': (52, 52), 'crop': ','},
        'profile_team_members': {'size': (300, 300), 'crop': ','},
        'partner_logo_list_view': {'size': (350, 248), 'background': '#FFFFFF'}
    },
}

LOCATION_FIELD = {
    'map.provider': 'openstreetmap',
    'map.zoom': 5,
    'provider.openstreetmap.max_zoom': 18,
    'search.provider': 'nominatim',
    'resources.root_path': '/static/location_field',
    'resources.media': {
        'js': [
            'custom_map_widget/form.js'
        ]}
}