from django.db import models
from django.utils.translation import ugettext_lazy as _
from satchmo.contact.models import Contact
import config
import datetime

class NullContact(object):
    """Simple object emulating a Contact, so that we can add users who aren't Satchmo Contacts.

    Note, this is *not* a Django object, and is not saved to the DB, only to the subscription lists.
    """

    def __init__(self, full_name, email):
        if not full_name:
            full_name = email.split('@')[0]

        self.full_name = full_name
        self.email = email

def get_contact_or_fake(full_name, email):
    try:
        contact = Contact.objects.get(email=email)

    except Contact.DoesNotExist:
        contact = NullContact(full_name, email)

    return contact

class Subscription(models.Model):
    """A newsletter subscription."""

    subscribed = models.BooleanField(_('Subscribed'), default=True)
    email = models.EmailField(_('Email'))
    create_date = models.DateField(_("Creation Date"))
    update_date = models.DateField(_("Update Date"))

    @classmethod
    def email_is_subscribed(cls, email):
        try:
            sub = cls.objects.get(email=email)
            return sub.subscribed
        except cls.DoesNotExist:
            return False

    def __unicode__(self):
        if self.subscribed:
            flag="Y"
        else:
            flag="N"
        return u"[%s] %s" % (flag, self.email)

    def __repr__(self):
        return "<Subscription: %s>" % str(self)

    def save(self):
        if not self.id:
            self.create_date = datetime.date.today()

        self.update_date = datetime.date.today()

        super(Subscription, self).save()
        
    class Admin:
        list_display = ['email', 'subscribed', 'create_date', 'update_date']
        list_filter = ['subscribed']

