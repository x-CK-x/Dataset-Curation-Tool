from __future__ import annotations

import os
import urllib.parse
import urllib.request

from krita import Extension, InfoObject, Krita
from PyQt5.QtWidgets import QAction, QInputDialog, QMessageBox


class KritaDatasetBridgeExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(
            "send_active_document_to_data_curation_tool",
            "Send Active Document to Data Curation Tool",
            "tools/scripts",
        )
        action.triggered.connect(self.send_active_document)

    def send_active_document(self):
        app = Krita.instance()
        doc = app.activeDocument()
        if doc is None:
            QMessageBox.warning(None, "Data Curation Tool", "No active Krita document is open.")
            return

        url, ok = QInputDialog.getText(None, "Data Curation Tool URL", "Local app URL:", text="http://127.0.0.1:7865")
        if not ok or not url.strip():
            return
        dataset_id, _ = QInputDialog.getText(None, "Dataset ID", "Dataset ID to import into (optional):", text="")
        tags, _ = QInputDialog.getText(None, "Tags", "Optional comma-separated tags:", text="")
        caption, _ = QInputDialog.getMultiLineText(None, "Caption", "Optional caption:", text="")

        tmp_dir = os.path.join(os.path.expanduser("~"), ".data_curation_tool", "krita_bridge")
        os.makedirs(tmp_dir, exist_ok=True)
        safe_name = doc.fileName() or doc.name() or "krita_document.png"
        safe_name = os.path.basename(safe_name)
        base, _ext = os.path.splitext(safe_name)
        export_path = os.path.join(tmp_dir, f"{base or 'krita_document'}_export.png")

        info = InfoObject()
        doc.exportImage(export_path, info)

        boundary = "----DCTKritaBoundary7MA4YWxkTrZu0gW"
        fields = []
        if dataset_id.strip():
            fields.append(("dataset_id", dataset_id.strip()))
        if tags.strip():
            fields.append(("tags", tags.strip()))
        if caption.strip():
            fields.append(("caption", caption.strip()))

        body = bytearray()
        for key, value in fields:
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(export_path)}"\r\n'.encode())
        body.extend(b"Content-Type: image/png\r\n\r\n")
        with open(export_path, "rb") as handle:
            body.extend(handle.read())
        body.extend(f"\r\n--{boundary}--\r\n".encode())

        endpoint = urllib.parse.urljoin(url.rstrip("/") + "/", "api/krita/import-image")
        req = urllib.request.Request(endpoint, data=bytes(body), method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            QMessageBox.information(None, "Data Curation Tool", f"Image sent.\n\n{text[:1000]}")
        except Exception as exc:
            QMessageBox.critical(None, "Data Curation Tool", f"Could not send image:\n{exc}")
