from django import template

register = template.Library()

def date_string(date):
    """Change datetime object to string representation for templates"""
    return date.strftime('%m/%y')

def get_tax(product):
    """Get igst or cgst for a product"""
    return product.igst or product.cgst

register.filter('date_string', date_string)
register.filter('get_tax', get_tax)
