import os
import re
import pdfplumber

ATTACHMENTS_DIR = "attachments"

def extract_total(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    # Mouser: "Paid by credit card USD $1,349.34"
    m = re.search(r'Paid by credit card\s+USD\s+\$([0-9,]+\.\d{2})', text)
    if m:
        return m.group(1).replace(",", "")

    # McMaster-Carr: "Total $186.22"
    m = re.search(r'\bTotal\s+\$([0-9,]+\.\d{2})', text)
    if m:
        return m.group(1).replace(",", "")

    # Acme Tools: footer row ending in "BALANCE DUE" then the value on the next line
    m = re.search(r'BALANCE DUE\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([\d.]+)', text)
    if m:
        return m.group(1)

    return None

def insert_total_into_filename(filename, total):
    # Format total as "82_00" style (underscore instead of decimal point)
    total_str = total.replace(".", "_")
    # Insert after the first hyphen-separated segment (the domain prefix)
    parts = filename.split("-", 1)
    if len(parts) == 2:
        return f"{parts[0]}-{total_str}-{parts[1]}"
    return filename

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".svg", ".heic"}

renamed = 0
skipped = 0
failed = 0

for filename in os.listdir(ATTACHMENTS_DIR):
    filepath = os.path.join(ATTACHMENTS_DIR, filename)

    if not os.path.isfile(filepath):
        continue

    ext = os.path.splitext(filename)[1].lower()

    # Delete Tufts files and images
    if filename.startswith("tufts-edu") or ext in IMAGE_EXTENSIONS:
        os.remove(filepath)
        print(f"  ✗ Deleted: {filename}")
        skipped += 1
        continue

    if ext != ".pdf":
        print(f"  ~ Skipped (not PDF): {filename}")
        skipped += 1
        continue

    # Skip files that already have a total inserted
    if re.match(r'^[^-]+-\d+_\d{2}-', filename):
        print(f"  ~ Already renamed: {filename}")
        skipped += 1
        continue

    total = extract_total(filepath)
    if total:
        new_filename = insert_total_into_filename(filename, total)
        new_filepath = os.path.join(ATTACHMENTS_DIR, new_filename)
        os.rename(filepath, new_filepath)
        print(f"  ✓ {filename} → {new_filename}")
        renamed += 1
    else:
        print(f"  ✗ Could not extract total: {filename}")
        failed += 1

print(f"\nDone. Renamed {renamed}, skipped {skipped}, failed {failed}.")
