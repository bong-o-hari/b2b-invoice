from django.contrib import admin
from .models import ProductMaster
# Register your models here.

class ProductMasterAdmin(admin.ModelAdmin):
    search_fields = ('product_name', 'hsn_code')
    exclude = ('is_deleted', 'deleted_at')
admin.site.register(ProductMaster, ProductMasterAdmin)