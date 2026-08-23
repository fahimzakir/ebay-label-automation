import os
import re
import sys
import pdfplumber
from dotenv import load_dotenv

from label_generator import LabelGenerator
from printer_service import PrinterService
from order_log import OrderLog

# Load environment variables for printer address
load_dotenv()

def parse_pdf(file_path):
    orders = []
    
    # We use pdfplumber to accurately extract text from the PDF
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # --- Extract Address ---
            # Look for block between "Ship To:\n" and "Order ID:"
            ship_to_match = re.search(r"Ship To:\n(.*?)\nOrder ID:", text, re.DOTALL)
            if not ship_to_match:
                print(f"Warning: Could not find shipping address on page {i+1}")
                continue
                
            lines = ship_to_match.group(1).strip().split('\n')
            name = lines[0]
            # Extract Address components from remaining lines
            address_block = lines[1:]
            address_line1 = ""
            address_line2 = ""
            city = ""
            state_prov = ""
            postal = ""

            if address_block:
                last_line = address_block[-1]
                # Try to parse City, State Zip from last line (e.g. 'GOSNELLS, WA 6110' or 'GOSNELLS WA 6110')
                match = re.search(r"^(.*?)[,\s]+([A-Z]{2,3})\s+(\d{4,5})$", last_line)
                
                if match:
                    city = match.group(1).strip()
                    state_prov = match.group(2).strip()
                    postal = match.group(3).strip()
                    rest = address_block[:-1]
                else:
                    rest = address_block

                if len(rest) == 1:
                    address_line1 = rest[0]
                elif len(rest) >= 2:
                    address_line1 = rest[0]
                    address_line2 = " ".join(rest[1:])
            
            # --- Extract Order ID ---
            order_idx = re.search(r"Order ID: ([\d-]+)", text)
            order_id = order_idx.group(1) if order_idx else f"UNK_{i}"
            
            # --- Extract Item Details ---
            # Try to find the quantity and title below column headers
            qty = 1
            title = "Item"
            item_match = re.search(r"Quantity Product details Unit price Order totals\n(\d+)\s+(.*?)\n(?:SKU|ASIN):", text, re.DOTALL)
            if item_match:
                qty = int(item_match.group(1))
                title = item_match.group(2).replace("\n", " ").strip()
                
            # Build the order dict matching what LabelGenerator expects
            order_data = {
                'orderId': order_id,
                'fulfillmentStartInstructions': [{
                    'shippingStep': {
                        'shipTo': {
                            'fullName': name,
                            'contactAddress': {
                                # Use the intelligently parsed fields
                                'addressLine1': address_line1,
                                'addressLine2': address_line2,
                                'city': city,
                                'stateOrProvince': state_prov,
                                'postalCode': postal,
                                'countryCode': 'AU'
                            }
                        }
                    }
                }],
                'lineItems': [
                    {
                        'quantity': qty,
                        'title': title
                    }
                ]
            }
            
            orders.append(order_data)
            
    return orders

def main(skip_processed_order=True):
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "amazon orders/Amazon orders.pdf"
        
    full_path = os.path.abspath(pdf_path)
    
    if not os.path.exists(full_path):
        print(f"Error: PDF file not found at {full_path}")
        return

    print("Parsing Amazon Packing Slips...")
    orders = parse_pdf(full_path)
    
    if not orders:
        print("No orders extracted from the PDF.")
        return
        
    print(f"Successfully extracted {len(orders)} orders.")
    
    # Initialize Label Generator and Printer
    PRINTER_ADDR = os.getenv("PRINTER_ADDRESS")
    label_gen = LabelGenerator(width_mm=80, height_mm=50)
    printer = PrinterService(address=PRINTER_ADDR)
    order_log = OrderLog()
    
    # Connect Printer
    printer.connect()
    
    for order in orders:
        order_id = order.get('orderId')
        print(f"Processing Order: {order_id}")
        
        if skip_processed_order and order_log.is_processed(order_id):
            print(f"  Order {order_id} already processed. Skipping.")
            print("-" * 30)
            continue
            
        
        label_filename = f"amazon_label_{order_id}.png"
        sender_filename = f"amazon_sender_{order_id}.png"
        
        try:
            path = label_gen.create_label(order, label_filename)
            sender_path = label_gen.create_sender_label(sender_filename, order_data=order)
            print(f"  Labels generated: {path}, {sender_path}")
        except Exception as e:
            print(f"  Failed to generate labels for {order_id}: {e}")
            continue

        if printer.print_label(path) and printer.print_label(sender_path):
            print("  Labels printed successfully.")
            order_log.log_order(order_id, "Amazon", order)
        else:
            print("  Printing failed for this order.")
            
        # Cleanup
        try:
            if os.path.exists(path): os.remove(path)
            if os.path.exists(sender_path): os.remove(sender_path)
        except Exception as e:
            pass
            
        print("-" * 30)

if __name__ == "__main__":
    main()
