import msal
import requests
import os
import re
import base64
from datetime import datetime, timedelta, timezone

# --- Config ---
client_id = "CLIENT ID GOES HERE"
tenant_id = "TENANT ID GOES HERE"
DOWNLOAD_DIR = "attachments"

# --- Auth ---
authority = f"https://login.microsoftonline.com/{tenant_id}"
app = msal.PublicClientApplication(client_id, authority=authority)
flow = app.initiate_device_flow(scopes=["Mail.Read"])
print(flow["message"])
result = app.acquire_token_by_device_flow(flow)
access_token = result["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}

# --- Setup ---
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
six_months_ago = (datetime.now(timezone.utc) - timedelta(days=182)).strftime("%Y-%m-%dT%H:%M:%SZ")

# --- Fetch emails with attachments, paginating through all results ---
url = (
    "https://graph.microsoft.com/v1.0/me/messages"
    f"?$filter=hasAttachments eq true and receivedDateTime ge {six_months_ago}"
    "&$select=id,subject,receivedDateTime,hasAttachments,from"
    "&$top=50"
)

total_emails = 0
total_attachments = 0
skipped = 0

while url:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    messages = data.get("value", [])
    total_emails += len(messages)

    for message in messages:
        msg_id = message["id"]
        subject = message.get("subject", "No Subject")
        received = message.get("receivedDateTime", "")

        sender = message.get("from", {}).get("emailAddress", {}).get("address", "")
        domain = sender.split("@")[-1].lower() if "@" in sender else "unknown"
        domain_prefix = re.sub(r"[^a-z0-9-]", "-", domain)  # e.g. "amazon.com" → "amazon-com"

        # Fetch attachments for this email
        attach_url = f"https://graph.microsoft.com/v1.0/me/messages/{msg_id}/attachments"
        attach_response = requests.get(attach_url, headers=headers)
        attach_response.raise_for_status()
        attachments = attach_response.json().get("value", [])

        for attachment in attachments:
            # Skip inline/embedded attachments (e.g. inline images)
            if attachment.get("isInline", False):
                skipped += 1
                continue

            # Only handle file attachments (not item/reference attachments)
            if attachment.get("@odata.type") != "#microsoft.graph.fileAttachment":
                skipped += 1
                continue

            filename = attachment.get("name", "unknown_file")
            content_bytes = attachment.get("contentBytes")  # base64-encoded

            if not content_bytes:
                skipped += 1
                continue

            # Sanitize filename and build a unique path using domain and received date prefix
            safe_name = re.sub(r"[^a-zA-Z0-9.-]", "-", filename)  # replace spaces/underscores/etc with hyphens
            date_prefix = received[:10]  # "YYYY-MM-DD"
            save_path = os.path.join(DOWNLOAD_DIR, f"{domain_prefix}-{date_prefix}-{safe_name}")

            # Avoid overwriting duplicates
            counter = 1
            base, ext = os.path.splitext(save_path)
            while os.path.exists(save_path):
                save_path = f"{base}-{counter}{ext}"
                counter += 1

            with open(save_path, "wb") as f:
                f.write(base64.b64decode(content_bytes))

            print(f"  ✓ Saved: {save_path}  (from: '{subject}' on {received[:10]})")
            total_attachments += 1

    # Follow pagination if there are more results
    url = data.get("@odata.nextLink")

print(f"\nDone. Scanned {total_emails} emails, saved {total_attachments} attachments, skipped {skipped}.")
