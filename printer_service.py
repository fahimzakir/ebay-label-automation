import subprocess

class PrinterService:
    def __init__(self, address=None):
        # The user's printer is registered as '_M110S' in macOS CUPS.
        # We can optionally allow overriding this via the address variable in .env
        match = address if address and "M110" in address else "_M110S"
        self.printer_name = match

    def connect(self):
        """
        Since the printer is mapped as a system printer via USB, 
        we don't need to manually maintain a socket or BLE connection.
        We just check if it's available via macOS commandline tools.
        """
        print(f"Configured to print natively via macOS USB using printer: {self.printer_name}")
        try:
            # lpstat checks if print service is active
            result = subprocess.run(["lpstat", "-p", self.printer_name], capture_output=True, text=True)
            if self.printer_name in result.stdout:
                print("Printer found and ready!")
            else:
                print(f"Warning: Printer {self.printer_name} might not be ready, but we will still attempt to print.")
        except Exception as e:
             print(f"Could not verify printer status: {e}")

    def print_label(self, image_path):
        """
        Send the generated PNG label straight to the macOS CUPS queue using `lp`.
        """
        print(f"Sending {image_path} via USB to macOS printer {self.printer_name}...")
        try:
            # Options like fit-to-page might be helpful since it's an image.
            # `lp -d [Printer_Name] -o fit-to-page image.png`
            cmd = ["lp", "-d", self.printer_name, "-o", "fit-to-page", image_path]
            subprocess.run(cmd, check=True)
            
            print("Print job submitted successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to submit print job: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error printing: {e}")
            return False
