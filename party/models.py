from django.db import models

from inboicing_system.core.mixins import AuditModelMixin
from .utils import get_state_from_pincode
# Create your models here.

class PartyDetails(AuditModelMixin):
    """
    Party details, about any particular party we are dealing with
    """
    name        = models.CharField(max_length=200, blank=True, null=True)
    gstin       = models.CharField(max_length=15, blank=True, null=True)
    dl          = models.CharField(max_length=30, blank=True, null=True)
    phone       = models.CharField(max_length=15, blank=True, null=True)
    address     = models.TextField(blank=True, null=True)
    city        = models.CharField(max_length=50, blank=True, null=True)
    state       = models.CharField(max_length=50, blank=True, null=True)
    pincode     = models.IntegerField(blank=True, null=True)
    state_code  = models.IntegerField(blank=True, null=True)
    country     = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Party Details'

    def save(self, *args, **kwargs):
        if self.pincode:
            _state = get_state_from_pincode(self.pincode)
            self.state = _state
        super(PartyDetails, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.gstin}"
