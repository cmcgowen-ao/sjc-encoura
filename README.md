# Encoura API File Downloader & SFTP Uploader

This script automates the process of:  
1. Authenticating with the **Encoura API**  
2. Downloading available exports  
3. Uploading those exports (CSV files) to a Slate SFTP server  

It is designed for admissions operations workflows that need to regularly pull data from Encoura and move it into Slate.  

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Environment Variables](#environment-variables)
- [Configuration](#configuration)
- [Usage](#usage)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [File Flow](#file-flow)
- [License](#license)

---

## Features

- **Encoura API login** with session token management  
- **File retrieval** for all exports with `status=NotDelivered`  
- **Filename sanitization** to ensure OS-safe naming  
- **Automatic download** of files to a local directory  
- **SFTP upload** to Slate (`ft.technolutions.net`) with cleanup of uploaded files  
- **Comprehensive logging** for troubleshooting and auditing  

---

## Requirements

- Python 3.8+  
- Libraries:  
  - `requests`  
  - `paramiko`  
  - `logging` (standard)  
  - `os`, `re`, `pathlib`, `urllib.parse`, `json` (standard)  

Install dependencies with:  

```bash
pip install requests paramiko
```

---

## Environment Variables

This script relies on environment variables for security. Set them in your shell or environment manager:  

| Variable | Description |
|----------|-------------|
| `ENCOURA_API_KEY` | Encoura API key |
| `ENCOURA_ORGANIZATION_UID` | Encoura organization UID |
| `ENCOURA_USERNAME` | Encoura account username |
| `ENCOURA_PASSWORD` | Encoura account password |
| `SLATE_HALIA_SFTP_UN` | Slate SFTP username |
| `SLATE_HALIA_SFTP_PW` | Slate SFTP password |

---

## Configuration

Inside the script, configure:  

- **Log file path**  
  ```python
  FILENAME = r"[path to log file]"
  ```

- **Download folder**  
  ```python
  DOWNLOAD_DIR = r"[path to download folder]"
  ```

---

## Usage

Run the script directly:  

```bash
python encoura_downloader.py
```

It will:  
1. Open a session with the Encoura API  
2. Log in and fetch available exports  
3. Save the files locally into your configured download directory  
4. Upload `.csv` files to Slate via SFTP (`/incoming/Encoura API Uploads/`)  
5. Delete the local CSVs after successful upload  

---

## Logging

The script writes logs to the configured file (`FILENAME`) with the format:  

```
2025-09-24 08:00:00,123 - download_files - INFO - Downloading file from url ...
```

Logs include:  
- Successful login  
- Files retrieved and saved  
- Upload success/failure messages  
- Error details for troubleshooting  

---

## Error Handling

- **Authentication failures** (Encoura API or SFTP) are logged  
- **Permissions errors** on the SFTP server are logged per file  
- **Other exceptions** (timeouts, connection issues) are caught and recorded  

---

## File Flow

```mermaid
flowchart TD
    A[Encoura API] -->|exports| B[Local Download Folder]
    B -->|*.csv| C[Slate SFTP Server]
    C --> D[Logs + Cleanup]
```

---

## License

This project is provided under the MIT License. See [LICENSE](LICENSE) for details.
