try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from django import newforms as forms
from django.conf import settings
from django.core import serializers, urlresolvers
from django.core.management.base import CommandError
from django.core.management.color import no_style
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from satchmo.configuration import config_value
from satchmo.product.models import Product, Price, Option
import logging
import os
import time
import zipfile

try:
    set
except NameError:
    from sets import Set as set   # Python 2.3 fallback

log = logging.getLogger('product.forms')

def export_choices():
    fmts = serializers.get_serializer_formats()
    return zip(fmts,fmts)

class ProductExportForm(forms.Form):    
    
    def __init__(self, *args, **kwargs):
        products = kwargs.pop('products', None)
        
        super(ProductExportForm, self).__init__(*args, **kwargs)
        
        self.fields['format'] = forms.ChoiceField(label=_('export format'), choices=export_choices(), required=True)
        self.fields['include_images'] = forms.BooleanField(label=_('Include Images'), initial=True, required=False)
        self.fields['include_categories'] = forms.BooleanField(label=_('Include Categories'), initial=True, required=False)
        
        if not products:
            products = Product.objects.all().order_by('slug')
            
        for product in products:
            subtypes = product.get_subtypes()
            expclasses = ('export', ) + subtypes
            extclasses = " ".join(expclasses)

            kw = { 
            'label' : product.slug,
            'help_text' : product.name,
            'initial' : False,
            'required' : False,
            'widget' : forms.CheckboxInput(attrs={'class': extclasses}) }
            
            chk = forms.BooleanField(**kw)
            chk.slug = product.slug
            chk.product_id = product.id
            chk.subtypes = " ".join(subtypes)            
            self.fields['export__%s' % product.slug] = chk
            
    def export(self, request):
        self.full_clean()
        format = 'yaml'
        selected = []
        include_images = False
        include_categories = False
        
        for name, value in self.cleaned_data.items():
            if name == 'format':
                format = value
                continue
                
            if name == 'include_images':
                include_images = value
                continue
            
            if name == 'include_categories':
                include_categories = value
                continue
                
            opt, key = name.split('__')
            
            if opt=='export':
                if value:
                    selected.append(key)

        try:
            serializers.get_serializer(format)
        except KeyError:
            raise CommandError("Unknown serialization format: %s" % format)

        objects = []
        images = []
        categories = {}
        for slug in selected:
            product = Product.objects.get(slug=slug)
            objects.append(product)
            for subtype in product.get_subtypes():
                objects.append(getattr(product,subtype.lower()))
            objects.extend(list(product.price_set.all()))
            objects.extend(list(product.productimage_set.all()))
            if include_images:
                for image in product.productimage_set.all():
                    images.append(image.picture)
            if include_categories:
                for category in product.category.all():
                    if category not in categories:
                        categories[category] = 1

        # Export all categories, translations.  Export images,translations if
        # desired.
        if include_categories:
            for category in categories.keys():
                objects.append(category)
                objects.extend(list(category.translations.all()))
                if include_images:
                    for image in category.images.all():
                        objects.append(image)
                        objects.extend(list(image.translations.all()))

        try:
            raw = serializers.serialize(format, objects, indent=False)
        except Exception, e:
            raise CommandError("Unable to serialize database: %s" % e)
            
        if include_images:
            filedir = settings.MEDIA_ROOT
            buf = StringIO()
            zf = zipfile.ZipFile(buf, 'a', zipfile.ZIP_STORED)
            
            export_file = 'products.%s' % format
            zf.writestr(str(export_file), raw)
            
            zinfo = zf.getinfo(str(export_file)) 
            # Caution, highly magic number, chmods the file to 644 
            zinfo.external_attr = 2175008768L 
            
            image_dir = config_value('PRODUCT', 'IMAGE_DIR')
            config = "PRODUCT.IMAGE_DIR=%s\nEXPORT_FILE=%s" % (image_dir, export_file)
            zf.writestr('VARS', config)
            
            zinfo = zf.getinfo('VARS') 
            # Caution, highly magic number, chmods the file to 644 
            zinfo.external_attr = 2175008768L 
            
            for image in images:
                f = os.path.join(filedir, image)
                if os.path.exists(f):
                    zf.write(f, str(image))
            
            zf.close()
            
            raw = buf.getvalue()
            mimetype = "application/zip"
            format = "zip"
        else:
            mimetype = "text/" + format

        response = HttpResponse(mimetype=mimetype, content=raw)
        response['Content-Disposition'] = 'attachment; filename="products-%s.%s"' % (time.strftime('%Y%m%d-%H%M'), format)
            
        return response


