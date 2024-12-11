from __future__ import annotations

__all__ = ["QEntryRowList"]

import typing as tp

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSpinBox

from .entry_row import QEntryRow


class QEntryRowList(QWidget):
    """Designed as the sole widget to occupy a `QScrollArea`."""

    ENTRY_RANGE_SIZE: tp.ClassVar[int] = 10

    layout: QVBoxLayout
    entry_rows: list[QEntryRow]

    entry_count: int
    first_row_index: QSpinBox  # hidden

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        # Reusable `QEntryRow` Widgets
        self.entry_rows = [QEntryRow(i) for i in range(self.ENTRY_RANGE_SIZE)]
        for i, entry_row in enumerate(self.entry_rows):
            self.layout.addWidget(entry_row)
            # Styling (alternating rows)
            entry_row.setStyleSheet("background-color: #f0f0f0;" if i % 2 == 0 else "background-color: #e0e0e0;")
        self.entry_count = 0

        self.first_row_index = QSpinBox(self)
        self.first_row_index.setValue(0)
        self.first_row_index.hide()

    def populate_entries(self, entries: list[tuple[int, str]]):
        """Update existing QEntryRow widgets with new entry data, starting at `self.row_range_start`."""
        self.entry_count = len(entries)  # ALL entries
        row_range_start = self.first_row_index.value()
        entries_range = entries[row_range_start:row_range_start + self.ENTRY_RANGE_SIZE]  # can be less than range size
        row_index = 0
        total_height = 0
        for entry_id, entry_text in entries_range:
            self.entry_rows[row_index].update_entry(entry_id, entry_text)
            self.entry_rows[row_index].show()
            total_height += self.entry_rows[row_index].height()
            row_index += 1
        # Hide all remaining rows.
        for unused_row_index in range(row_index, self.ENTRY_RANGE_SIZE):
            self.entry_rows[unused_row_index].hide()
        # Resize entry list container based on number of visible rows.
        self.setMinimumHeight(total_height)
        self.setMaximumHeight(total_height)

    def go_to_previous_range(self, entries: list[tuple[int, str]]):
        """Navigate to the previous range of entries."""
        current_row_range_start = self.first_row_index.value()
        if current_row_range_start == 0:
            return  # button should be disabled!
        new_row_range_start = current_row_range_start - self.ENTRY_RANGE_SIZE
        new_row_range_start = max(new_row_range_start, 0)
        self.first_row_index.setValue(new_row_range_start)
        self.populate_entries(entries)

    def go_to_next_range(self, entries: list[tuple[int, str]]):
        """Navigate to the next range of entries."""
        current_row_range_start = self.first_row_index.value()
        if current_row_range_start + self.ENTRY_RANGE_SIZE >= len(entries):
            return
        new_row_range_start = current_row_range_start + self.ENTRY_RANGE_SIZE
        self.first_row_index.setValue(new_row_range_start)
        self.populate_entries(entries)

    @property
    def previous_button_valid(self):
        return self.first_row_index.value() > 0

    @property
    def next_button_valid(self):
        return self.first_row_index.value() < self.entry_count - self.ENTRY_RANGE_SIZE
