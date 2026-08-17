Some Python scripts for downloading receipts from my email

Almost surely not useful for you.

## Reminder of how this works

1. Whereever you're going to run this, make an empty directory called `attachments`. If it already exists, it would be wise to move all the old files to some archive.
2. Run `download-attachments.py`, which will prompt you to open a browser to authenticate with Tufts SSO.
3. Wait while a bunch of attachments are downloaded.
4. Run `filter-and-rename-invoices.py`.
5. Delete the garbage files that slip through, mostly PDFs that aren't actually receipts.

Consider asking Claude or one of his generous friends to write code that finds transactions in Peoplesoft and uploads matching receipts. Probably not worth the 3 hours per year it would save.
