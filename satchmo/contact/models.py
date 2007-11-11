"""
Stores customer, organization, and order information.
"""

from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from satchmo.configuration import config_choice_values, config_value, SettingNotSet
from satchmo.discount.models import Discount
from satchmo.payment.config import payment_choices
from satchmo.product.models import Product, DownloadableProduct
from satchmo.shop.templatetags.satchmo_currency import moneyfmt
from satchmo.shop.utils import load_module
from satchmo import tax
import config
import datetime
import logging
import operator
import satchmo.shipping.config
import sys
from django.db.models import permalink
from django.core import urlresolvers
from django.contrib.sites.models import Site

log = logging.getLogger('contact.views')

CONTACT_CHOICES = (
    ('Customer', _('Customer')),
    ('Supplier', _('Supplier')),
    ('Distributor', _('Distributor')),
)

ORGANIZATION_CHOICES = (
    ('Company', _('Company')),
    ('Government', _('Government')),
    ('Non-profit', _('Non-profit')),
)

ORGANIZATION_ROLE_CHOICES = (
    ('Supplier', _('Supplier')),
    ('Distributor', _('Distributor')),
    ('Manufacturer', _('Manufacturer')),
)

class Organization(models.Model):
    """
    An organization can be a company, government or any kind of group.
    """
    name = models.CharField(_("Name"), max_length=50, core=True)
    type = models.CharField(_("Type"), max_length=30,
        choices=ORGANIZATION_CHOICES)
    role = models.CharField(_("Role"), max_length=30,
        choices=ORGANIZATION_ROLE_CHOICES)
    create_date = models.DateField(_("Creation Date"))
    notes = models.TextField(_("Notes"), max_length=200, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def save(self):
        """Ensure we have a create_date before saving the first time."""
        if not self.id:
            self.create_date = datetime.date.today()
        super(Organization, self).save()

    class Admin:
        list_filter = ['type', 'role']
        list_display = ['name', 'type', 'role']

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

class Contact(models.Model):
    """
    A customer, supplier or any individual that a store owner might interact
    with.
    """
    first_name = models.CharField(_("First name"), max_length=30, core=True)
    last_name = models.CharField(_("Last name"), max_length=30, core=True)
    user = models.ForeignKey(User, unique=True, blank=True, null=True,
        edit_inline=models.TABULAR, num_in_admin=1, min_num_in_admin=1,
        max_num_in_admin=1, num_extra_on_change=0)
    role = models.CharField(_("Role"), max_length=20, blank=True, null=True,
        choices=CONTACT_CHOICES)
    organization = models.ForeignKey(Organization, verbose_name=_("Organization"), blank=True, null=True)
    dob = models.DateField(_("Date of birth"), blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True)
    notes = models.TextField(_("Notes"), max_length=500, blank=True)
    create_date = models.DateField(_("Creation date"))

    @classmethod
    def from_request(cls, request, create=False):
        """Get the contact from the session, else look up using the logged-in
        user. Create an unsaved new contact if `create` is true.

        Returns:
        - Contact object or None
        """
        contact = None
        if request.session.get('custID'):
            try:
                contact = cls.objects.get(id=request.session['custID'])
            except Contact.DoesNotExist:
                del request.session['custID']

        if contact is None and request.user.is_authenticated():
            try:
                contact = cls.objects.get(user=request.user.id)
                request.session['custID'] = contact.id
            except Contact.DoesNotExist:
                pass
        else:
            # Don't create a Contact if the user isn't authenticated.
            create = False

        if contact is None and create:
            contact = Contact(user=request.user)

        return contact

    def _get_full_name(self):
        """Return the person's full name."""
        return u'%s %s' % (self.first_name, self.last_name)
    full_name = property(_get_full_name)

    def _shipping_address(self):
        """Return the default shipping address or None."""
        try:
            return self.addressbook_set.get(is_default_shipping=True)
        except AddressBook.DoesNotExist:
            return None
    shipping_address = property(_shipping_address)

    def _billing_address(self):
        """Return the default billing address or None."""
        try:
            return self.addressbook_set.get(is_default_billing=True)
        except AddressBook.DoesNotExist:
            return None
    billing_address = property(_billing_address)

    def _primary_phone(self):
        """Return the default phone number or None."""
        try:
            return self.phonenumber_set.get(primary=True)
        except PhoneNumber.DoesNotExist:
            return None
    primary_phone = property(_primary_phone)

    def __unicode__(self):
        return self.full_name

    def save(self):
        """Ensure we have a create_date before saving the first time."""
        if not self.id:
            self.create_date = datetime.date.today()
        super(Contact, self).save()

    class Admin:
        list_display = ('last_name', 'first_name', 'organization', 'role')
        list_filter = ['create_date', 'role', 'organization']
        ordering = ['last_name']

    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

PHONE_CHOICES = (
    ('Work', _('Work')),
    ('Home', _('Home')),
    ('Fax', _('Fax')),
    ('Mobile', _('Mobile')),
)

INTERACTION_CHOICES = (
    ('Email', _('Email')),
    ('Phone', _('Phone')),
    ('In Person', _('In Person')),
)

class Interaction(models.Model):
    """
    A type of activity with the customer.  Useful to track emails, phone calls,
    or in-person interactions.
    """
    contact = models.ForeignKey(Contact, verbose_name=_("Contact"))
    type = models.CharField(_("Type"), max_length=30,choices=INTERACTION_CHOICES)
    date_time = models.DateTimeField(_("Date and Time"), core=True)
    description = models.TextField(_("Description"), max_length=200)

    def __unicode__(self):
        return u'%s - %s' % (self.contact.full_name, self.type)

    class Admin:
        list_filter = ['type', 'date_time']

    class Meta:
        verbose_name = _("Interaction")
        verbose_name_plural = _("Interactions")

class PhoneNumber(models.Model):
    """
    Phone number associated with a contact.
    """
    contact = models.ForeignKey(Contact, edit_inline=models.TABULAR,
        num_in_admin=1)
    type = models.CharField(_("Description"), choices=PHONE_CHOICES,
        max_length=20, blank=True)
    phone = models.CharField(_("Phone Number"), blank=True, max_length=12,
        core=True)
    primary = models.BooleanField(_("Primary"), default=False)

    def __unicode__(self):
        return u'%s - %s' % (self.type, self.phone)

    def save(self):
        """
        If this number is the default, then make sure that it is the only
        primary phone number. If there is no existing default, then make
        this number the default.
        """
        existing_number = self.contact.primary_phone
        if existing_number:
            if self.primary:
                existing_number.primary = False
                super(PhoneNumber, existing_number).save()
        else:
            self.primary = True
        super(PhoneNumber, self).save()

    class Meta:
        ordering = ['-primary']
        verbose_name = _("Phone Number")
        verbose_name_plural = _("Phone Numbers")

class AddressBook(models.Model):
    """
    Address information associated with a contact.
    """
    contact = models.ForeignKey(Contact,
        edit_inline=models.STACKED, num_in_admin=1)
    description = models.CharField(_("Description"), max_length=20, blank=True,
        help_text=_('Description of address - Home, Office, Warehouse, etc.',))
    street1 = models.CharField(_("Street"), core=True, max_length=50)
    street2 = models.CharField(_("Street"), max_length=50, blank=True)
    state = models.CharField(_("State"), max_length=50, blank=True)
    city = models.CharField(_("City"), max_length=50)
    postal_code = models.CharField(_("Zip Code"), max_length=10)
    country = models.CharField(_("Country"), max_length=50, blank=True)
    is_default_shipping = models.BooleanField(_("Default Shipping Address"),
        default=False)
    is_default_billing = models.BooleanField(_("Default Billing Address"),
        default=False)

    def __unicode__(self):
       return u'%s - %s' % (self.contact.full_name, self.description)

    def save(self):
        """
        If this address is the default billing or shipping address, then
        remove the old address's default status. If there is no existing
        default, then make this address the default.
        """
        existing_billing = self.contact.billing_address
        if existing_billing:
            if self.is_default_billing:
                existing_billing.is_default_billing = False
                super(AddressBook, existing_billing).save()
        else:
            self.is_default_billing = True

        existing_shipping = self.contact.shipping_address
        if existing_shipping:
            if self.is_default_shipping:
                existing_shipping.is_default_shipping = False
                super(AddressBook, existing_shipping).save()
        else:
            self.is_default_shipping = True

        super(AddressBook, self).save()

    class Meta:
        verbose_name = _("Address Book")
        verbose_name_plural = _("Address Books")

ORDER_CHOICES = (
    ('Online', _('Online')),
    ('In Person', _('In Person')),
    ('Show', _('Show')),
)

ORDER_STATUS = (
    ('Temp', _('Temp')),
    ('Pending', _('Pending')),
    ('In Process', _('In Process')),
    ('Billed', _('Billed')),
    ('Shipped', _('Shipped')),
)

class Order(models.Model):
    """
    Orders contain a copy of all the information at the time the order was
    placed.
    """
    contact = models.ForeignKey(Contact)
    ship_street1 = models.CharField(_("Street"), max_length=50, blank=True)
    ship_street2 = models.CharField(_("Street"), max_length=50, blank=True)
    ship_city = models.CharField(_("City"), max_length=50, blank=True)
    ship_state = models.CharField(_("State"), max_length=50, blank=True)
    ship_postal_code = models.CharField(_("Zip Code"), max_length=10, blank=True)
    ship_country = models.CharField(_("Country"), max_length=50, blank=True)
    bill_street1 = models.CharField(_("Street"), max_length=50, blank=True)
    bill_street2 = models.CharField(_("Street"), max_length=50, blank=True)
    bill_city = models.CharField(_("City"), max_length=50, blank=True)
    bill_state = models.CharField(_("State"), max_length=50, blank=True)
    bill_postal_code = models.CharField(_("Zip Code"), max_length=10, blank=True)
    bill_country = models.CharField(_("Country"), max_length=50, blank=True)
    notes = models.TextField(_("Notes"), max_length=100, blank=True, null=True)
    sub_total = models.DecimalField(_("Subtotal"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(_("Total"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    discount_code = models.CharField(_("Discount Code"), max_length=20, blank=True, null=True,
        help_text=_("Coupon Code"))
    discount = models.DecimalField(_("Discount amount"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    method = models.CharField(_("Order method"),
        choices=ORDER_CHOICES, max_length=50, blank=True)
    shipping_description = models.CharField(_("Shipping Description"),
        max_length=50, blank=True, null=True)
    shipping_method = models.CharField(_("Shipping Method"),
        max_length=50, blank=True, null=True)
    shipping_model = models.CharField(_("Shipping Models"),
        choices=config_choice_values('SHIPPING','MODULES'), max_length=30, blank=True, null=True)
    shipping_cost = models.DecimalField(_("Shipping Cost"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    tax = models.DecimalField(_("Tax"),
        max_digits=6, decimal_places=2, blank=True, null=True)
    timestamp = models.DateTimeField(_("Timestamp"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=ORDER_STATUS,
        core=True, blank=True, help_text=_("This is set automatically."))

    def __unicode__(self):
        return "Order #%s: %s" % (self.id, self.contact.full_name)

    def add_status(self, status=None, notes=None):
        orderstatus = OrderStatus()
        if not status:
            if self.orderstatus_set.count() > 0:                
                curr_status = self.orderstatus_set.all().order_by('-timestamp')[0]
                status = curr_status.status
            else:
                status = 'Pending'
        
        orderstatus.status = status
        orderstatus.notes = notes
        orderstatus.timestamp = datetime.datetime.now()
        orderstatus.order = self
        orderstatus.save()

    def copy_addresses(self):
        """
        Copy the addresses so we know what the information was at time of order.
        """
        shipaddress = self.contact.shipping_address
        billaddress = self.contact.billing_address
        self.ship_street1 = shipaddress.street1
        self.ship_street2 = shipaddress.street2
        self.ship_city = shipaddress.city
        self.ship_state = shipaddress.state
        self.ship_postal_code = shipaddress.postal_code
        self.ship_country = shipaddress.country
        self.bill_street1 = billaddress.street1
        self.bill_street2 = billaddress.street2
        self.bill_city = billaddress.city
        self.bill_state = billaddress.state
        self.bill_postal_code = billaddress.postal_code
        self.bill_country = billaddress.country

    def remove_all_items(self):
        """Delete all items belonging to this order."""
        for item in self.orderitem_set.all():
            item.delete()
        self.save()

    def _balance(self):
        payments = [p.amount for p in self.payments.all()]
        if payments:
            paid = reduce(operator.add, payments)
            return self.total - paid
        return self.total
        
    balance = property(fget=_balance)
    
    def balance_forward(self):
        return moneyfmt(self.balance)

    balance_forward = property(fget=balance_forward)
    
    def _credit_card(self):
        """Return the credit card associated with this payment."""
        for payment in self.payments.order_by('-timestamp'):
            try:
                if payment.creditcards.count() > 0:
                    return payment.creditcards.get()
            except payments.creditcards.model.DoesNotExist:
                pass
        return None
    credit_card = property(_credit_card)
    

    def _full_bill_street(self, delim="<br/>"):
        """Return both billing street entries separated by delim."""
        if self.bill_street2:
            return self.bill_street1 + delim + self.bill_street2
        else:
            return self.bill_street1
    full_bill_street = property(_full_bill_street)

    def _full_ship_street(self, delim="<br/>"):
        """Return both shipping street entries separated by delim."""
        if self.ship_street2:
            return self.ship_street1 + delim + self.ship_street2
        else:
            return self.ship_street1
    full_ship_street = property(_full_ship_street)

    def save(self):
        """
        Copy addresses from contact. If the order has just been created, set
        the create_date.
        """
        if not self.id:
            self.timestamp = datetime.datetime.now()

        self.copy_addresses()
        super(Order, self).save() # Call the "real" save() method.

    def invoice(self):
        return('<a href="/admin/print/invoice/%s/">View</a>' % self.id)
    invoice.allow_tags = True

    def packingslip(self):
        return('<a href="/admin/print/packingslip/%s/">View</a>' % self.id)
    packingslip.allow_tags = True
    
    def recalculate_total(self, save=True):
        """Calculates subtotal, taxes and total."""
        #Can't really do a full shipping recalc - shipping is bound to the cart. 
        
        discount_amount = Decimal("0.00")
        if self.discount_code:
            try:
                discount = Discount.objects.filter(code=self.discount_code)[0]
                if discount:
                    if discount.freeShipping:
                        self.shipping_cost = Decimal("0.00")
                    discount_amount = discount.calc(self)
                    
            except Discount.DoesNotExist:
                pass

        self.discount = discount_amount
        
        itemprices = [ item.line_item_price for item in self.orderitem_set.all() ]
        if itemprices:
            subtotal = reduce(operator.add, itemprices)
        else:
            subtotal = Decimal('0.00')
            
        self.sub_total = subtotal
        
        taxProcessor = tax.get_processor(self)
        self.tax = taxProcessor.process()
        
        log.debug("recalc: subtotal=%s, shipping=%s, discount=%s, tax=%s", 
                subtotal, self.shipping_cost, self.discount, self.tax)
        self.total = subtotal + self.shipping_cost - self.discount + self.tax
        
        if save:
            self.save()

    def shippinglabel(self):
        return('<a href="/admin/print/shippinglabel/%s/">View</a>' % self.id)
    shippinglabel.allow_tags = True

    def _order_total(self):
        #Needed for the admin list display
        return moneyfmt(self.total)
    order_total = property(_order_total)

    def order_success(self):
        """Run each item's order_success method."""
        for orderitem in self.orderitem_set.all():
            subtype = orderitem.product.get_subtype_with_attr('order_success')
            if subtype:
                subtype.order_success(self, orderitem)
                
    def _paid_in_full(self):
        """True if total has been paid"""
        return self.balance <= 0
    paid_in_full = property(fget=_paid_in_full)
    
    def _has_downloads(self):
        """Determine if there are any downloadable products on this order"""
        if self.downloadlink_set.count() > 0:
            return True
        return False
    has_downloads = property(_has_downloads)

    def _is_shippable(self):
        """Determine if we will be shipping any items on this order """
        for orderitem in self.orderitem_set.all():
            if orderitem.product.is_shippable:
                return True
        return False
    is_shippable = property(_is_shippable)

    def validate(self, request):
        """
        Return whether the order is valid.
        Not guaranteed to be side-effect free.
        """
        valid = True
        for orderitem in self.orderitem_set.all():
            for subtype_name in orderitem.product.get_subtypes():
                subtype = getattr(orderitem.product, subtype_name.lower())
                validate_method = getattr(subtype, 'validate_order', None)
                if validate_method:
                    valid = valid and validate_method(request, self, orderitem)
        return valid

    class Admin:
        fields = (
            (None, {'fields': ('contact', 'method', 'status', 'notes')}),
            (_('Shipping Method'), {'fields':
                ('shipping_method', 'shipping_description')}),
            (_('Shipping Address'), {'classes': 'collapse', 'fields':
                ('ship_street1', 'ship_street2', 'ship_city', 'ship_state',
                'ship_postal_code', 'ship_country')}),
            (_('Billing Address'), {'classes': 'collapse', 'fields':
                ('bill_street1', 'bill_street2', 'bill_city', 'bill_state',
                'bill_postal_code', 'bill_country')}),
            (_('Totals'), {'fields':
                ('sub_total', 'shipping_cost', 'tax', 'discount', 'total',
                'timestamp')}))
        list_display = ('contact', 'timestamp', 'order_total', 'balance_forward', 'status',
            'invoice', 'packingslip', 'shippinglabel')
        list_filter = ['timestamp', 'contact']
        date_hierarchy = 'timestamp'

    class Meta:
        verbose_name = _("Product Order")
        verbose_name_plural = _("Product Orders")

class OrderItem(models.Model):
    """
    A line item on an order.
    """
    order = models.ForeignKey(Order, verbose_name=_("Order"), edit_inline=models.TABULAR, num_in_admin=3)
    product = models.ForeignKey(Product, verbose_name=_("Product"))
    quantity = models.IntegerField(_("Quantity"), core=True)
    unit_price = models.DecimalField(_("Unit price"),
        max_digits=6, decimal_places=2)
    line_item_price = models.DecimalField(_("Line item price"),
        max_digits=6, decimal_places=2)

    def __unicode__(self):
        return self.product.name

    def _get_category(self):
        return(self.product.get_category.name)
    category = property(_get_category)

    class Meta:
        verbose_name = _("Order Line Item")
        verbose_name_plural = _("Order Line Items")

class DownloadLink(models.Model):
    downloadable_product = models.OneToOneField(DownloadableProduct)
    order = models.ForeignKey(Order)
    key = models.CharField(max_length=40)
    num_attempts = models.IntegerField()
    time_stamp = models.DateTimeField()
    active = models.BooleanField(default=True)

    def is_valid(self):
        # Check num attempts and expire_minutes
        if not self.downloadable_product.active:
            return (False, _("This download is no longer active"))
        if self.num_attempts > self.downloadable_product.num_allowed_downloads:
            return (False, _("You have exceeded the number of allowed downloads."))
        expire_time = datetime.timedelta(minutes=self.downloadable_product.expire_minutes) + self.time_stamp
        if datetime.datetime.now() > expire_time:
            return (False, _("This download link has expired."))
        return (True, "")
        
    def get_absolute_url(self):
        return('satchmo.shop.views.download.process', (), { 'download_key': self.key})
    get_absolute_url = permalink(get_absolute_url)
    
    def get_full_url(self):
        url = urlresolvers.reverse('satchmo_download_process', kwargs= {'download_key': self.key})
        return('http://%s%s' % (Site.objects.get_current(), url))

    def save(self):
        """
       Set the initial time stamp
        """
        if self.time_stamp is None:
            self.time_stamp = datetime.datetime.now()
        super(DownloadLink, self).save()
    
    def __unicode__(self):
        return u"%s - %s" % (self.downloadable_product.product.slug, self.time_stamp)
    
    def _product_name(self):
        return u"%s" % (self.downloadable_product.product.name)
    product_name=property(_product_name)        
    
    class Admin:
        pass

class OrderStatus(models.Model):
    """
    An order will have multiple statuses as it moves its way through processing.
    """
    order = models.ForeignKey(Order, verbose_name=_("Order"), edit_inline=models.STACKED, num_in_admin=1)
    status = models.CharField(_("Status"),
        max_length=20, choices=ORDER_STATUS, core=True, blank=True)
    notes = models.CharField(_("Notes"), max_length=100, blank=True)
    timestamp = models.DateTimeField(_("Timestamp"))

    def __unicode__(self):
        return self.status

    def save(self):
        super(OrderStatus, self).save()
        self.order.status = self.status
        self.order.save()

    class Meta:
        verbose_name = _("Order Status")
        verbose_name_plural = _("Order Statuses")

class OrderPayment(models.Model):
    order = models.ForeignKey(Order, related_name="payments")
    payment = models.CharField(_("Payment Method"),
        choices=payment_choices(), max_length=25, blank=True)
    amount = models.DecimalField(_("amount"), core=True,
        max_digits=6, decimal_places=2, blank=True, null=True)
    timestamp = models.DateTimeField(_("timestamp"), blank=True, null=True)

    def _credit_card(self):
        """Return the credit card associated with this payment."""
        try:
            return self.creditcards.get()
        except self.creditcards.model.DoesNotExist:
            return None
    credit_card = property(_credit_card)

    def _amount_total(self):
        return moneyfmt(self.amount)

    amount_total = property(fget=_amount_total)

    def __unicode__(self):
        if self.id is not None:
            return u"Order payment #%i" % self.id
        else:
            return u"Order payment (unsaved)"

    def save(self):
        if not self.id:
            self.timestamp = datetime.datetime.now()

        super(OrderPayment, self).save()

    class Admin:
        list_filter = ['order', 'payment']
        list_display = ['id', 'order', 'payment', 'amount_total', 'timestamp']
        fields = (
            (None, {'fields': ('order', 'payment', 'amount', 'timestamp')}),
            )
            
    class Meta:
        verbose_name = _("Order Payment")
        verbose_name_plural = _("Order Payments")