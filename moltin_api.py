import requests
from slugify import slugify


def get_access_token(client_id, client_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()


def get_products(access_token):
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_products_by_category_id(access_token, category_id):
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    payload = {
        'filter': f'eq(category.id, {category_id})'
    }
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    return response.json()


def get_products_by_category_slug(access_token, category_slug):
    category = get_category_by_slug(access_token, category_slug)
    category_id = category['data'][0]['id']
    products_by_category = get_products_by_category_id(access_token,
                                                       category_id)
    return products_by_category


def get_product(access_token, product_id):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product_main_image_url(access_token, image_id):
    url = f'https://api.moltin.com/v2/files/{image_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


def create_product(access_token, product_id, name, description,
                   price, slug=None):
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    product_description = {
        'data': {
            'type': 'product',
            'name': name,
            'slug': slug if slug else slugify(name),
            'sku': f'sku-{product_id}',
            'description': description,
            'manage_stock': False,
            'price': [
                {
                    'amount': int(price) * 100,
                    'currency': 'RUB',
                    'includes_tax': True,
                },
            ],
            'status': 'live',
            'commodity_type': 'physical',
        },
    }
    response = requests.post(url, headers=headers, json=product_description)
    response.raise_for_status()
    return response.json()


def add_product_main_image(access_token, product_id, image_id):
    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    image_description = {
        'data': {
            'type': 'main_image',
            'id': image_id,
        },
    }
    response = requests.post(url, headers=headers, json=image_description)
    response.raise_for_status()
    return response.json()


def delete_product(access_token, product_id):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    return response.ok


def get_or_create_cart(access_token, cart_id, currency='RUB'):
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-MOLTIN-CURRENCY': currency
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_items(access_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def add_cart_item(access_token, cart_id, item_id,
                  item_quantity, currency='RUB'):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-MOLTIN-CURRENCY': currency
    }
    cart_item = {
        'data': {
            'id': item_id,
            'type': 'cart_item',
            'quantity': item_quantity,
        },
    }
    response = requests.post(url, headers=headers, json=cart_item)
    response.raise_for_status()
    return response.json()


def remove_cart_item(access_token, cart_id, item_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{item_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    return response.ok


def delete_cart(access_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    return response.ok


def get_customer(access_token, customer_id):
    url = f'https://api.moltin.com/v2/customers/{customer_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_customer(access_token, email, name=None):
    url = 'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    customer = {
        'data': {
            'type': 'customer',
            'name': name if name else email.split('@')[0],
            'email': email,
        },
    }
    response = requests.post(url, headers=headers, json=customer)
    response.raise_for_status()
    return response.json()


def create_file(access_token, file_url):
    url = 'https://api.moltin.com/v2/files'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    files = {
        'file_location': (None, file_url),
    }
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    return response.json()


def create_flow(access_token, name, description, slug=None, enabled=True):
    url = 'https://api.moltin.com/v2/flows'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    flow_description = {
        'data': {
            'type': 'flow',
            'name': name,
            'slug': slug if slug else slugify(name),
            'description': description,
            'enabled': enabled,
        },
    }
    response = requests.post(url, headers=headers, json=flow_description)
    response.raise_for_status()
    return response.json()


def create_flow_field(access_token, flow_id, name, field_type, description,
                      slug=None, required=True, enabled=True, default=None):
    url = 'https://api.moltin.com/v2/fields'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    field_description = {
        'data': {
            'type': 'field',
            'name': name,
            'slug': slug if slug else slugify(name),
            'field_type': field_type,
            'description': description,
            'required': required,
            'enabled': enabled,
            'relationships': {
                'flow': {
                    'data': {
                        'type': 'flow',
                        'id': flow_id,
                    },
                },
            },
        },
    }
    if default:
        field_description['data'].update({'default': default})
    response = requests.post(url, headers=headers, json=field_description)
    response.raise_for_status()
    return response.json()


def create_flow_entry(access_token, flow_slug, fields_slug_per_value: dict):
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    entry_description = {
        'data': {
            'type': 'entry',
            **fields_slug_per_value
        }
    }
    response = requests.post(url, headers=headers, json=entry_description)
    response.raise_for_status()
    return response.json()


def get_entries(access_token, flow_slug, next_page_url=None):
    url = (next_page_url if next_page_url
           else f'https://api.moltin.com/v2/flows/{flow_slug}/entries')
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'page[limit]': 100,
    }
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    return response.json()


def get_available_entries(access_token, flow_slug):
    available_entries = []
    entries = get_entries(access_token, flow_slug=flow_slug)
    available_entries += entries['data']
    while next_page_url := entries['links']['next']:
        entries = get_entries(access_token, flow_slug=flow_slug,
                              next_page_url=next_page_url)
        available_entries += entries['data']
    return available_entries


def get_categories(access_token):
    url = 'https://api.moltin.com/v2/categories'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_category_by_slug(access_token, category_slug):
    url = 'https://api.moltin.com/v2/categories'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'filter': f'eq(slug, {category_slug})'
    }
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    return response.json()
