import gradio as gr

class Advanced_settings_tab:
    def render_tab(self):
        with gr.Tab("Advanced Settings"):
            tag_suggestions_checkbox = gr.Checkbox(label="Enable Tag Suggestions", value=True)
            total_suggestions_slider = gr.Slider(
                info="Limit Number of Tag Suggestions",
                minimum=0,
                maximum=1000,
                step=1,
                value=10,
                show_label=False,
            )

        self.tag_suggestions_checkbox = tag_suggestions_checkbox
        self.total_suggestions_slider = total_suggestions_slider

        return self.total_suggestions_slider, self.tag_suggestions_checkbox
