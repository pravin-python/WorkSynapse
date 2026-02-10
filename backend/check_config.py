 co from app.agents.orchestrator.config import get_orchestrator_config

def check_config():
    config = get_orchestrator_config()
    
    # Check if google provider config is available
    google_config = config.get_provider_config("google")
    if google_config:
        print(f"SUCCESS: 'google' provider config found. API Key Present: {bool(google_config.api_key)}")
        print(f"Config Name: {google_config.name}")
    else:
        print("FAILURE: 'google' provider config NOT found.")
        
    # Check available providers list
    available = config.get_available_providers()
    print(f"Available Providers: {available}")
    
    if "google" in available:
        print("SUCCESS: 'google' is in available providers.")
    else:
        if config.google_api_key:
            print("FAILURE: 'google' should be in available providers but isn't.")
        else:
            print("INFO: 'google' not in available providers (no API key currently set, or env var missing).")

if __name__ == "__main__":
    check_config()
