import gradio as gr

from utils import helper_functions as help


class Stats_tab:
    def __init__(self, gallery_tab_manager):
        self.gallery_tab_manager = gallery_tab_manager

    def run_stats(self, stats_run_options, stats_load_file):
        csv_table, size = self.gallery_tab_manager.is_csv_dict_empty(stats_load_file)

        help.verbose_print(f"stats_run_options:\t\t{stats_run_options}")
        help.verbose_print(f"stats_load_file:\t\t{stats_load_file}")

        dataframe = None
        show_list = None
        if "frequency table" in stats_run_options:
            show_list = sorted(csv_table.items(), key=lambda x: x[1], reverse=True)
            dataframe = gr.update(visible=True, label=stats_run_options, max_rows=size,
                                  value=show_list)
        elif "inverse freq table" in stats_run_options:
            total_sum = sum(csv_table.values())
            normalized_dict = {key: value / total_sum for key, value in csv_table.items()}
            show_list = sorted(normalized_dict.items(), key=lambda x: x[1], reverse=True)
            dataframe = gr.update(visible=True, label=stats_run_options, max_rows=size,
                                  value=show_list)
        # verbose_print(f"show_list:\t\t{show_list}")
        return dataframe

    def render_tab(self):
        with gr.Tab("Data Stats"):
            with gr.Row():
                stats_run_options = gr.Dropdown(label="Run Method", choices=["frequency table", "inverse freq table"])
                stats_load_file = gr.Dropdown(label="Meta Tag Category", choices=["tags", "artist", "character", "species", "general", "meta", "rating"])
                stats_run_button = gr.Button(value="Run Stats", variant='primary')
            with gr.Row():
                stats_selected_data = gr.Dataframe(interactive=False, label="Dataframe Table", visible=False,
                                               headers=["Tag Category", "Count"], datatype=["str", "number"], col_count=2,
                                               type="array")

        self.stats_run_options = stats_run_options
        self.stats_load_file = stats_load_file
        self.stats_run_button = stats_run_button
        self.stats_selected_data = stats_selected_data

        return [
            self.stats_run_options,
            self.stats_load_file,
            self.stats_run_button,
            self.stats_selected_data
        ]

    def get_event_listeners(self):
        self.stats_run_button.click(
            fn=self.run_stats,
            inputs=[self.stats_run_options, self.stats_load_file],
            outputs=[self.stats_selected_data]
        )