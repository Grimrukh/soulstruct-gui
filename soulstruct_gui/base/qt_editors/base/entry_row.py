from __future__ import annotations

__all__ = ["QEntryRow"]

import typing as tp

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu
from PyQt6.QtCore import Qt, pyqtSignal


class QEntryRow(QFrame):
    """Represents a single row in the entry editor.

    Depending on the entry data type being represented, the entry may be passed either an `entry_index` (which implies
    the entry comes from a list, e.g an `MSBEntryList`) or an `entry_id` (which implies the entry comes from a
    dictionary, e.g. a `Param`). Exactly one of these should always be `None`; both are emitted in entry change signals.

    TODO: Better to rely on `QEntryList` vs. `QEntryDict` class, which can share 90% in a base class. Then this can just
     be a `QEntry` class that may or may not expose an ID field (`QEntryDict` only). QEntryList allows entries to be
     reordered, while QEntryDict allows ID editing and automatically orders them from that.
    """

    # Class display settings:
    # TODO: Move style arguments to style sheet.
    ENTRY_ANCHOR: tp.ClassVar[str] = "center"
    ENTRY_ROW_HEIGHT: tp.ClassVar[int] = 50

    SHOW_ENTRY_ID: tp.ClassVar[bool] = True
    EDIT_ENTRY_ID: tp.ClassVar[bool] = True  # TODO: use
    ENTRY_ID_WIDTH: tp.ClassVar[int] = 15
    ENTRY_ID_FG: tp.ClassVar[str] = "#CDF"

    ENTRY_TEXT_WIDTH: tp.ClassVar[int] = 150
    ENTRY_TEXT_FG: tp.ClassVar[str] = "#FFF"

    # Signals:
    # TODO: Could use a QSpinBox variable rather than this.
    entry_id_changed: tp.ClassVar[pyqtSignal] = pyqtSignal(int, int)  # (old_id, new_id)
    entry_text_changed: tp.ClassVar[pyqtSignal] = pyqtSignal(int, int, str)  # (entry_index, entry_id, new_text)
    entry_deleted: tp.ClassVar[pyqtSignal] = pyqtSignal(int)  # (row_index)

    # Members:
    entry_index: int | None  # *index* of entry in source data (e.g. `MSBEntryList` index); required for emitted updates
    entry_id: int | None  # *ID* of entry in source data (e.g. `Param` row ID key); real data that (may) change

    layout: QHBoxLayout
    id_label: QLabel | None
    id_line_edit: QLineEdit | None
    name_label: QLabel
    name_line_edit: QLineEdit
    context_menu: QMenu

    _active: bool

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.entry_index = None
        self.entry_id = None

        self.setFixedHeight(self.ENTRY_ROW_HEIGHT)

        # Layout for the row
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)

        if self.SHOW_ENTRY_ID and self.entry_id is not None:
            # Entry ID label
            self.id_label = QLabel(str(self.entry_id), self)
            self.id_label.setMaximumWidth(self.ENTRY_ID_WIDTH)
            self.layout.addWidget(self.id_label)
            if self.EDIT_ENTRY_ID:
                self.id_label.mousePressEvent = self.start_editing_id

        else:
            self.id_label = None

        # Entry text
        self.name_label = QLabel("Entry Text", self)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.name_label.setMaximumWidth(self.ENTRY_TEXT_WIDTH)
        self.name_label.mousePressEvent = self._start_name_edit
        self.layout.addWidget(self.name_label)
        # Entry text editing
        self.name_line_edit = QLineEdit(self)
        self.name_line_edit.setMaximumWidth(self.ENTRY_TEXT_WIDTH)
        self.name_line_edit.setText(self.name_label.text())
        self.name_line_edit.hide()
        self.name_line_edit.returnPressed.connect(self._finish_name_edit)
        self.name_line_edit.focusOutEvent = self._cancel_name_edit
        self.name_line_edit.editingFinished.connect(self._finish_name_edit)
        self.layout.addWidget(self.name_line_edit)

        # Context menu for right-click actions
        self.context_menu = QMenu(self)
        # TODO: Can handle pop-out editing here, and also emit deletion signals.
        self.context_menu.addAction("Edit Entry Text", lambda: base_editor.edit_entry_text(self.row_index))
        self.context_menu.addAction("Delete Entry", lambda: base_editor.delete_entry(self.row_index))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def update_entry(
        self,
        *,
        entry_index: int | None = None,
        entry_id: int | None = None,
        entry_name: str = "",
    ) -> None:
        """Update the row container with new data. `entry_name` cannot actually be empty."""
        if entry_index is None and entry_id is None:
            raise ValueError("Entry row must have either an entry index or an entry ID.")
        if entry_index is not None and entry_id is not None:
            raise ValueError("Entry row cannot have both an entry index and an entry ID.")
        if not entry_name:
            raise ValueError("Entry name cannot be empty.")

        if self.entry_index is not None:
            self.entry_index = entry_index
        elif self.entry_id is not None:
            self.entry_id = entry_id
            if self.id_label:
                self.id_label.setText(str(entry_id))
                self.id_line_edit.setText(str(entry_id))

        self.name_label.setText(entry_name)
        self.name_line_edit.setText(entry_name)

    def _start_id_edit(self, _=None):
        """Switch from QLabel to QLineEdit for editing."""
        if not self.id_label:
            raise ValueError("Cannot edit ID that does not exist.")
        self.id_label.hide()
        self.id_line_edit.show()
        self.id_line_edit.setFocus()

    def _finish_id_edit(self):
        """Save the edited ID text and switch back to QLabel."""
        new_id_str = self.id_line_edit.text()
        try:
            new_id = int(new_id_str)
        except ValueError:
            # Invalid entry. Restore original ID.
            self.id_line_edit.setText(str(self.entry_id))
            self.id_line_edit.hide()
            self.id_label.show()
            return
        if new_id != self.entry_id:
            self.id_label.setText(new_id_str)
            self.entry_id_changed.emit(self.entry_id, new_id)
            self.entry_id = new_id
        self.name_line_edit.hide()
        self.name_label.show()

    def _cancel_id_edit(self, _=None):
        """Cancel editing and restore the original text."""
        self.name_line_edit.setText(self.name_label.text())
        self.name_line_edit.hide()
        self.name_label.show()

    def _start_name_edit(self, _=None):
        """Switch from QLabel to QLineEdit for editing."""
        self.name_label.hide()
        self.name_line_edit.show()
        self.name_line_edit.setFocus()

    def _finish_name_edit(self):
        """Save the edited text and switch back to QLabel."""
        new_text = self.name_line_edit.text()
        if new_text != self.name_label.text():
            self.name_label.setText(new_text)
            self.entry_text_changed.emit(self.entry_index, self.entry_id, new_text)
        self.name_line_edit.hide()
        self.name_label.show()

    def _cancel_name_edit(self, _=None):
        """Cancel editing and restore the original text."""
        self.name_line_edit.setText(self.name_label.text())
        self.name_line_edit.hide()
        self.name_label.show()

    def show_context_menu(self, pos) -> None:
        """Show the context menu."""
        self.context_menu.exec(self.mapToGlobal(pos))
