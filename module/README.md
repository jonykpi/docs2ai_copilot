# Docs2AI Upload for Odoo

Docs2AI Upload lets Odoo finance teams push vendor bills (PDF or images) straight to the Docs2AI service, trigger OCR + extraction, and keep traceability from the bill form. This guide explains how to install the addon from the public repository, configure Odoo, and run the daily workflow.

---

## 1. Prerequisites

- Odoo 16.0+ (tested on 19.0) with shell access.
- PostgreSQL user that matches your `odoo.conf` (commonly `odoo`).
- Docs2AI API credentials (API token and folder/company identifiers).
- Git installed on the server.

---

## 2. Installation

### Option A – Clone straight into an addons path

```bash
git clone git@github.com:jonykpi/docs2ai_copilot.git docs2ai_copilot
```

### Option B – Download with `curl` (no git required)

```bash
cd /path/to/your/custom/addons        # must be a directory already in addons_path
curl -L https://github.com/jonykpi/docs2ai_copilot/archive/refs/heads/main.zip -o docs2ai_copilot.zip
unzip docs2ai_copilot.zip
mv docs2ai_copilot-main docs2ai_copilot
```

Staying inside that addons directory ensures Odoo already points at the new module. After extracting, go to Apps ▸ Developer Mode ▸ **Update Apps List**.

### Option C – Package into a ZIP from an existing checkout

1. From your working copy run `package_docs2ai_module.sh` (provided in this repo) which creates `docs2ai_copilot.zip`.
2. Extract the archive into an addons directory or copy the folder to the target server.

### Update `odoo.conf`

In whatever config Odoo actually loads (e.g. `/etc/odoo/odoo.conf` or the project-local file), append the folder to `addons_path`:

```
addons_path = /odoo/odoo/addons,/opt/odoo/custom/addons,/opt/odoo/addons/docs2ai_copilot
```

Restart Odoo so the new path is scanned.

---

## 3. Install the module inside Odoo

1. Enable Developer Mode.
2. Apps ▸ Update Apps List ▸ search for **Docs2AI Upload**.
3. Click **Install**.

If you prefer CLI:

```bash
./odoo-bin -c odoo.conf -d <database> -u docs2ai_copilot
```

---

## 4. Configuration

Navigate to **Settings ▸ Docs2AI Upload** (or *Accounting ▸ Configuration ▸ Docs2AI*).

Fill in:

- **Docs2AI API URL** – e.g. `https://backend.docs2ai.co/api/enterprise/<folder_id>/send-file-doc2ai`
- **API Token** – Bearer token issued by Docs2AI.
- **Default Folder / Company IDs** – used on every upload unless a user overrides them.

Save and, if asked, allow Odoo to restart accounting assets.

---

## 5. Daily workflow

1. Open a vendor bill (`account.move` of type *in_invoice*).
2. Click **Upload to Docs2AI**.
3. Choose the PDF or image from your machine.
4. Confirm – the wizard sends the document to Docs2AI and shows the queued job ID returned by the API.
5. Monitor processing status from Docs2AI; once processed you can reconcile or attach the extracted data manually.

---

## 6. Troubleshooting

| Symptom | Fix |
| --- | --- |
| Module missing from Apps list | Ensure the folder name is `docs2ai_copilot`, `application = True` in `__manifest__.py`, refresh Apps list. |
| Import Module wizard fails on `model_docs2ai_copilot_wizard` | Use git/CLI installation; the Import wizard cannot load Python models. |
| `FATAL: role "odoo" does not exist` | Recreate the PostgreSQL role or edit `db_user` in `odoo.conf`. |
| `Invalid module name: docs2ai-oddo` | Do not leave hyphenated folders in `addons_path`. Rename the folder to `docs2ai_copilot`. |

---

## 7. Repository & contributions

Source code and issues live at [github.com/jonykpi/docs2ai-oddo][repo]. Feel free to open issues or PRs for bugfixes and feature requests.

[repo]: https://github.com/jonykpi/docs2ai-oddo
