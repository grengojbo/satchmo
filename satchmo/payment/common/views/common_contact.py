####################################################################
# First step in the order process - capture all the demographic info
#####################################################################

from django import http
from django.shortcuts import render_to_response
from django.template import RequestContext
from satchmo.configuration import config_get_group, config_value
from satchmo.contact.common import get_area_country_options
from satchmo.contact.models import Contact
from satchmo.payment.common.forms import PaymentContactInfoForm
from satchmo.shop.models import Cart
from satchmo.utils.dynamic import lookup_url

def contact_info(request):
    """View which collects demographic information from customer."""

    #First verify that the cart exists and has items
    tempCart = Cart.objects.from_request(request)
    if tempCart.numItems == 0:
        return render_to_response('checkout/empty_cart.html', RequestContext(request))

    init_data = {}
    areas, countries, only_country = get_area_country_options(request)
    if request.user.is_authenticated():
        if request.user.email:
            init_data['email'] = request.user.email
        if request.user.first_name:
            init_data['first_name'] = request.user.first_name
        if request.user.last_name:
            init_data['last_name'] = request.user.last_name
    try:
        contact = Contact.objects.from_request(request, create=False)
    except Contact.DoesNotExist:
        contact = None

    if request.method == "POST":
        new_data = request.POST.copy()
        if not tempCart.is_shippable:
            new_data['copy_address'] = True
        form = PaymentContactInfoForm(countries, areas, contact, new_data, shippable=tempCart.is_shippable, 
            initial=init_data)

        if form.is_valid():
            if contact is None and request.user:
                contact = Contact(user=request.user)
            custID = form.save(contact=contact, update_newsletter=False)
            request.session['custID'] = custID
            #TODO - Create an order here and associate it with a session
            modulename = 'PAYMENT_' + new_data['paymentmethod']
            paymentmodule = config_get_group(modulename)
            url = lookup_url(paymentmodule, 'satchmo_checkout-step2')
            return http.HttpResponseRedirect(url)
    else:
        if contact:
            #If a person has their contact info, make sure we populate it in the form
            for item in contact.__dict__.keys():
                init_data[item] = getattr(contact,item)
            if contact.shipping_address:
                for item in contact.shipping_address.__dict__.keys():
                    init_data["ship_"+item] = getattr(contact.shipping_address,item)
            if contact.billing_address:
                for item in contact.billing_address.__dict__.keys():
                    init_data[item] = getattr(contact.billing_address,item)
            if contact.primary_phone:
                init_data['phone'] = contact.primary_phone.phone
        else:
            # Allow them to login from this page.
            request.session.set_test_cookie()
        form = PaymentContactInfoForm(countries, areas, contact, shippable=tempCart.is_shippable, initial=init_data)

    context = RequestContext(request, {
        'form': form,
        'country': only_country,
        'paymentmethod_ct': len(config_value('PAYMENT', 'MODULES'))
        })
    return render_to_response('checkout/form.html', context)

