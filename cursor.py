import sys
import time
import threading
from contextlib import ContextDecorator


class RotatingCursor(ContextDecorator):
    def __init__(
        self, text="Processing", cursor_chars="|/-\\", interval=0.1, output_stream=None
    ):
        """
        A context manager that displays a rotating cursor while performing tasks.

        :param text: The text to display alongside the rotating cursor.
        :param cursor_chars: Characters to rotate through for the spinner.
        :param interval: Time (in seconds) to wait between cursor rotations.
        :param output_stream: The output stream for displaying the cursor (default is sys.stdout).
        """
        self.text = text
        self.cursor_chars = cursor_chars
        self.interval = interval
        self.output_stream = output_stream or sys.stdout
        self._stop_event = threading.Event()
        self._thread = None

    def _spinner(self):
        """Private method to handle the rotating cursor."""
        while not self._stop_event.is_set():
            for char in self.cursor_chars:
                # Write the cursor and text
                self.output_stream.write(f"\r{self.text} {char}")
                self.output_stream.flush()
                time.sleep(self.interval)
                if self._stop_event.is_set():
                    break

    def __enter__(self):
        """Start the spinner in a separate thread."""
        self._stop_event.clear()
        # Start a daemon thread to ensure it stops if the main program exits
        self._thread = threading.Thread(target=self._spinner, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Stop the spinner and clean up."""
        self._stop_event.set()
        self._thread.join()
        self.output_stream.flush()
        # Return False to propagate any exceptions that occurred within the context
        return False


# Example usage
if __name__ == "__main__":
    with RotatingCursor(text="Processing", cursor_chars="|/-\\", interval=0.1):
        time.sleep(5)  # Simulate a long-running task
