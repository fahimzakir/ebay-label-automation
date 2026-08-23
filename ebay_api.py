import os
import requests
import json
from datetime import datetime, timedelta
import base64

class EbayClient:
    def __init__(self, token, env='SANDBOX', client_id=None, client_secret=None, refresh_token=None):
        self.token = token
        self.env = env
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        
        if env == 'PRODUCTION':
            self.base_url = "https://api.ebay.com/sell/fulfillment/v1"
            self.oauth_url = "https://api.ebay.com/identity/v1/oauth2/token"
        else:
            self.base_url = "https://api.sandbox.ebay.com/sell/fulfillment/v1"
            self.oauth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def refresh_access_token(self):
        """
        Uses the refresh token to get a new access token from eBay.
        Returns the new access token if successful, otherwise None.
        """
        if not self.refresh_token or not self.client_id or not self.client_secret:
            print("Cannot refresh token: missing refresh_token, client_id, or client_secret.")
            return None

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        try:
            print("Refreshing eBay access token...")
            response = requests.post(self.oauth_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            new_token = token_data.get('access_token')
            if new_token:
                self.token = new_token
                self.headers["Authorization"] = f"Bearer {self.token}"
                print("Access token refreshed successfully.")
                
                # Optionally, here you could write the new token back to your .env file
                # to persist it across program runs.
                
                return new_token
        except requests.exceptions.RequestException as e:
            print(f"Failed to refresh access token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(e.response.text)
                
        return None

    def _execute_request(self, method, url, **kwargs):
        """
        Helper method to execute a request, handling exactly one automatic retry 
        if the access token is expired (401 Unauthorized).
        """
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            if response.status_code == 401:
                print("eBay API returned 401 Unauthorized. Attempting to refresh token...")
                if self.refresh_access_token():
                    # Retry the request with the newly updated self.headers
                    response = requests.request(method, url, headers=self.headers, **kwargs)
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise e

    def get_orders(self):
        """
        Fetches orders that are Paid but Not Shipped.
        filter=orderfulfillmentstatus:{NOT_STARTED|IN_PROGRESS}
        And we likely want to filter by payment status too to ensure paid.
        """
        # The filter syntax is complex. Let's try to get all NOT_STARTED orders.
        # Usually NOT_STARTED means paid but not shipped.
        url = f"{self.base_url}/order"
        params = {
            "filter": "orderfulfillmentstatus:{NOT_STARTED|IN_PROGRESS}",
            "limit": 50
        }
        
        try:
            response = self._execute_request("GET", url, params=params)
            data = response.json()
            orders = data.get('orders', [])
            # enhance filtering if needed client side (e.g. check payment status)
            paid_orders = [o for o in orders if o.get('orderPaymentStatus') == 'PAID']
            return paid_orders
        except requests.exceptions.RequestException as e:
            print(f"Error fetching orders: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(e.response.text)
            return []

    def mark_order_shipped(self, order_id, line_items):
        """
        Marks an order as shipped.
        We need create a Shipping Fulfillment.
        """
        url = f"{self.base_url}/order/{order_id}/shipping_fulfillment"
        
        # Payload for shipping fulfillment
        # Simplified: assumes all items in the order are being shipped
        line_item_refs = [{"lineItemId": item['lineItemId']} for item in line_items]
        
        payload = {
            "lineItems": line_item_refs,
            "shippedDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            # You can add trackingNumber and shippingCarrierCode here if available
        }
        
        try:
            response = self._execute_request("POST", url, json=payload)
            # If successful, returns 201 Created and Location header
            fulfillment_id = response.headers.get('Location', '').split('/')[-1]
            return fulfillment_id
        except requests.exceptions.RequestException as e:
            print(f"Error marking order {order_id} as shipped: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(e.response.text)
            return None
