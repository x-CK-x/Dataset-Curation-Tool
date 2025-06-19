import gradio as gr


class Database_tab:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def execute_query(self, query):
        if not query.strip():
            return gr.update(), gr.update(value="No query provided.")
        try:
            headers, rows = self.db_manager.run_query(query)
            if headers:
                return gr.update(value=rows, headers=headers, visible=True), gr.update(value="")
            else:
                return gr.update(visible=False, value=[]), gr.update(value="Query executed.")
        except Exception as e:
            return gr.update(), gr.update(value=f"Error: {e}")

    def list_tables(self):
        headers, rows = self.db_manager.run_query("SELECT name FROM sqlite_master WHERE type='table'")
        return gr.update(value=rows, headers=headers, visible=True)

    def render_tab(self):
        with gr.Tab("Database"):
            gr.Markdown(
                """# Database\nUse this tab to run SQL commands on
                `dataset_curation.db`. Example: `SELECT * FROM downloads LIMIT 5;`"""
            )
            query_text = gr.Textbox(
                label="SQL Query",
                lines=4,
                info="Enter any valid SQL statement"
            )
            run_button = gr.Button(value="Execute", variant="primary")
            tables_button = gr.Button(value="List Tables")
            result_table = gr.Dataframe(visible=False)
            message_box = gr.Textbox(label="Message", interactive=False)

        self.query_text = query_text
        self.run_button = run_button
        self.tables_button = tables_button
        self.result_table = result_table
        self.message_box = message_box

        return [self.query_text, self.run_button, self.tables_button, self.result_table, self.message_box]

    def get_event_listeners(self):
        self.run_button.click(
            fn=self.execute_query,
            inputs=self.query_text,
            outputs=[self.result_table, self.message_box],
        )
        self.tables_button.click(
            fn=lambda: self.list_tables(),
            inputs=None,
            outputs=self.result_table,
        )


