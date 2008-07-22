from django import template
from django.db import models
from satchmo.contact.models import Order
from satchmo.contact.models import ORDER_STATUS

register = template.Library()

def orders_at_status(status):
    return Order.objects.filter(status=status)

def pending_order_list():
    """Returns a formatted list of pending orders"""
    pending = unicode(ORDER_STATUS[1][1])
    orders = orders_at_status(pending)
    
    return {
        'orders' : orders
    }

register.inclusion_tag('admin/_ordercount_list.html')(pending_order_list)

def inprocess_order_list():
    """Returns a formatted list of in-process orders"""
    inprocess = unicode(ORDER_STATUS[2][1])
    orders = orders_at_status(inprocess)
    
    return {
        'orders' : orders
    }

register.inclusion_tag('admin/_ordercount_list.html')(inprocess_order_list)
