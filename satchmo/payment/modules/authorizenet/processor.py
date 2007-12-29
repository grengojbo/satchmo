from satchmo.payment.common.utils import record_payment
from urllib import urlencode
import urllib2

class PaymentProcessor(object):
    #Authorize.NET payment processing module
    #You must have an account with authorize.net in order to use this module
    def __init__(self, settings):
        self.settings = settings
        self.contents = ''
        if settings.LIVE.value:
            testflag = 'FALSE'
            self.connection = settings.CONNECTION.value
        else:
            testflag = 'TRUE'
            self.connection = settings.CONNECTION_TEST.value
            
        self.configuration = {
            'x_login' : settings.LOGIN.value,
            'x_tran_key' : settings.TRANKEY.value,
            'x_version' : '3.1',
            'x_relay_response' : 'FALSE',
            'x_test_request' : testflag,
            'x_delim_data' : 'TRUE',
            'x_delim_char' : '|',
            'x_type': 'AUTH_CAPTURE',
            'x_method': 'CC',
            }

    def prepareData(self, data):
        self.custBillData = {
            'x_first_name' : data.contact.first_name,
            'x_last_name' : data.contact.last_name,
            'x_address': data.full_bill_street,
            'x_city': data.bill_city,
            'x_state' : data.bill_state,
            'x_zip' : data.bill_postal_code,
            'x_country': data.bill_country,
            'x_phone' : data.contact.primary_phone
            }
        # Can add additional info here if you want to but it's not required
        self.transactionData = {
            'x_amount' : data.balance,
            'x_card_num' : data.credit_card.decryptedCC,
            'x_exp_date' : data.credit_card.expirationDate,
            'x_card_code' : data.credit_card.ccv
            }

        self.postString = urlencode(self.configuration) + "&" + urlencode(self.transactionData) + "&" + urlencode(self.custBillData)
        self.order = data

    def process(self):
        # Execute the post to Authorize Net
        conn = urllib2.Request(url=self.connection, data=self.postString)
        f = urllib2.urlopen(conn)
        all_results = f.read()
        parsed_results = all_results.split(self.configuration['x_delim_char'])
        response_code = parsed_results[0]
        reason_code = parsed_results[1]
        response_text = parsed_results[3]
        record_payment(self.order, self.settings, order=self.order.balance)
        if response_code == '1':
            return(True, reason_code, response_text)
        elif response_code == '2':
            return(False, reason_code, response_text)
        else:
            return(False, reason_code, response_text)


if __name__ == "__main__":
    #####
    # This is for testing - enabling you to run from the command line and make
    # sure everything is ok
    #####

    import os
    from satchmo.configuration import config_get_group
    import config

    # Set up some dummy classes to mimic classes being passed through Satchmo
    class testContact(object):
        pass
    class testCC(object):
        pass
    class testOrder(object):
        def __init__(self):
            self.contact = testContact()
            self.credit_card = testCC()
        def order_success(self):
            pass

    if not os.environ.has_key("DJANGO_SETTINGS_MODULE"):
        os.environ["DJANGO_SETTINGS_MODULE"]="satchmo.settings"

    settings_module = os.environ['DJANGO_SETTINGS_MODULE']
    settingsl = settings_module.split('.')
    settings = __import__(settings_module, {}, {}, settingsl[-1])

    sampleOrder = testOrder()
    sampleOrder.contact.first_name = 'Chris'
    sampleOrder.contact.last_name = 'Smith'
    sampleOrder.contact.primary_phone = '801-555-9242'
    sampleOrder.full_bill_street = '123 Main Street'
    sampleOrder.bill_postal_code = '12345'
    sampleOrder.bill_state = 'TN'
    sampleOrder.bill_city = 'Some City'
    sampleOrder.bill_country = 'US'
    sampleOrder.total = "27.00"
    sampleOrder.balance = "27.00"
    sampleOrder.credit_card.decryptedCC = '6011000000000012'
    sampleOrder.credit_card.expirationDate = "10/09"
    sampleOrder.credit_card.ccv = "144"

    authorize_settings = config_get_group('PAYMENT_AUTHORIZENET')
    if authorize_settings.LIVE.value:
        print "Warning.  You are submitting a live order.  AUTHORIZE.NET system is set LIVE."
        
    processor = PaymentProcessor(authorize_settings)
    processor.prepareData(sampleOrder)
    results, reason_code, msg = processor.process()
    print results,"::", msg


