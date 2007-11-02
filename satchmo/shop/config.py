from satchmo.configuration import config_register, BooleanValue, StringValue, MultipleStringValue, SHOP_GROUP, ConfigurationGroup
from django.utils.translation import ugettext_lazy as _

#### SHOP Group ####

CURRENCY = config_register(
    StringValue(SHOP_GROUP, 
        'CURRENCY', 
        description= _("Default currency symbol"), 
        default="$"))

ENABLE_RATINGS = config_register(
    BooleanValue(SHOP_GROUP, 
        'RATINGS', 
        description= _("Enable product ratings"), 
        default=True))
        
#### Google Group ####

GOOGLE_GROUP = ConfigurationGroup('GOOGLE', 'Google Settings')

GOOGLE_ANALYTICS = config_register(
    BooleanValue(GOOGLE_GROUP, 
        'ANALYTICS', 
        description= _("Enable Analytics"), 
        default=False,
        ordering=0))
        
GOOGLE_ANALYTICS_CODE = config_register(
    StringValue(GOOGLE_GROUP, 
        'ANALYTICS_CODE', 
        description= _("Analytics Code"), 
        default = "",
        ordering=5,
        requires = GOOGLE_ANALYTICS))
    
GOOGLE_ADWORDS = config_register(
    BooleanValue(GOOGLE_GROUP, 
        'ADWORDS', 
        description= _("Enable Conversion Tracking"), 
        default=False,
        ordering=10))
        
GOOGLE_ADWORDS_ID = config_register(
    StringValue(GOOGLE_GROUP, 
        'ADWORDS_ID', 
        description= _("Adwords ID (ex: UA-abcd-1)"), 
        default = "",
        ordering=15,
        requires = GOOGLE_ADWORDS))