class ProductImportForm(forms.Form):  
    
    def __init__(self, *args, **kwargs):        
        super(ProductImportForm, self).__init__(*args, **kwargs)
    
        self.fields['upload'] = forms.Field(label=_("File to import"), widget=forms.FileInput, required=False)

    def import_from(self, infile, maxsize=10000000):
        errors = []
        results = []
        
        filetype = infile['content-type']   
        filename = infile['filename']  
        raw = infile['content']
        
        # filelen = len(raw)
        # if filelen > maxsize:
        #     errors.append(_('Import too large, must be smaller than %i bytes.' % maxsize ))
        
        format = os.path.splitext(filename)[1]
        if format and format.startswith('.'):
            format = format[1:]
        if not format:
            errors.append(_('Could not parse format from filename: %s') % filename)
        
        if format == 'zip':
            zf = zipfile.ZipFile(StringIO(raw), 'r')
            files = zf.namelist()
            image_dir = config_value('PRODUCT', 'IMAGE_DIR')
            other_image_dir = None
            export_file = None
            if 'VARS' in files:
                config = zf.read('VARS')
                lines = [line.split('=') for line in config.split('\n')]
                for key, val in lines:
                    if key == 'PRODUCT.IMAGE_DIR':
                        other_image_dir = val
                    elif key == 'EXPORT_FILE':
                        export_file = val
                
                if other_image_dir is None or export_file is None:
                    errors.append(_('Bad VARS file in import zipfile.'))
                    
                else:
                    # save out all the files which start with other_image_dr
                    rename = image_dir == other_image_dir
                    for f in files:
                        if f.startswith(other_image_dir):
                            buf = zf.read(f)
                            if rename:
                                f = f[len(other_image_dir):]
                                if f[0] in ('/', '\\'):
                                    f = f[1:]
                                f = os.path.join(settings.MEDIA_ROOT, image_dir, f)
                            outf = open(f, 'w')
                            outf.write(buf)
                            outf.close()
                            results.append('Imported image: %s' % f)
                            
                    infile = zf.read(export_file)
                    zf.close()
                    
                    format = os.path.splitext(export_file)[1]
                    if format and format.startswith('.'):
                        format = format[1:]
                    if not format:
                        errors.append(_('Could not parse format from filename: %s') % filename)
                    else:
                        raw = infile
            
            else:
                errors.append(_('Missing VARS in import zipfile.'))
        
        else:
            raw = StringIO(str(raw))
            
        if not format in serializers.get_serializer_formats():
            errors.append(_('Unknown file format: %s') % format)
            
        if not errors:
            serializer = serializers.get_serializer(format)
            
            from django.db import connection, transaction
            
            transaction.commit_unless_managed()
            transaction.enter_transaction_management()
            transaction.managed(True)
        
            try:
                objects = serializers.deserialize(format, raw)
                ct = 0
                models = set()
                for obj in objects:
                    obj.save()
                    models.add(obj.object.__class__)
                    ct += 1
                if ct>0:
                    style=no_style()
                    sequence_sql = connection.ops.sequence_reset_sql(style, models)
                    if sequence_sql:
                        cursor = connection.cursor()
                        for line in sequence_sql:
                            cursor.execute(line)
                    
                results.append(_('Added %(count)i objects from %(filename)s') % {'count': ct, 'filename': filename})
                transaction.commit()
                #label_found = True
            except Exception, e:
                #fixture.close()
                errors.append(_("Problem installing fixture '%(filename)s': %(error_msg)s\n") % {'filename': filename, 'error_msg': str(e)})
                errors.append("Raw: %s" % raw)
                transaction.rollback()
                transaction.leave_transaction_management()
            
        return results, errors


class InventoryForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        products = kwargs.pop('products', None)

        super(InventoryForm, self).__init__(*args, **kwargs)

        if not products:
            products = Product.objects.all().order_by('slug')

        for product in products:
            subtypes = product.get_subtypes()
            qtyclasses = ('text', 'qty') + subtypes
            qtyclasses = " ".join(qtyclasses)

            kw = { 
            'label' : product.slug,
            'help_text' : product.name,
            'initial' : product.items_in_stock,
            'widget' : forms.TextInput(attrs={'class': qtyclasses}) }

            qty = forms.IntegerField(**kw)
            self.fields['qty__%s' % product.slug] = qty
            qty.slug = product.slug
            qty.product_id = product.id
            qty.subtypes = " ".join(subtypes)

            if 'CustomProduct' in subtypes:
                initial_price = product.customproduct.full_price
            else:
                initial_price = product.unit_price
                
            kw['initial'] = initial_price
            kw['required'] = False
            kw['widget'] = forms.TextInput(attrs={'class': "text price"})
            price = forms.DecimalField(**kw)
            price.slug = product.slug
            self.fields['price__%s' % product.slug] = price

            kw['initial'] = product.active
            kw['widget'] = forms.CheckboxInput(attrs={'class': "checkbox active"})
            active = forms.BooleanField(**kw)
            active.slug = product.slug
            self.fields['active__%s' % product.slug] = active

            kw['initial'] = product.featured
            kw['widget'] = forms.CheckboxInput(attrs={'class': "checkbox featured"})
            featured = forms.BooleanField(**kw)
            featured.slug = product.slug
            self.fields['featured__%s' % product.slug] = featured

    def save(self, request):
        self.full_clean()
        for name, value in self.cleaned_data.items():
            opt, key = name.split('__')

            prod = Product.objects.get(slug__exact=key)
            subtypes = prod.get_subtypes()
            
            if opt=='qty':
                if value != prod.items_in_stock:
                    request.user.message_set.create(message='Updated %s stock to %s' % (key, value))
                    log.debug('Saving new qty=%i for %s' % (value, key))
                    prod.items_in_stock = value
                    prod.save()

            elif opt=='price':
                if 'CustomProduct' in subtypes:
                    full_price = prod.customproduct.full_price
                else:
                    full_price = prod.unit_price
                    
                if value != full_price:
                    request.user.message_set.create(message='Updated %s unit price to %s' % (key, value))
                    log.debug('Saving new price %s for %s' % (value, key))
                    try:
                        price = Price.objects.get(product=prod, quantity=1)
                    except Price.DoesNotExist:
                        price = Price(product=prod, quantity=1)
                    price.price = value
                    price.save()

            elif opt=="active":
                if value != prod.active:
                    if value:
                        note = "Activated %s"
                    else:
                        note = "Deactivated %s"
                    request.user.message_set.create(message=note % (key))

                    prod.active = value
                    prod.save()

            elif opt=="featured":
                if value != prod.featured:
                    if value:
                        note = "%s is now featured"
                    else:
                        note = "%s is no longer featured"
                    request.user.message_set.create(message=note % (key))

                    prod.featured = value
                    prod.save()

class VariationManagerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.optionkeys = []
        self.variationkeys = []
        self.existing = {}
        self.optiondict = {}
        self.edit_urls = {}
        self.namedict = {}
        self.skudict = {}
        self.slugdict = {}
        
        self.product = kwargs.pop('product', None)
        
        super(VariationManagerForm, self).__init__(*args, **kwargs)
        
        if self.product:
            configurableproduct = self.product.configurableproduct;
            
            for grp in configurableproduct.option_group.all():
                optchoices = [("%i_%i" % (opt.optionGroup.id, opt.id), opt.name) for opt in grp.option_set.all()]
                kw = { 
                    'label' : grp.name,
                    'widget' : forms.CheckboxSelectMultiple(),
                    'required' : False,
                    'choices' : optchoices,
                }
                fld = forms.MultipleChoiceField(**kw)
                key = 'optiongroup__%s' % grp.id
                self.fields[key] = fld
                self.optionkeys.append(key)
                self.optiondict[grp.id] = []
                
            for opts in configurableproduct.get_all_options():
                variation = configurableproduct.get_product_from_options(opts)
                optnames = [opt.value for opt in opts]
                kw = { 
                    'initial' : None,
                    'label' : " ".join(optnames)
                }
                
                opt_str = '__'.join(["%i_%i" % (opt.optionGroup.id, opt.id) for opt in opts])    
                
                key = "pv__%s" % opt_str

                if variation:
                    basename = variation.name
                    sku = variation.sku
                    slug = variation.slug
                    kw['initial'] = 'add'
                    self.existing[key] = True
                    self.edit_urls[key] = urlresolvers.reverse('django.contrib.admin.views.main.change_stage', args=('product', 'product', variation.id))
                else:
                    basename = u'%s (%s)' % (self.product.name, u'/'.join(optnames))
                    slug = u'%s_%s' % (self.product.slug, u'_'.join(optnames))
                    sku = ""

                pv = forms.BooleanField(**kw)

                self.fields[key] = pv
                
                for opt in opts:
                    self.optiondict[opt.optionGroup.id].append(key)
                
                self.variationkeys.append(key)
                
                # Name Field
                
                nv = forms.CharField(initial=basename)
                namekey = "name__%s" % opt_str
                self.fields[namekey] = nv
                self.namedict[key] = namekey
                
                # SKU Field                

                sv = forms.CharField(initial=sku)
                skukey = "sku__%s" % opt_str
                self.fields[skukey] = sv
                self.skudict[key] = skukey
                
                # Slug Field
                sf = forms.CharField(initial=slug)
                slugkey = "slug__%s" % opt_str
                self.fields[slugkey] = sf
                self.slugdict[key] = slugkey

    def save(self, request):
        self.full_clean()
        configurableproduct = self.product.configurableproduct;
        for name, value in self.cleaned_data.items():
            if '__' in name:
                parts = name.split('__')
                opt = parts[0]
                ids = [part.split('_') for part in parts[1:]]
                
                if opt == "pv":
                    if value:
                        opts = _get_options_for_ids(ids)
                        if opts:
                            namekey = "name" + name[2:]
                            nameval = self.cleaned_data[namekey]
                            skukey = "sku" + name[2:]
                            skuval = self.cleaned_data[skukey]
                            slugkey = "slug" + name[2:]
                            slugval = self.cleaned_data[slugkey]
                            log.debug("Got name=%s, sku=%s, slug=%s", nameval, skuval, slugval)
                            
                            configurableproduct.create_variation(opts, name=nameval, sku=skuval, slug=slugval)
                            
                    else:
                        opts = _get_options_for_ids(ids)
                        if opts:
                            variation = configurableproduct.get_product_from_options(opts)
                            if variation:
                                log.info("Deleting variation for [%s] %s", self.product.slug, opts)
                                variation.delete()
            
def _get_options_for_ids(ids):
    opts = []
    for grpid, optid in ids:
        option = Option.objects.get(optionGroup__id = grpid, id = optid)
        opts.append(option)
    return opts
    