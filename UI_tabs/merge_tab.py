import gradio as gr
import os

class Merge_tab:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def merge_db(self, other_path):
        if not other_path or not os.path.isfile(other_path):
            return gr.update(value="Invalid database path")
        self.db_manager.merge_database(other_path)
        return gr.update(value="Merge complete")

    def render_tab(self):
        with gr.Tab("Merge DB"):
            gr.Markdown(
                """# Merge Databases\nCombine another `dataset_curation.db`
                file with this one."""
            )
            db_path = gr.Textbox(label="Other DB Path", info="Path to another .db file")
            run_btn = gr.Button("Merge")
            message = gr.Textbox(label="Message", interactive=False)
        self.db_path = db_path
        self.run_btn = run_btn
        self.message = message
        return [db_path, run_btn, message]

    def get_event_listeners(self):
        self.run_btn.click(fn=self.merge_db, inputs=self.db_path, outputs=self.message)
