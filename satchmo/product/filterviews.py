from django import http
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from satchmo.caching import cache_get, cache_set, NotCachedError
from satchmo.configuration import config_value
from satchmo.product.models import Product
import comments
import logging
        
log = logging.getLogger('product.filterviews')

def display_bestratings(request):
    """Display a list of the products with the best ratings in comments"""
    products = comments.highest_rated()
    ctx = RequestContext(request, {
        'products' : products,
    })
    return render_to_response('product/best_ratings.html', ctx)
    
def display_bestsellers(request):
    """Display a list of the products which have sold the most"""
    try:
        pks = cache_get('BESTSELLERS')
        pks = [long(pk) for pk in pks.split(',')]
        productdict = Product.objects.in_bulk(pks)
        #log.debug(productdict)
        sellers = [productdict[pk] for pk in pks]
        log.debug('retrieved bestselling products from cache')
        
    except NotCachedError, nce:
        products = Product.objects.all()
        work = []
        for p in products:
            ct = p.orderitem_set.count()
            if ct>0:
                work.append((ct, p))
        num = config_value('SHOP', 'NUM_DISPLAY')
        work.sort()
        work = work[-num:]
        work.reverse()
        
        sellers = []
        pks = []
        
        for p in work:
            product = p[1]
            pks.append("%i" % product.pk)
            sellers.append(product)
             
        pks = ",".join(pks)
        log.debug('calculated bestselling products, set to cache: %s', sellers)
        cache_set(nce.key, value=pks)

    ctx = RequestContext(request, {
        'products' : sellers,
    })
    return render_to_response('product/best_sellers.html', ctx)
        
def display_recent(request):
    """Display a list of recently added products."""
    if request.method == 'GET':
        page = request.GET.get('page', 1)
    else:
        page = 1
        
    num = config_value('SHOP', 'NUM_PAGINATED')
    query = Product.objects.filter(active=True, productvariation__product__isnull=True).order_by('-date_added')
    paginator = Paginator(query, num)
    currentpage = paginator.page(page)
    
    ctx = RequestContext(request, {
        'page' : currentpage
    })
    return render_to_response('product/recently_added.html', ctx)
