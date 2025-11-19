import json
import os
from hubspot_pz import HubspotPZ
from mailer_pz import MailerPZ

# Path to the secrets file inside the container
SECRETS_FILE = "/app/data/secrets.json"

class SecretsManager:
    def __init__(self):
        self._secrets = {}
        self._hubspot = None
        self._mailer = None
        self.load_secrets()

    def load_secrets(self):
        """Load secrets from JSON file or env vars if file doesn't exist."""
        if os.path.exists(SECRETS_FILE):
            try:
                with open(SECRETS_FILE, 'r') as f:
                    self._secrets = json.load(f)
            except json.JSONDecodeError:
                print(f"Error decoding {SECRETS_FILE}, falling back to empty secrets.")
                self._secrets = {}
        else:
            # Fallback to env vars if file doesn't exist (first run)
            print(f"{SECRETS_FILE} not found, initializing from environment variables.")
            self._secrets = {
                "INFO_EMAIL_NAME": os.getenv("INFO_EMAIL_NAME", ""),
                "INFO_EMAIL_ADDRESS": os.getenv("INFO_EMAIL_ADDRESS", ""),
                "INFO_EMAIL_PASSWORD": os.getenv("INFO_EMAIL_PASSWORD", ""),
                "HUBSPOT_AGENT_ASSIGNMENT_TOKEN": os.getenv("HUBSPOT_AGENT_ASSIGNMENT_TOKEN", "")
            }
            # Ensure directory exists before saving
            os.makedirs(os.path.dirname(SECRETS_FILE), exist_ok=True)
            self.save_secrets(self._secrets)
        
        self._reset_instances()

    def save_secrets(self, new_secrets):
        """Save secrets to JSON file and reset instances."""
        self._secrets = new_secrets
        try:
            with open(SECRETS_FILE, 'w') as f:
                json.dump(self._secrets, f, indent=4)
            self._reset_instances()
        except Exception as e:
            print(f"Error saving secrets to {SECRETS_FILE}: {e}")

    def _reset_instances(self):
        """Clear cached instances to force recreation with new secrets."""
        self._hubspot = None
        self._mailer = None

    def get_secret(self, key, default=None):
        return self._secrets.get(key, default)
    
    def get_all_secrets(self):
        return self._secrets

    def get_hubspot(self):
        if not self._hubspot:
            token = self.get_secret("HUBSPOT_AGENT_ASSIGNMENT_TOKEN")
            if token:
                self._hubspot = HubspotPZ(token)
        return self._hubspot

    def get_mailer(self):
        if not self._mailer:
            name = self.get_secret("INFO_EMAIL_NAME")
            address = self.get_secret("INFO_EMAIL_ADDRESS")
            password = self.get_secret("INFO_EMAIL_PASSWORD")
            if name and address and password:
                self._mailer = MailerPZ(name, address, password)
        return self._mailer

# Global instance
secrets_manager = SecretsManager()
