from decimal import Decimal
from datetime import datetime
from satchmo.contact.models import OrderPayment
import logging

log = logging.getLogger('payment.common.utils')

NOTSET = object()

def create_pending_payment(order, config, amount=NOTSET):
    """Create a placeholder payment entry for the order.  
    This is done by step 2 of the payment process."""
    key = unicode(config.KEY.value)
    if amount == NOTSET:
        amount = Decimal("0.00")
        
    log.debug("Creating pending payment for %s", order)
        
    orderpayment = OrderPayment(order=order, amount=amount, payment=key, 
        transaction_id="PENDING")
    orderpayment.save()

    return orderpayment

def record_payment(order, config, amount=NOTSET, transaction_id=""):
    """Convert a pending payment into a real payment."""
    key = unicode(config.KEY.value)
    if amount == NOTSET:
        amount = order.balance
        
    log.debug("Recording %s payment of %s for %s", key, amount, order)
    payments = order.payments.filter(transaction_id__exact="PENDING", 
        payment__exact=key)
    ct = payments.count()
    if ct == 0:
        log.debug("No pending %s payments for %s", key, order)
        orderpayment = OrderPayment(order=order, amount=amount, payment=key,
            transaction_id=transaction_id)
    
    else:
        orderpayment = payments[0]
        orderpayment.amount = amount
        orderpayment.transaction_id = transaction_id

        if ct > 1:
            for payment in payments[1:len(payments)]:
                payment.transaction_id="ABORTED"
                payment.save()
            
    orderpayment.timestamp = datetime.now()
    orderpayment.save()
    
    if order.paid_in_full:
        order.order_success()
    
    return orderpayment
