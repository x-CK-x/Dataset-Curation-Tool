import gradio as gr
import os
import datetime


class Import_tab:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def import_data(self, website, config_file, config_json, image_folder, tag_folder):
        if not image_folder or not os.path.isdir(image_folder):
            return gr.update(value=f"Invalid image folder: {image_folder}")
        json_text = None
        config_path = None
        if config_file:
            config_path = config_file
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    json_text = f.read()
            except Exception:
                json_text = None
        elif config_json and config_json.strip():
            json_text = config_json
        download_id = self.db_manager.add_download_record(website or "manual", json_text, config_path)
        count = 0
        for fname in os.listdir(image_folder):
            img_path = os.path.join(image_folder, fname)
            if os.path.isfile(img_path):
                tag_path = os.path.join(tag_folder, os.path.splitext(fname)[0] + ".txt") if tag_folder else None
                self.db_manager.add_file(
                    download_id,
                    post_tags="",
                    post_created_at=None,
                    downloaded_at=datetime.datetime.utcnow().isoformat(),
                    cdn_url=None,
                    local_path=img_path,
                    tag_local_path=tag_path if tag_path and os.path.exists(tag_path) else None,
                    tag_cdn_url=None,
                )
                count += 1
        return gr.update(value=f"Imported {count} files to download {download_id}")

    def render_tab(self):
        with gr.Tab("Import Data"):
            gr.Markdown(
                """# Import Data\nLoad folders of existing images and tags
                into the database. Provide the originating website and optional
                config JSON."""
            )
            website_text = gr.Textbox(label="Website", info="Source site name")
            config_file = gr.File(label="Config JSON File", file_types=[".json"], type="filepath")
            config_text = gr.Textbox(label="Config JSON", lines=3, info="Paste settings used for the download")
            img_folder = gr.Textbox(label="Image Folder", info="Path to images")
            img_browse = gr.File(label="Browse Folder", type="filepath", file_count="directory")
            tag_folder = gr.Textbox(label="Tag Folder", value="", info="Optional path to tag files")
            run_btn = gr.Button("Import")
            message = gr.Textbox(label="Message", interactive=False)

        self.website_text = website_text
        self.config_file = config_file
        self.config_text = config_text
        self.img_folder = img_folder
        self.img_browse = img_browse
        self.tag_folder = tag_folder
        self.run_btn = run_btn
        self.message = message
        return [website_text, config_file, config_text, img_folder, img_browse, tag_folder, run_btn, message]

    def get_event_listeners(self):
        self.img_browse.change(lambda p: p, inputs=self.img_browse, outputs=self.img_folder)
        self.run_btn.click(
            fn=self.import_data,
            inputs=[self.website_text, self.config_file, self.config_text, self.img_folder, self.tag_folder],
            outputs=self.message,
        )
