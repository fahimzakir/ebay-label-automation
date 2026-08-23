import os
import time
from dotenv import load_dotenv
from ebay_api import EbayClient
from label_generator import LabelGenerator
from printer_service import PrinterService
from order_log import OrderLog

# Load environment variables
load_dotenv()

def main(skip_processed_order=True):
    # Configuration
    EBAY_TOKEN = os.getenv("EBAY_USER_TOKEN")
    EBAY_REFRESH_TOKEN = os.getenv("EBAY_REFRESH_TOKEN")
    EBAY_APP_ID = os.getenv("EBAY_APP_ID")
    EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")
    EBAY_ENV = os.getenv("EBAY_API_ENV", "SANDBOX")
    PRINTER_ADDR = os.getenv("PRINTER_ADDRESS")

    if not EBAY_TOKEN and not EBAY_REFRESH_TOKEN:
        print("Error: Neither EBAY_USER_TOKEN nor EBAY_REFRESH_TOKEN found in environment variables.")
        return

    # Initialize Services
    ebay = EbayClient(
        token=EBAY_TOKEN, 
        env=EBAY_ENV, 
        client_id=EBAY_APP_ID, 
        client_secret=EBAY_CERT_ID, 
        refresh_token=EBAY_REFRESH_TOKEN
    )
    label_gen = LabelGenerator(width_mm=80, height_mm=50)
    printer = PrinterService(address=PRINTER_ADDR)
    order_log = OrderLog()
    
    # Connect to printer
    printer.connect()

    print("Fetching orders...")
    orders = ebay.get_orders()
    
    if not orders:
        print("No paid, unshipped orders found.")
        return

    print(f"Found {len(orders)} orders to process.")

    for order in orders:
        order_id = order.get('orderId')
        print(f"Processing Order ID: {order_id}")

        
        if skip_processed_order and order_log.is_processed(order_id):
            print(f"  Order {order_id} already processed. Skipping.")
            print("-" * 30)
            continue
        
        # 1. Generate Labels
        label_filename = f"label_{order_id}.png"
        sender_filename = f"sender_{order_id}.png"
        try:
            path = label_gen.create_label(order, label_filename)
            sender_path = label_gen.create_sender_label(sender_filename, order_data=order)
            print(f"  Labels generated: {path}, {sender_path}")
        except Exception as e:
            print(f"  Failed to generate labels: {e}")
            continue

        #2. Print Labels
        if printer.print_label(path) and printer.print_label(sender_path):
            print("  Labels printed successfully.")
            
            # 3. Mark as Shipped
            # Only mark as shipped if printing was successful
            print("  Marking as shipped on eBay...")
            line_items = order.get('lineItems', [])
            fulfillment_id = ebay.mark_order_shipped(order_id, line_items)
            
            if fulfillment_id:
               print(f"  Order {order_id} marked as shipped! Fulfillment ID: {fulfillment_id}")
            else:
               print(f"  Failed to mark order {order_id} as shipped.")
               
            order_log.log_order(order_id, "eBay", order)
        else:
           print("  Printing failed. Skipping mark-as-shipped.")

        # cleanup
        os.remove(path) 
        os.remove(sender_path)
        print("-" * 30)

if __name__ == "__main__":
    main()
