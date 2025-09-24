import requests
import json
import os
import re
import logging
import paramiko
from urllib.parse import urlparse, unquote
from pathlib import Path

# Set up logging
FILENAME = r"[path to log file]"
LEVEL = logging.INFO
FORMAT = "%(asctime)s - %(funcName)s - %(levelname)s - %(message)s"
logging.basicConfig(filename=FILENAME, level=LEVEL, format=FORMAT)

# API configuration
ENCORA_URL = "https://api-datalab.encoura.org/v1"
ENCOURA_API_KEY = os.environ.get("ENCOURA_API_KEY")
ENCOURA_ORGANIZATION_UID = os.environ.get("ENCOURA_ORGANIZATION_UID")

# File download configuration
DOWNLOAD_DIR = r"[path to download folder]"
DOWNLOAD_DIR = Path(DOWNLOAD_DIR)

# Authentication credentials
ENCOURA_USERNAME = os.environ.get("ENCOURA_USERNAME")
ENCOURA_PASSWORD = os.environ.get("ENCOURA_PASSWORD")
SLATE_HALIA_SFTP_UN = os.environ.get("SLATE_HALIA_SFTP_UN")
SLATE_HALIA_SFTP_PW = os.environ.get("SLATE_HALIA_SFTP_PW")

def get_valid_filename(s):
    """
    Returns a valid filename by removing any invalid characters and replacing spaces with underscores.

    Args:
        s (str): The input string to be converted into a valid filename.

    Returns:
        str: The valid filename.

    """
    s = str(s).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", "", s)

def login(session):
    """
    Logs in to the ENCOURA API using the provided session.

    Parameters:
    session (object): The session object used for making API requests.

    Returns:
    None
    """
    payload = {"userName": ENCOURA_USERNAME, "password": ENCOURA_PASSWORD, "acceptedTerms": True}
    response_json = session.post(f"{ENCORA_URL}/login", data=json.dumps(payload)).json()
    if "sessionToken" not in response_json:
        logging.error(f"Couldn't find sessionToken in response json:\n {response_json}")
    else:
        logging.info("Logged in successfully")
        session.headers.update({"Authorization": f"JWT {response_json['sessionToken']}"})

def download_files(session):
    """
    Downloads files from the Encoura API.

    Args:
        session (requests.Session): The session object used for making HTTP requests.

    Returns:
        None
    """
    get_exports_payload = {"status": "NotDelivered"}
    response_json = session.get(f"{ENCORA_URL}/datacenter/exports", params=get_exports_payload, headers={"Organization": ENCOURA_ORGANIZATION_UID}).json()
    files_to_download = []
    for export in response_json:
        if "uid" in export:
            export_uid = export["uid"]
            file_export_url = f"{ENCORA_URL}/datacenter/exports/{export_uid}/download"
            export_response_json = session.get(file_export_url, headers={"Organization": ENCOURA_ORGANIZATION_UID}).json()
            if "downloadUrl" in export_response_json:
                files_to_download.append(export_response_json["downloadUrl"])
    if len(files_to_download) == 0:
        logging.info("No files to download!")
    else:
        for file in files_to_download:
            parsed_url = urlparse(file)
            escaped_filename = get_valid_filename(unquote(os.path.basename(parsed_url.path)))
            download_path = DOWNLOAD_DIR / escaped_filename
            logging.info(f"Downloading file from url {file}")
            download_file_response = requests.get(file, allow_redirects=True, stream=True)
            if download_file_response.ok:
                logging.info(f"Writing file to {download_path}.")
                with open(download_path, "wb") as f:
                    for chunk in download_file_response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
            else:
                logging.error(f"There was an error retrieving {file} with status code {download_file_response.status_code}.")
                logging.error(f"{download_file_response.content}")

def upload_files():
    """
    Uploads CSV files from a specified directory to a remote server using SFTP.

    The function connects to the remote server using the provided credentials,
    iterates through all CSV files in the specified directory, and uploads each
    file to a specific location on the remote server. After successful upload,
    the local file is deleted.

    If there are no CSV files in the directory, a log message is generated.

    Raises:
        paramiko.ssh_exception.AuthenticationException: If there is an authentication error while connecting to the remote server.
        PermissionError: If there is a permissions error on the remote server while uploading a file.
        Exception: If there is any other error during the SFTP operation.

    """
    pathlist = list(Path(DOWNLOAD_DIR).rglob('*.csv'))
    if len(list(pathlist)) == 0:
        logging.info("No files to upload!")
    else:
        try:
            tp = paramiko.Transport("ft.technolutions.net", 22)
            tp.connect(username=SLATE_HALIA_SFTP_UN, password=SLATE_HALIA_SFTP_PW)
            try:
                sftpClient = paramiko.SFTPClient.from_transport(tp)
                for path in pathlist:
                    path_in_str = str(path)
                    file = path_in_str.split('\\')[-1]
                    try:
                        sftpClient.put(path_in_str, f"/incoming/Encoura API Uploads/{file}")
                        os.unlink(path_in_str)
                        logging.info(f"{file} successfully uploaded")
                    except PermissionError as err:
                        logging.error(f"SFTP Operation Failed on {file} due to a permissions error on the remote server [" + str(err) + "]")
                    except Exception as err:
                        logging.error(f"SFTP Operation Failed on {file} due to other error [" + str(err) + "]")
                sftpClient.close()
            except Exception as err:
                logging.error("SFTP failed due to [" + str(err) + "]")
            tp.close()
        except paramiko.ssh_exception.AuthenticationException as err:
            logging.error("Can't connect due to authentication error [" + str(err) + "]")
        except Exception as err:
            logging.error("Can't connect due to other error [" + str(err) + "]")

def main():
    """
    This function is the entry point of the program.
    It performs the following steps:
    1. Creates a session with the Encoura API using the provided API key.
    2. Logs in to the Encoura API.
    3. Downloads files from the Encoura API.
    4. Uploads files.
    """
    session = requests.Session()
    session.headers.update({"x-api-key": ENCOURA_API_KEY})
    login(session)
    download_files(session)
    upload_files()

if __name__ == "__main__":
    main()

