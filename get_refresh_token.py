import os
import requests
import base64
import urllib.parse
from dotenv import load_dotenv

def main():
    load_dotenv()

    app_id = os.getenv("EBAY_APP_ID")
    cert_id = os.getenv("EBAY_CERT_ID")
    runame = os.getenv("EBAY_RUNAME")
    env = os.getenv("EBAY_API_ENV", "SANDBOX")

    if not all([app_id, cert_id, runame]):
        print("Error: Missing required environment variables.")
        print("Please ensure EBAY_APP_ID, EBAY_CERT_ID, and EBAY_RUNAME are set in your .env file.")
        print("You can find your RuName (Redirect URL name) in the eBay Developer Portal under 'User Tokens'.")
        return

    # Set up endpoints and scopes based on the environment
    if env == 'PRODUCTION':
        auth_url_base = "https://auth.ebay.com/oauth2/authorize"
        token_url = "https://api.ebay.com/identity/v1/oauth2/token"
    else:
        auth_url_base = "https://auth.sandbox.ebay.com/oauth2/authorize"
        token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

    # Scopes needed for order fulfillment operations
    scopes = [
        "https://api.ebay.com/oauth/api_scope",
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly"
    ]
    scope_str = " ".join(scopes)

    # 1. Generate the Authorization URL
    params = {
        "client_id": app_id,
        "redirect_uri": runame,
        "response_type": "code",
        "scope": scope_str,
        "prompt": "login"
    }
    
    auth_url = f"{auth_url_base}?{urllib.parse.urlencode(params)}"
    
    print("="*60)
    print("STEP 1: USER CONSENT")
    print("="*60)
    print("Please click the following link to log in and authorize your application:")
    print(f"\n{auth_url}\n")
    print("After you agree, you will be redirected to a new URL.")
    print("The URL will look something like this:")
    print("https://your-redirect-domain.com/?code=v^1.1#i^1#...&expires_in=299")
    print("="*60)
    
    # 2. Extract Authorization Code from User
    auth_code_url = input("\nSTEP 2: Paste the FULL REDIRECTED URL here: ").strip()
    
    try:
        # Extract the 'code' parameter from the pasted URL
        parsed_url = urllib.parse.urlparse(auth_code_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        auth_code = query_params.get('code', [None])[0]
        
        if not auth_code:
            print("Error: Could not extract the authorization code from the URL.")
            return
            
        print("\nAuthorization code extracted successfully!")
    except Exception as e:
        print(f"Error parsing URL: {e}")
        return

    # 3. Exchange Authorization Code for Refresh Token
    print("\nSTEP 3: Exchanging authorization code for tokens...")
    
    credentials = f"{app_id}:{cert_id}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": runame
    }

    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        print("\n" + "="*60)
        print("SUCCESS! Your tokens have been generated.")
        print("="*60)
        
        print("\n[ACCESS TOKEN] (Valid for 2 hours):")
        print(token_data.get('access_token'))
        
        print("\n[REFRESH TOKEN] (Valid for 18 months - SAVE THIS):")
        refresh_token = token_data.get('refresh_token')
        print(refresh_token)
        print("\n" + "="*60)
        print("ACTION REQUIRED:")
        print("Copy the [REFRESH TOKEN] above and paste it into your .env file as EBAY_REFRESH_TOKEN.")
        print("Your automation script will handle everything else automatically!")

    except requests.exceptions.RequestException as e:
        print("\nFailed to exchange token. Error from eBay:")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)
        else:
            print(str(e))

if __name__ == "__main__":
    main()
