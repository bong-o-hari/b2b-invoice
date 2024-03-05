from .models import ProductMaster

def get_product_from_id(product_id):
    if product_id and (product := ProductMaster.objects.filter(id=product_id, is_deleted=False).first()):
        return product
    return None