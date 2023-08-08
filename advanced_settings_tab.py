import gradio as gr

class Advanced_settings_tab:
    def get_tab(self):
        with gr.Tab("Advanced Settings"):
            total_suggestions_slider = gr.Slider(info="Limit Number of Tag Suggestions", minimum=0, maximum=100, step=1, value=10, show_label=False)
        return total_suggestions_slider