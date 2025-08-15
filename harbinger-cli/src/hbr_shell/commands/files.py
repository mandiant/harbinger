import os
from ..utils import make_api_request, print_output

def setup(subparsers):
    """Setup the files command."""
    parser = subparsers.add_parser("files", help="Manage files in Harbinger")
    files_subparsers = parser.add_subparsers(dest="files_command", required=True)

    # List command
    list_parser = files_subparsers.add_parser("list", help="List all files")
    list_parser.set_defaults(func=list_files)

    # Upload command
    upload_parser = files_subparsers.add_parser("upload", help="Upload a file")
    upload_parser.add_argument("file_path", help="Path to the file to upload")
    upload_parser.add_argument("--file-type", default="text", help="The type of the file")
    upload_parser.set_defaults(func=upload_file)

    # Download command
    download_parser = files_subparsers.add_parser("download", help="Download a file")
    download_parser.add_argument("file_id", help="ID of the file to download")
    download_parser.add_argument("output_path", help="Path to save the downloaded file")
    download_parser.set_defaults(func=download_file)

def list_files(args):
    """List all files."""
    response = make_api_request("GET", "/files/")
    if response:
        files_data = response.json()
        files = files_data.get("items", [])
        headers = ["ID", "Filename", "File Type", "Time Created"]
        
        # Remap keys for print_output
        output_data = []
        for f in files:
            output_data.append({
                "id": f.get("id"),
                "filename": f.get("filename"),
                "file_type": f.get("filetype"),
                "time_created": f.get("time_created"),
            })
        print_output(output_data, headers, args.output)

def upload_file(args):
    """Upload a file."""
    print(f"Uploading file: {args.file_path}")
    
    with open(args.file_path, "rb") as f:
        files = {"file": (os.path.basename(args.file_path), f)}
        params = {"file_type": args.file_type}
        response = make_api_request("POST", "/upload_file/", files=files, params=params)
    
    if response:
        print("File uploaded successfully.")
        file_data = response.json()
        output_data = [{
            "id": file_data.get("id"),
            "filename": file_data.get("filename"),
            "file_type": file_data.get("filetype"),
            "time_created": file_data.get("time_created"),
        }]
        print_output(output_data, ["ID", "Filename", "File Type", "Time Created"], args.output)


def download_file(args):
    """Download a file."""
    print(f"Downloading file {args.file_id} to {args.output_path}")
    response = make_api_request("GET", f"/files/{args.file_id}/download", stream=True)
    if response:
        with open(args.output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("File downloaded successfully.")
