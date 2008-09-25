"""Satchmo product signals

Signals:
 - `index_prerender`

   Usage: index_prerender.send(Sender, request=request, context=ctx, object_list=somelist)
   
 - `satchmo_price_query`: Usage::
    
    Usage: satchmo_price_query.send(self, product=product, price=price) 
    
 - `satchmo_order_success`
"""

import django.dispatch

index_prerender = django.dispatch.Signal()
satchmo_price_query = django.dispatch.Signal()
subtype_order_success = django.dispatch.Signal()
