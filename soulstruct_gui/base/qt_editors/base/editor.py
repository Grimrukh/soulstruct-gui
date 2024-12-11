from __future__ import annotations

__all__ = ["BaseEditor"]

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QListWidget, QListWidgetItem, QSpinBox,
    QLabel, QComboBox,
)
from PyQt6.QtCore import Qt

from soulstruct_gui.base.qt_editors.base.entry_list import QEntryRowList


TEST_DATA = {
    "Category A": [(1, "Entry 1A"), (2, "Entry 2A"), (3, "Entry 3A")],
    "Category B": [(4, "Entry 1B"), (5, "Entry 2B"), (6, "Entry 3B")],
    "Category C": [(7, "Entry 1C"), (8, "Entry 2C"), (9, "Entry 3C")],
    "Category Big": [(i, f"Big Entry {i}") for i in range(45)],
}


class BaseEditor(QMainWindow):
    """Base class for a two-part window with a list of 'categories' (left) and entries within the selected category
    (right)."""

    WINDOW_TITLE = "Base Editor"

    # Members: Widgets
    central_widget: QWidget
    main_layout: QVBoxLayout

    header_layout: QHBoxLayout
    map_label: QLabel
    map_dropdown: QComboBox

    content_layout: QHBoxLayout
    category_list: QListWidget
    entry_row_list_scroll_area: QScrollArea
    entry_row_list: QEntryRowList
    nav_layout: QHBoxLayout
    previous_button: QPushButton
    next_button: QPushButton

    # Members: Data/State
    selected_category_name: str

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setGeometry(100, 100, 800, 600)

        # MAIN
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # HEADER
        self.header_layout = QHBoxLayout()
        # Map Choice
        self.map_label = QLabel("Selected Map:", self)
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.header_layout.addWidget(self.map_label)
        self.map_dropdown = QComboBox(self)
        self.map_dropdown.addItems(["Map 1", "Map 2", "Map 3"])  # TODO: from game
        self.header_layout.addWidget(self.map_dropdown)
        # Entry Range Navigation
        self.nav_layout = QHBoxLayout()
        self.previous_button = QPushButton("Previous")
        self.previous_button.clicked.connect(
            lambda: self.entry_list.go_to_previous_range(self.get_selected_category_entries())
        )
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(
            lambda: self.entry_list.go_to_next_range(self.get_selected_category_entries())
        )
        self.nav_layout.addWidget(self.previous_button)
        self.nav_layout.addWidget(self.next_button)
        self.header_layout.addLayout(self.nav_layout)
        # End Header
        self.main_layout.addLayout(self.header_layout)

        # CONTENT
        self.content_layout = QHBoxLayout()
        # Categories List (left panel)
        self.category_list = QListWidget(self)
        self.category_list.itemClicked.connect(self.on_category_selected)
        self.content_layout.addWidget(self.category_list, 1)  # Stretch factor 1
        # Entries Scroll Area (right panel)
        self.entry_list_scroll_area = QScrollArea(self)
        self.entry_list_scroll_area.setWidgetResizable(True)
        self.entry_list = QEntryRowList(self.entry_list_scroll_area)
        self.entry_list_scroll_area.setWidget(self.entry_list)
        self.content_layout.addWidget(self.entry_list_scroll_area, 3)  # Stretch factor 3
        # End Content
        self.main_layout.addLayout(self.content_layout)

        # TODO: Some test categories/entries.
        self.categories = TEST_DATA

        # Connect to `QEntryRow` signals
        for entry_row in self.entry_row_list.entry_rows:
            entry_row.entry_text_changed.connect(self.edit_entry_text)

        # Update range buttons when entry list range start changes.
        self.entry_list.first_row_index.valueChanged.connect(self.update_range_button_states)

        # Select first category automatically
        self.selected_category_name = next(iter(self.categories.keys()), None)
        self.populate_categories()
        self.on_category_selected(self.category_list.item(0))
        self.update_range_button_states()

    def populate_categories(self):
        """Add categories to the category list."""
        self.category_list.clear()
        for category in self.categories.keys():
            item = QListWidgetItem(category)
            self.category_list.addItem(item)

    def on_category_selected(self, item: QListWidgetItem):
        """Handle category selection."""
        self.selected_category_name = item.text()
        self.entry_list.populate_entries(self.get_selected_category_entries())
        self.update_range_button_states()

    def get_selected_category_entries(self) -> list[tuple[int, str]]:
        """Get the entries for the selected category.
        
        TODO: Real entry types would vary, not just (id, text), and should use a `tp.Generic` class variable.
        TODO: Could also have a subclass method for extracting the key (id, text) data from entries (MSBEntry, etc.).
        """
        return self.categories.get(self.selected_category_name, [])

    def update_range_button_states(self):
        self.previous_button.setEnabled(self.entry_list.previous_button_valid)
        self.next_button.setEnabled(self.entry_list.next_button_valid)

    def update_entry_text(self, entry_id: int, new_text: str) -> None:
        print(f"Updating entry text for entry ID {entry_id}")
        self.get_selected_category_entries()[entry_id] = (entry_id, new_text)

    def delete_entry(self, row_index) -> None:
        print(f"Deleting entry at row {row_index}")
        
    @property
    def selected_category_entry_count(self) -> int:
        return len(self.get_selected_category_entries())


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    editor = BaseEditor()
    editor.show()
    sys.exit(app.exec())
