def parse_cart(cart):
    total_price = cart['meta']['display_price']['with_tax']['formatted']
    cart_description = []

    for cart_item in cart['data']:
        item_id = cart_item['id']
        item_name = cart_item['name']
        item_description = cart_item['description']
        item_quantity = cart_item['quantity']
        item_price = cart_item['meta']['display_price']['with_tax']
        item_unit_price = item_price['unit']['formatted']
        item_value_price = item_price['value']['formatted']

        cart_item_description = {
            'id': item_id,
            'name': item_name,
            'description': item_description,
            'quantity': item_quantity,
            'unit_price': item_unit_price,
            'value_price': item_value_price
        }
        cart_description.append(cart_item_description)
    return {
        'total_price': total_price,
        'cart_description': cart_description
    }
