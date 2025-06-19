import gradio as gr
import os


class Database_tab:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    # Tag management helpers
    def add_tag(self, tag, current):
        """Add a tag to the required tag list."""
        tags = list(current or [])
        t = tag.strip()
        if t and t not in tags:
            tags.append(t)
        return "", gr.update(choices=tags, value=[]), tags

    def remove_tag(self, selected, current):
        tags = [t for t in (current or []) if t not in (selected or [])]
        return gr.update(choices=tags, value=[]), tags

    def add_black_tag(self, tag, current):
        tags = list(current or [])
        t = tag.strip()
        if t and t not in tags:
            tags.append(t)
        return "", gr.update(choices=tags, value=[]), tags

    def remove_black_tag(self, selected, current):
        tags = [t for t in (current or []) if t not in (selected or [])]
        return gr.update(choices=tags, value=[]), tags

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
        options = [r[0] for r in rows]
        return gr.update(value=rows, headers=headers, visible=True), gr.update(choices=options)

    def view_table(self, table_name):
        if not table_name:
            return gr.update(), gr.update(value="No table selected")
        try:
            headers, rows = self.db_manager.fetch_table(table_name)
            return gr.update(value=rows, headers=headers, visible=True), gr.update(value="")
        except Exception as e:
            return gr.update(), gr.update(value=f"Error: {e}")

    def search(self, required_list, blacklist_list):
        """Search the files table using the provided tag lists."""
        required = required_list or []
        blacklist = blacklist_list or []
        headers, rows = self.db_manager.search_files(required, blacklist)
        return gr.update(value=rows, headers=headers, visible=True)

    def create_search_table(self, new_table_name, required_list, blacklist_list):
        if not new_table_name:
            return gr.update(value="Table name required")
        required = required_list or []
        blacklist = blacklist_list or []
        headers, _ = self.db_manager.search_files(required, blacklist)
        cols = ', '.join(headers)
        query = f"CREATE TABLE {new_table_name} AS SELECT {cols} FROM files"
        if required or blacklist:
            conditions = []
            for t in required:
                conditions.append(f"post_tags LIKE '%{t}%'")
            for t in blacklist:
                conditions.append(f"post_tags NOT LIKE '%{t}%'")
            query += " WHERE " + " AND ".join(conditions)
        self.db_manager.run_query(query)
        return gr.update(value=f"Created table {new_table_name}")

    def export_table(self, table_name, dest_dir):
        if not table_name or not dest_dir:
            return gr.update(value="Select table and directory")
        count = self.db_manager.copy_files_from_table(table_name, dest_dir)
        return gr.update(value=f"Copied {count} files")

    def render_tab(self):
        with gr.Tab("Database"):
            gr.Markdown(
                """# Database
                This tab lets you browse the tables within `dataset_curation.db`.

                **SQL Query** runs a raw SQL statement. Use with care.

                **View Table** displays the selected table's contents.

                **Tag Search** - enter tags in the boxes and press <kbd>Enter</kbd>
                to add them to the lists. All tags currently shown will be used
                when searching. Blacklisted tags are excluded.

                You can create a new table from the search results or export the
                matching files to a folder on disk.
                """
            )
            query_text = gr.Textbox(label="SQL Query", lines=4, info="Enter SQL")
            run_button = gr.Button(value="Execute", variant="primary")
            tables_button = gr.Button(value="List Tables")
            table_options = self.db_manager.get_table_names() if hasattr(self.db_manager, "get_table_names") else []
            table_dropdown = gr.Dropdown(table_options, label="View Table", value=None)
            view_button = gr.Button(value="Show Table")
            with gr.Accordion("Tag Search", open=False):
                with gr.Row():
                    with gr.Column():
                        req_tags = gr.Textbox(label="Add Required Tag", value="",
                                             info="Press Enter to add")
                        req_group = gr.CheckboxGroup(label="Required Tags")
                        req_remove = gr.Button(value="Remove Selected Required")
                    with gr.Column():
                        blacklist_tags = gr.Textbox(label="Add Blacklist Tag", value="",
                                                   info="Press Enter to add")
                        blacklist_group = gr.CheckboxGroup(label="Blacklist Tags")
                        blacklist_remove = gr.Button(value="Remove Selected Blacklist")
                search_button = gr.Button(value="Search")
                new_table_name = gr.Textbox(label="New Table Name")
                create_table_btn = gr.Button(value="Create Table from Search")
                export_dir = gr.Textbox(label="Export Directory")
                export_button = gr.Button(value="Export Table Files")

            result_table = gr.Dataframe(visible=False)
            message_box = gr.Textbox(label="Message", interactive=False)
            req_state = gr.State([])
            blacklist_state = gr.State([])

        self.query_text = query_text
        self.run_button = run_button
        self.tables_button = tables_button
        self.table_dropdown = table_dropdown
        self.view_button = view_button
        self.req_tags = req_tags
        self.req_group = req_group
        self.req_remove = req_remove
        self.blacklist_tags = blacklist_tags
        self.blacklist_group = blacklist_group
        self.blacklist_remove = blacklist_remove
        self.search_button = search_button
        self.new_table_name = new_table_name
        self.create_table_btn = create_table_btn
        self.export_dir = export_dir
        self.export_button = export_button
        self.result_table = result_table
        self.message_box = message_box
        self.req_state = req_state
        self.blacklist_state = blacklist_state

        return [query_text, run_button, tables_button, table_dropdown, view_button,
                req_tags, req_group, req_remove,
                blacklist_tags, blacklist_group, blacklist_remove,
                search_button, new_table_name, create_table_btn,
                export_dir, export_button, result_table, message_box,
                req_state, blacklist_state]

    def get_event_listeners(self):
        self.run_button.click(
            fn=self.execute_query,
            inputs=self.query_text,
            outputs=[self.result_table, self.message_box],
        )
        self.tables_button.click(
            fn=lambda: self.list_tables(),
            inputs=None,
            outputs=[self.result_table, self.table_dropdown],
        )
        self.view_button.click(
            fn=self.view_table,
            inputs=self.table_dropdown,
            outputs=[self.result_table, self.message_box],
        )
        self.req_tags.submit(
            fn=self.add_tag,
            inputs=[self.req_tags, self.req_state],
            outputs=[self.req_tags, self.req_group, self.req_state],
        )
        self.req_remove.click(
            fn=self.remove_tag,
            inputs=[self.req_group, self.req_state],
            outputs=[self.req_group, self.req_state],
        )
        self.blacklist_tags.submit(
            fn=self.add_black_tag,
            inputs=[self.blacklist_tags, self.blacklist_state],
            outputs=[self.blacklist_tags, self.blacklist_group, self.blacklist_state],
        )
        self.blacklist_remove.click(
            fn=self.remove_black_tag,
            inputs=[self.blacklist_group, self.blacklist_state],
            outputs=[self.blacklist_group, self.blacklist_state],
        )
        self.search_button.click(
            fn=self.search,
            inputs=[self.req_state, self.blacklist_state],
            outputs=self.result_table,
        )
        self.create_table_btn.click(
            fn=self.create_search_table,
            inputs=[self.new_table_name, self.req_state, self.blacklist_state],
            outputs=self.message_box,
        )
        self.export_button.click(
            fn=self.export_table,
            inputs=[self.table_dropdown, self.export_dir],
            outputs=self.message_box,
        )


