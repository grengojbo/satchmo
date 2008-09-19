from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from satchmo.product.admin import ProductOptions
from satchmo.product.brand.models import Brand, BrandTranslation, BrandCategory, BrandCategoryTranslation, BrandProduct
from satchmo.product.models import Product
from satchmo.thumbnail.field import ImageWithThumbnailField
from satchmo.thumbnail.widgets import AdminImageWithThumbnailWidget

class BrandTranslation_Inline(admin.StackedInline):
    model = BrandTranslation
    extra = 1
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        # This method will turn all TextFields into giant TextFields
        if isinstance(db_field, ImageWithThumbnailField):
            kwargs['widget'] = AdminImageWithThumbnailWidget
            return db_field.formfield(**kwargs)
            
        return super(BrandTranslation_Inline, self).formfield_for_dbfield(db_field, **kwargs)
    

class BrandCategoryTranslation_Inline(admin.StackedInline):
    model = BrandCategoryTranslation
    extra = 1

    def formfield_for_dbfield(self, db_field, **kwargs):
        # This method will turn all TextFields into giant TextFields
        if isinstance(db_field, ImageWithThumbnailField):
            kwargs['widget'] = AdminImageWithThumbnailWidget
            return db_field.formfield(**kwargs)
            
        return super(BrandCategoryTranslation_Inline, self).formfield_for_dbfield(db_field, **kwargs)

class BrandCategoryTranslationOptions(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields' : ('brandcategory', 'languagecode', 'name', 'description', 'picture')}),
    )

class BrandOptions(admin.ModelAdmin):
    inlines = [BrandTranslation_Inline]
    filter_horizontal = ('products',)
    
class BrandProductInline(admin.TabularInline):
    model = BrandProduct
    max_num = 1

class BrandTranslationOptions(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields' : ('brand', 'languagecode', 'name', 'description', 'picture')}),
    )

class BrandCategoryOptions(admin.ModelAdmin):
    inlines = [BrandCategoryTranslation_Inline]
    filter_horizontal = ('products',)

admin.site.register(Brand, BrandOptions)
admin.site.register(BrandCategory, BrandCategoryOptions)
admin.site.unregister(Product)
ProductOptions.inlines.append(BrandProductInline)
admin.site.register(Product, ProductOptions)
