import requests
import config


def get_state_from_pincode(pincode):
    res = requests.get(f"{config.INDIAPOST_API}/{pincode}")
    res = res.json()
    po = res[0].get('PostOffice', [])
    if po_details := po[0]:
        return po_details.get('State')
    return None


def get_party_by_id(party_id):
    from .models import PartyDetails

    if party_id and (party := PartyDetails.objects.get(id=party_id, is_deleted=False)):
        return party
    return None
