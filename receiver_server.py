import os
from flask import Flask, request, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = "."

def create_nested_folders(path):
    """Creates nested folders from a normalized path."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

@app.route('/create_folder', methods=['POST'])
def create_folder():
    """Creates nested folders on the follower node."""
    data = request.json
    folder_path = data.get('folder')
    
    if not folder_path:
        return jsonify({"error": "No folder path provided"}), 400

    try:
        full_path = os.path.join(UPLOAD_FOLDER, folder_path)
        create_nested_folders(full_path)
        return jsonify({"message": f"Folder '{folder_path}' created"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Receives a file and saves it to the specified relative path."""
    relative_path = request.form.get("relative_path")
    file = request.files.get("file")
    
    if not file or not relative_path:
        return jsonify({"error": "Missing file or relative path"}), 400

    # Normalize the path and save file in the correct nested directory
    relative_path = relative_path.replace("\\", "/")
    save_path = os.path.join(UPLOAD_FOLDER, relative_path)
    folder = os.path.dirname(save_path)

    try:
        create_nested_folders(folder)
        file.save(save_path)
        return jsonify({"message": f"File '{relative_path}' uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)