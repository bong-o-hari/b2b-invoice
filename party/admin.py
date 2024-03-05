from django.contrib import admin
from .models import PartyDetails
# Register your models here.

class PartyAdmin(admin.ModelAdmin):
    search_fields = ('phone', 'gstin')
    exclude = ('is_deleted', 'deleted_at')
    readonly_fields = ('state',)
admin.site.register(PartyDetails, PartyAdmin)