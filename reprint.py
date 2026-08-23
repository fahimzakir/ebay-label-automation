import os
import sys
from dotenv import load_dotenv

from order_log import OrderLog
from label_generator import LabelGenerator
from printer_service import PrinterService

# Load environment variables
load_dotenv()

def main():
    if len(sys.argv) < 2:
        print("Usage: python reprint.py <order_id>")
        print("\nAvailable orders in log:")
        
        # List the last few printed orders to help the user
        order_log = OrderLog()
        if not order_log.log_data:
            print("  Log is empty.")
            return
            
        # Sort by last printed
        sorted_orders = sorted(order_log.log_data.items(), key=lambda x: x[1].get('last_printed', ''), reverse=True)
        for order_id, info in sorted_orders[:10]: # show top 10
            print(f"  - {order_id}: {info.get('name', 'Unknown')} | {info.get('source', 'Unknown')} | Printed {info.get('print_count', 0)}x")
        return

    target_order_id = sys.argv[1]
    order_log = OrderLog()
    
    if target_order_id not in order_log.log_data:
        print(f"Error: Order ID '{target_order_id}' not found in the log.")
        return
        
    entry = order_log.log_data[target_order_id]
    
    # Check if we have raw data
    raw_data = entry.get("raw_data")
    if not raw_data:
        print(f"Error: No raw data found for order '{target_order_id}'.")
        print("This order was logged before raw data storage was enabled. Cannot automatically reprint.")
        return
        
    print(f"Reprinting order: {target_order_id} ({entry.get('name', 'Unknown')})")
    
    # Initialize services
    PRINTER_ADDR = os.getenv("PRINTER_ADDRESS")
    label_gen = LabelGenerator(width_mm=80, height_mm=50)
    printer = PrinterService(address=PRINTER_ADDR)
    
    printer.connect()
    
    # Generate labels
    label_filename = f"reprint_label_{target_order_id}.png"
    sender_filename = f"reprint_sender_{target_order_id}.png"
    
    try:
        path = label_gen.create_label(raw_data, label_filename)
        sender_path = label_gen.create_sender_label(sender_filename, order_data=raw_data)
        print(f"Labels generated for reprint.")
    except Exception as e:
        print(f"Failed to generate labels for {target_order_id}: {e}")
        return

    # Print labels
    if printer.print_label(path) and printer.print_label(sender_path):
        print("Labels printed successfully.")
        
        # Update log print count and timestamp
        order_log.log_order(target_order_id, entry.get("source"), raw_data)
        print("Log updated with new print timestamp and count.")
    else:
        print("Printing failed.")

    # Cleanup
    try:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(sender_path): os.remove(sender_path)
    except Exception:
        pass

if __name__ == "__main__":
    main()
