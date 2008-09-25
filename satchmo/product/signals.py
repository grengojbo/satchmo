"""Satchmo product signals

Signals:
 - `satchmo_price_query`: Usage::
    
    Usage: satchmo_price_query.send(self, product=product, price=price) 
    
 - `satchmo_order_success`
 
 - `index_prerender`
 
    Usage: index_prerender.send(Sender, request=request, context=ctx, object_list=somelist)
"""

import django.dispatch

satchmo_price_query = django.dispatch.Signal()
subtype_order_success = django.dispatch.Signal()
index_prerender = django.dispatch.Signal()
