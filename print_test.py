import os
from dotenv import load_dotenv
from printer_service import PrinterService

def print_test_label():
    load_dotenv()
    printer_addr = os.getenv("PRINTER_ADDRESS")
    
    printer = PrinterService(address=printer_addr)
    printer.connect()
    
    label_path = "test_label.png"
    sender_path = "test_sender_label.png"
    
    if os.path.exists(label_path):
        print(f"Printing {label_path}...")
        printer.print_label(label_path)
    
    if os.path.exists(sender_path):
        print(f"Printing {sender_path}...")
        printer.print_label(sender_path)
    else:
        print(f"Error: {sender_path} does not exist. Run label_generator.py first to create it.")

if __name__ == "__main__":
    print_test_label()
