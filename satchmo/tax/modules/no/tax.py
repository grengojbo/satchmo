from decimal import Decimal

class Processor(object):
    
    method="no"
    
    def __init__(self, order=None):
        """
        Any preprocessing steps should go here
        For instance, copying the shipping and billing areas
        """
        pass

    def by_product(self, product, user):
        return Decimal("0.0")
                
    def shipping(self, product, user):
        return Decimal("0.0")                
                
    def process(self, order=None):
        """
        Calculate the tax and return it
        """
        return Decimal("0.0"), {}
