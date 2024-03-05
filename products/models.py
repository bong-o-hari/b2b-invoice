from django.db import models

from inboicing_system.core.mixins import AuditModelMixin

# Create your models here.


class ProductMaster(AuditModelMixin):
    """
    Table to store product details that you offer
    """

    product_name = models.CharField(max_length=256, blank=True, null=True)
    mrp = models.IntegerField(blank=True, null=True)
    hsn_code = models.IntegerField(blank=True, null=True)
    gst_percent = models.IntegerField(blank=True, null=True)
    primary_box_qty = models.IntegerField(blank=True, null=True)
    pack = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Products"

    def __str__(self):
        return self.product_name

    def save(self, *args, **kwargs):
        self.product_name = self.product_name.replace("'", "")
        super(ProductMaster, self).save(*args, **kwargs)
