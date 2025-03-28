from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Lug‘atdan kalit bo‘yicha qiymat olish"""
    return dictionary.get(key)
