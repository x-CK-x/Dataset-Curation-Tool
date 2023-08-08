import gradio as gr

class Stats_tab:
    def get_tab(self):
        with gr.Tab("Data Stats"):
            with gr.Row():
                stats_run_options = gr.Dropdown(label="Run Method", choices=["frequency table", "inverse freq table"])
                stats_load_file = gr.Dropdown(label="Meta Tag Category", choices=["tags", "artist", "character", "species", "general", "meta", "rating"])
                stats_run_button = gr.Button(value="Run Stats", variant='primary')
            with gr.Row():
                stats_selected_data = gr.Dataframe(interactive=False, label="Dataframe Table", visible=False,
                                               headers=["Tag Category", "Count"], datatype=["str", "number"], max_cols=2,
                                               type="array")
        return [stats_run_options, stats_load_file, stats_run_button, stats_selected_data]