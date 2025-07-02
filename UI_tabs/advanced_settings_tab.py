import gradio as gr

class Advanced_settings_tab:
    def render_tab(self, suggestions_enabled=True):
        with gr.Tab("Advanced Settings"):
            total_suggestions_slider = gr.Slider(
                info="Limit Number of Tag Suggestions",
                minimum=0,
                maximum=1000,
                step=1,
                value=10,
                show_label=False,
            )

            tag_suggestions_checkbox = gr.Checkbox(
                label="Tag Suggestions",
                value=suggestions_enabled,
                info="Enable search tag suggestions",
            )

        self.total_suggestions_slider = total_suggestions_slider
        self.tag_suggestions_checkbox = tag_suggestions_checkbox

        return self.total_suggestions_slider, self.tag_suggestions_checkbox
