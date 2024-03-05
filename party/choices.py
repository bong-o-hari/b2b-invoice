from django.db import models

class StateCodes(models.IntegerChoices):
    JAMMU_AND_KASHMIR       = 1
    HIMACHAL_PRADESH        = 2
    PUNJAB                  = 3
    CHANDIGARH              = 4
    UTTARAKHAND             = 5
    HARYANA                 = 6
    DELHI                   = 7
    RAJASTHAN               = 8
    UTTAR_PRADESH           = 9
    BIHAR                   = 10
    SIKKIM                  = 11
    ARUNACHAL_PRADESH       = 12
    NAGALAND                = 13
    MANIPUR                 = 14
    MIZORAM                 = 15
    TRIPURA                 = 16
    MEGHALAYA               = 17
    ASSAM                   = 18
    WEST_BENGAL             = 19
    JHARKHAND               = 20
    ORISSA                  = 21
    CHHATTISGARH            = 22
    MADHYA_PRADESH          = 23
    GUJARAT                 = 24
    DAMAN_AND_DIU           = 25
    DADRA_AND_NAGAR_HAVELI  = 26
    MAHARASHTRA             = 27
    KARNATAKA               = 29
    GOA                     = 30
    LAKSHADWEEP             = 31
    KERALA                  = 32
    TAMIL_NADU              = 33
    PUDUCHERRY              = 34
    ANDAMAN_AND_NICOBAR     = 35
    TELANGANA               = 36
    ANDHRA_PRADESH          = 37
    LADAKH                  = 38
    OTHER_COUNTRY           = 96
    OTHER_TERRITORY         = 97