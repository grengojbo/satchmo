from decimal import Decimal
from django import template
from satchmo import tax
from satchmo.l10n.utils import moneyfmt
from satchmo.shop.templatetags import get_filter_args
import logging

log = logging.getLogger('satchmo.tax.templatetags')

try:
    from threading import local
except ImportError:
    log.warn('getting threadlocal support from django')
    from django.utils._threading_local import local

_threadlocals = local()

def set_thread_variable(key, var):
    setattr(_threadlocals, key, var)
    
def get_thread_variable(key, default):
    return getattr(_threadlocals, key, None)

register = template.Library()

def _get_taxprocessor(request):
    taxprocessor = get_thread_variable('taxer', None)
    if not taxprocessor:
        user = request.user
        if user.is_authenticated():
            user = user
        else:
            user = None

        taxprocessor = tax.get_processor(user=user)    
        set_thread_variable('taxer', taxprocessor)
        
    return taxprocessor

class CartitemLineTaxedTotalNode(template.Node):
    def __init__(self, cartitem, currency):
        self.cartitem = cartitem
        self.currency = currency

    def render(self, context):
        taxer = _get_taxprocessor(context['request'])
        try:
            item = template.resolve_variable(self.cartitem, context)
        except template.VariableDoesNotExist:
            raise tempalte.TemplateSyntaxError("No such variable: %s", self.cartitem)
        
        total = item.line_total + taxer.by_price(item.product.taxClass, item.line_total)
        if self.currency:
            return moneyfmt(total)
        return total

def cartitem_line_taxed_total(parser, token):
    """Returns the line total for the cartitem, with tax added.  If currency evaluates true,
    then return the total formatted through moneyfmt.
    Example: {% taxed_line_total cartitem [currency] %}
    """
    tokens = token.contents.split()
    if len(tokens) < 2:
        raise template.TemplateSyntaxError, "'%s' tag requires a cartitem argument" % tokens[0]

    return CartitemLineTaxedTotalNode(tokens[1], tokens[2])

class CartTaxedTotalNode(template.Node):
    def __init__(self, cart, currency):
        self.cart = cart
        self.currency = currency

    def render(self, context):
        taxer = _get_taxprocessor(context['request'])
        try:
            cart = template.resolve_variable(self.cart, context)
        except template.VariableDoesNotExist:
            raise tempalte.TemplateSyntaxError("No such variable: %s", self.cart)

        total = Decimal('0.00')
        for item in cart:
            total += item.line_total + taxer.by_price(item.product.taxClass, item.line_total)
        if self.currency:
            return moneyfmt(total)
        
        if currency:
            return moneyfmt(total)
        return total

def cart_taxed_total(parser, token):
    """Returns the line total for the cartitem, with tax added.  If currency evaluates true,
    then return the total formatted through moneyfmt.
    Example: {% taxed_line_total cartitem [currency] %}
    """
    tokens = token.contents.split()
    if len(tokens) < 2:
        raise template.TemplateSyntaxError, "'%s' tag requires a cart argument" % tokens[0]

    return CartTaxedTotalNode(tokens[1], tokens[2])

register.tag('cartitem_line_taxed_total', cartitem_line_taxed_total)
register.tag('cart_taxed_total', cart_taxed_total)
