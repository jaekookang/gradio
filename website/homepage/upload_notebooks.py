import os
import json
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

GRADIO_DEMO_DIR = "../../demo/"
NOTEBOOK_TYPE = "application/vnd.google.colaboratory"
GOOGLE_FOLDER_TYPE = "application/vnd.google-apps.folder"

def run():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("google_credentials.json")
    print("!", gauth.credentials)
    if gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    drive = GoogleDrive(gauth)

    demo_links = {}
    with open("colab_template.ipynb") as notebook_template_file:
        notebook_template = notebook_template_file.read()
    file_list = drive.ListFile({'q': f"title='Demos' and mimeType='{GOOGLE_FOLDER_TYPE}' and 'root' in parents and trashed=false"}).GetList()
    if len(file_list) > 0:
        demo_folder = file_list[0].metadata["id"]
    else:
        demo_folder_file = drive.CreateFile({'title' : "Demos", 'mimeType' : GOOGLE_FOLDER_TYPE})
        demo_folder_file.Upload()
        demo_folder = demo_folder_file.metadata["id"]
    for demo_name in os.listdir(GRADIO_DEMO_DIR):
        notebook_title = demo_name + ".ipynb"
        print("--- " + demo_name + " ---")
        with open(os.path.join(GRADIO_DEMO_DIR, demo_name, "run.py")) as demo_file:
            demo_content = demo_file.read()
            demo_content = demo_content.replace('if __name__ == "__main__":\n    iface.launch()', "iface.launch()")
            lines = demo_content.split("/n")
            demo_content = [line + "\n" if i != len(lines) - 1 else line for i, line in enumerate(lines)]
        notebook = json.loads(notebook_template)
        notebook["cells"][1]["source"] = demo_content
        file_list = drive.ListFile({'q': f"title='{notebook_title}' and mimeType='{NOTEBOOK_TYPE}' and 'root' in parents and trashed=false"}).GetList()
        if len(file_list) > 0:
            drive_file = file_list[0]
        else:
            drive_file = drive.CreateFile({
                'title': notebook_title,
                'mimeType': NOTEBOOK_TYPE,
                'parents': [{"id": demo_folder}]
            })
        drive_file.SetContentString(json.dumps(notebook))
        drive_file.Upload()
        drive_file.InsertPermission({
                            'type': 'anyone',
                            'value': 'anyone',
                            'role': 'reader'})
        demo_links[demo_name] = drive_file['alternateLink']
    os.makedirs("generated", exist_ok=True)
    with open("generated/colab_links.json", "w") as demo_links_file:
        json.dump(demo_links, demo_links_file)
    return demo_links

if __name__ == "__main__":
    run()