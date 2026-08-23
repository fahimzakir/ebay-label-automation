import json
import os
from datetime import datetime

class OrderLog:
    def __init__(self, filepath="processed_orders.json"):
        self.filepath = filepath
        self.log_data = self._load_log()

    def _load_log(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _save_log(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.log_data, f, indent=4)

    def is_processed(self, order_id):
        return order_id in self.log_data

    def _extract_details(self, order):
        try:
            ship_to = order.get('fulfillmentStartInstructions', [{}])[0].get('shippingStep', {}).get('shipTo', {})
            name = ship_to.get('fullName', '')
            address = ship_to.get('contactAddress', {})
            
            address_parts = [
                address.get('addressLine1', ''),
                address.get('addressLine2', ''),
                address.get('city', ''),
                address.get('stateOrProvince', ''),
                address.get('postalCode', '')
            ]
            address_str = ", ".join([p for p in address_parts if p])
            
            items = []
            for item in order.get('lineItems', []):
                items.append(f"{item.get('quantity', 1)}x {item.get('title', '')}")
                
            return {
                "name": name,
                "address": address_str,
                "items": items
            }
        except Exception as e:
            return {"name": "Error extracting", "address": str(e), "items": []}

    def log_order(self, order_id, source, order_data):
        details = self._extract_details(order_data)
        
        self.log_data[order_id] = {
            "source": source,
            "name": details["name"],
            "address": details["address"],
            "items": details["items"],
            "last_printed": datetime.now().isoformat(),
            "print_count": self.log_data.get(order_id, {}).get("print_count", 0) + 1,
            "raw_data": order_data
        }
        self._save_log()
