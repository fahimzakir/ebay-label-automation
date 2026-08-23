from PIL import Image, ImageDraw, ImageFont
import textwrap

class LabelGenerator:
    def __init__(self, width_mm=70, height_mm=50, dpi=203):
        self.width_px = int(width_mm * dpi / 25.4)
        self.height_px = int(height_mm * dpi / 25.4)
        self.dpi = dpi
        
    def create_label(self, order_data, output_path):
        """
        Generates a shipping label image from order data.
        """
        # Create a new white image (1-bit strictly black and white for thermal printers)
        image = Image.new('1', (self.width_px, self.height_px), 1)  # 1 is white in '1' mode
        draw = ImageDraw.Draw(image)
        
        # Load fonts - using default if system fonts not easily accessible, 
        # but robust implementation would load TTF.
        try:
            # Try to load a truetype font
            font_large = ImageFont.truetype("Arial.ttf", 48)
            font_medium = ImageFont.truetype("Arial.ttf", 36)
            font_small = ImageFont.truetype("Arial.ttf", 30)
        except IOError:
            # Fallback to default
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Extract address info
        # Structure depends on eBay API response for 'fulfillmentStartInstructions'
        instructions = order_data.get('fulfillmentStartInstructions', [{}])[0]
        shipping_step = instructions.get('shippingStep', {})
        ship_to = shipping_step.get('shipTo', {})
        recipient = ship_to.get('fullName', 'Valued Customer')
        contact_address = ship_to.get('contactAddress', {})
        
        address_line1 = contact_address.get('addressLine1', '')
        address_line2 = contact_address.get('addressLine2', '')
        city = contact_address.get('city', '')
        state = contact_address.get('stateOrProvince', '')
        postal_code = contact_address.get('postalCode', '')
        country = contact_address.get('countryCode', '')

        # Draw content
        y = 20
        margin = 30
        
        draw.text((margin, y), "To:", font=font_medium, fill=0)
        y += 40
        
        # Recipient Name
        for wrapped_line in textwrap.wrap(recipient, width=22):
            draw.text((margin, y), wrapped_line, font=font_large, fill=0)
            y += 55
        
        # Address - Filtering out eBay tracking/reference IDs
        for line in (address_line1, address_line2):
            if line and not line.lower().startswith('ebay:'):
                for wrapped_addr in textwrap.wrap(line, width=28):
                    draw.text((margin, y), wrapped_addr, font=font_medium, fill=0)
                    y += 45
            
        full_city_state = ""
        if city or state or postal_code:
            city_str = f"{city}, " if city else ""
            full_city_state = f"{city_str}{state} {postal_code}".strip()
            # If it's just a dangling comma for some reason, clean it up
            if full_city_state.endswith(','):
                full_city_state = full_city_state[:-1]
                
        if full_city_state:
            for wrapped_city in textwrap.wrap(full_city_state, width=28):
                draw.text((margin, y), wrapped_city, font=font_medium, fill=0)
                y += 45
        
        for wrapped_country in textwrap.wrap(country, width=28):
            draw.text((margin, y), wrapped_country, font=font_medium, fill=0)
            y += 45
            
        # Rotate for landscape printing on a 50mm width roll
        image = image.transpose(Image.ROTATE_90)
        
        # Save image
        image.save(output_path)
        return output_path

    def create_sender_label(self, output_path, order_data=None):
        """
        Generates a fixed shipping label for the sender.
        Optionally includes a product tracking hint if order_data is provided.
        """
        image = Image.new('1', (self.width_px, self.height_px), 1)
        draw = ImageDraw.Draw(image)
        
        try:
            font_large = ImageFont.truetype("Arial.ttf", 48)
            font_medium = ImageFont.truetype("Arial.ttf", 36)
            font_small = ImageFont.truetype("Arial.ttf", 30)
        except IOError:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        y = 20
        margin = 30

        draw.text((margin, y), "From:", font=font_medium, fill=0)
        y += 40

        # Sender Name
        draw.text((margin, y), "FZ Solution", font=font_large, fill=0)
        y += 55
        
        # Address
        draw.text((margin, y), "U601", font=font_medium, fill=0)
        y += 45
        draw.text((margin, y), "164 great western highway", font=font_medium, fill=0)
        y += 45
        draw.text((margin, y), "Westmead, NSW-2145", font=font_medium, fill=0)
        
        # Product Hint
        if order_data:
            line_items = order_data.get('lineItems', [])
            if line_items:
                # Grab details from the first item
                first_item = line_items[0]
                qty = first_item.get('quantity', 1)
                title = first_item.get('title', 'Item')
                
                title_lower = title.lower()
                
                # Check if it's the Uber/Rideshare sign
                if any(kw in title_lower for kw in ['uber', 'ubur', 'rideshare', 'didi']):
                    if 'non reflective' in title_lower or 'non-reflective' in title_lower:
                        variation = 'Standard'
                    elif 'reflective' in title_lower:
                        variation = 'Reflective'
                    else:
                        variation = 'Standard'
                    extra = " (+More)" if len(line_items) > 1 else ""
                    hint_str = f"[{qty} * Uber ({variation}){extra}]"
                else:
                    # We'll take just the first 3 words of the title to keep the hint brief
                    short_title = " ".join(title.split()[:3])
                    
                    # If there are multiple unique items, we can indicate that too
                    extra = " (+More)" if len(line_items) > 1 else ""
                    hint_str = f"[{qty}x {short_title}{extra}]"
                
                y += 65
                draw.text((margin, y), hint_str, font=font_small, fill=0)

        # Rotate for landscape printing on a 50mm width roll
        image = image.transpose(Image.ROTATE_90)
        
        # Save image
        image.save(output_path)
        return output_path

if __name__ == "__main__":
    # Test
    gen = LabelGenerator()
    dummy_data = {
        'orderId': '12345',
        'fulfillmentStartInstructions': [{
            'shippingStep': {
                'shipTo': {
                    'fullName': 'John Doe',
                    'contactAddress': {
                        'addressLine1': '123 Main St',
                        'city': 'New York',
                        'stateOrProvince': 'NY',
                        'postalCode': '10001',
                        'countryCode': 'US'
                    }
                }
            }
        }],
        'lineItems': [
            {
                'quantity': 2,
                'title': 'Rideshare Car Sign for Uber and DiDi, Black, Reflective, Square'
            }
        ]
    }
    
    gen.create_label(dummy_data, "test_label.png")
    gen.create_sender_label("test_sender_label.png", order_data=dummy_data)
    print("Test labels generated: test_label.png, test_sender_label.png")
