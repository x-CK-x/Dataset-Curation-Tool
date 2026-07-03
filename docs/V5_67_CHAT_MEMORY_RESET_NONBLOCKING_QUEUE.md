# v5.67 Chat Memory Reset and Non-Blocking Chat Queue

- Clear memory now creates a real model-visible context reset point.
- Older visible transcript messages remain visible for the user but are no longer sent to the model after reset.
- Context/token budget display resets to a cleared-memory state.
- Tag Editor assistant chat and Code Assistant chat now queue messages while a response is running instead of disabling the composer.
- Queued messages appear as pending bubbles and are sent automatically in order.
