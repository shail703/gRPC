import os
import requests

# List of follower nodes with their IPs and ports
FOLLOWER_NODES = ["http://192.168.204.136:5001", "http://192.168.204.145:5001"]

# Files and folders to sync
FILES_TO_SYNC = [
    "users.json",
    "assignments.json",
    "submissions.json",
    "doubts.json",
    "log.txt",
]

FOLDERS_TO_SYNC = {
    "assignments": "assignments",
    "content": "content",
    "questions": os.path.join("assignments", "questions"),
}



def sync_file(file_path, relative_path, followers):
    """Sends a file to each follower node."""
    for node in followers:
        url = f"{node}/upload"
        try:
            with open(file_path, "rb") as file_data:
                response = requests.post(
                    url,
                    files={"file": file_data},
                    data={"relative_path": relative_path},
                )
                if response.status_code == 200:
                    print(f"Successfully sent {relative_path} to {node}")
                else:
                    print(f"Failed to send {relative_path} to {node}: {response.text}")
        except Exception as e:
            print(f"Error sending {relative_path} to {node}: {e}")


def create_folder(folder_path, followers):
    """Creates folder on all follower nodes."""
    for node in followers:
        url = f"{node}/create_folder"
        data = {"folder": folder_path}
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"Created folder {folder_path} on {node}")
            else:
                print(
                    f"Failed to create folder {folder_path} on {node}: {response.text}"
                )
        except Exception as e:
            print(f"Error creating folder {folder_path} on {node}: {e}")


def sync_folders(root_folder, followers):
    """Recursively creates folders and syncs files for a folder and its subfolders."""
    for foldername, subfolders, filenames in os.walk(root_folder):
        # Create the folder on followers
        relative_folder = foldername.replace("\\", "/")
        create_folder(relative_folder, followers)

        # Sync files in the folder
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            relative_path = os.path.join(relative_folder, filename).replace("\\", "/")
            sync_file(file_path, relative_path, followers)


def sync_all():
    """Main function to sync all files and folders to followers."""
    # Step 1: Ensure folders exist on followers
    for folder_name, folder_path in FOLDERS_TO_SYNC.items():
        sync_folders(folder_path, FOLLOWER_NODES)

    # Step 2: Sync each file
    for file in FILES_TO_SYNC:
        if os.path.exists(file):
            sync_file(file, file, FOLLOWER_NODES)
        else:
            print(f"File {file} does not exist on the leader, skipping.")


if __name__ == "__main__":
    sync_all()
