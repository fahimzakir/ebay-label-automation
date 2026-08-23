# eBay Label Automation Tool

This tool automates the process of fetching paid orders from eBay, generating shipping labels, printing them to a Phomemo printer, and marking the orders as shipped.

## 1. Setup

### Prerequisites
- Python 3.8+
- Phomemo M110 Printer

### Installation
1.  Clone this repository or download the files.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 2. Authentication (eBay API)

To use the eBay API, you need to generate an OAuth token.

1.  **Register as a Developer**: Go to [developer.ebay.com](https://developer.ebay.com) and create an account.
2.  **Create Keys**: Create a **User Access Token** (Authorization Code Grant) for the **Fulfillment API**.
    -   Go to your Application Keys page.
    -   Note your `App ID` (Client ID), `Cert ID` (Client Secret), and `Dev ID`.
3.  **Get User Token**:
    -   Use the [API Explorer](https://developer.ebay.com/my/api_test_tool) or implement an OAuth flow to get a User Access Token.
    -   **Scopes required**: `https://api.ebay.com/oauth/api_scope/sell.fulfillment`
    -   The token will expire after 2 hours. For long-term use, you will need to implement Refresh Token logic (not covered in this basic script, but highly recommended for production).

## 3. Configuration

1.  Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```
2.  Open `.env` and fill in your eBay credentials and Printer details.
    -   `EBAY_USER_TOKEN`: Paste your OAuth token here.

## 4. Usage

Run the main script:

```bash
python main.py
```

The script will:
1.  Fetch "Paid" and "Not Shipped" orders.
2.  Generate a 50x80mm label image for each.
3.  Send the image to the configured Phomemo printer.
4.  Mark the order as Shipped on eBay.

source /Users/fahimzakir/Desktop/projects/ebay-label-automation/.venv/bin/activate 
