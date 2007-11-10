####################################################################
# Last step in the order process - confirm the info and process it
#####################################################################

from django.core import urlresolvers
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from satchmo.contact.models import Order
from satchmo.payment.common.pay_ship import send_order_confirmation
from satchmo.payment.urls import lookup_url, lookup_template
from satchmo.shop.models import Cart
import logging

log = logging.getLogger('satchmo.payment.common.views')

def credit_confirm_info(request, payment_module, custom_confirm_template='checkout/confirm.html'):
    """A view which shows and requires credit card selection"""
    if not request.session.get('orderID'):
        url = urlresolvers.reverse('satchmo_checkout-step1')
        return HttpResponseRedirect(url)

    if request.session.get('cart'):
        tempCart = Cart.objects.get(id=request.session['cart'])
        if tempCart.numItems == 0:
            template = lookup_template(payment_module, 'checkout/empty_cart.html')
            return render_to_response(template, RequestContext(request))
    else:
        template = lookup_template(payment_module, 'checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))

    orderToProcess = Order.objects.get(id=request.session['orderID'])

    # Check if the order is still valid
    if not orderToProcess.validate(request):
        context = RequestContext(request,
            {'message': _('Your order is no longer valid.')})
        return render_to_response('shop_404.html', context)

    if request.POST:
        #Do the credit card processing here & if successful, empty the cart and update the status
        credit_processor = payment_module.MODULE.load_module('processor')
        processor = credit_processor.PaymentProcessor(payment_module)
        processor.prepareData(orderToProcess)
        results, reason_code, msg = processor.process()
        
        log.info("""Processing credit card transaction with %s
Order #%i
Results=%s
Response=%s
Reason=%s""", payment_module.key, orderToProcess.id, results, reason_code, msg)

        if results:
            tempCart.empty()
            #Update status
            
            orderToProcess.add_status(status='Pending', notes = "Order successfully submitted")

            send_order_confirmation(orderToProcess)
            
            #Redirect to the success page
            url = lookup_url(payment_module, 'satchmo_checkout-success')
            return HttpResponseRedirect(url)
        #Since we're not successful, let the user know via the confirmation page
        else:
            errors = msg
    else:
        errors = ''

    template = lookup_template(payment_module, custom_confirm_template)
    context = RequestContext(request, {
        'order': orderToProcess,
        'errors': errors,
        'checkout_step2': lookup_url(payment_module, 'satchmo_checkout-step2')})
    return render_to_response(template, context)
