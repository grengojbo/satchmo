from django import template
from satchmo.shop.templatetags import get_filter_args

register = template.Library()

@register.inclusion_tag('contact/_order_details.html', takes_context=True)
def order_details(context, order, default_view_tax=False):
    """Output a formatted block giving order details."""
    return {'order' : order,
        'default_view_tax' : default_view_tax,
        'request' : context['request']
    }

@register.inclusion_tag('contact/_order_tracking_details.html')
def order_tracking_details(order, paylink=False):
    """Output a formatted block giving order tracking details."""
    return {'order' : order,
        'paylink' : paylink }

@register.filter
def order_variable(order, args):
    """
    Get a variable from an order

    Sample usage::

      {{ order|order_variable:'variable' }}

    """
    args, kwargs = get_filter_args(args)
    args = token.split_contents()
    if not len(args == 1):
        raise template.TemplateSyntaxError("%r filter expected variable, got: %s" % (args[0], args))

    return order.get_variable(args[0])
    
# @register.filter
# def giftcertificate(order):
#     """Get the giftcertificate from the order, if any"""
#     try:
#         return GiftCertificate.objects.from_order(order)
#     except GiftCertificate.DoesNotExist:
#         pass
#             
#     return None