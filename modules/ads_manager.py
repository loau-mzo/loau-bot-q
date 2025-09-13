from database import db

AD_KEY = "current_ad"

def add_ad(ad_text: str):
    """Saves or updates the advertisement text."""
    db.set_setting(AD_KEY, ad_text)
    return True, "Advertisement has been set."

def view_ad():
    """Retrieves the current advertisement text."""
    ad_text = db.get_setting(AD_KEY)
    if ad_text:
        return ad_text
    return "No advertisement is currently set."

def delete_ad():
    """Deletes the current advertisement."""
    if db.get_setting(AD_KEY):
        db.delete_setting(AD_KEY)
        return True, "Advertisement has been deleted."
    return False, "No advertisement to delete."
