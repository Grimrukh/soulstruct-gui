from __future__ import annotations

__all__ = ["ToolTip"]

import tkinter as tk


class ToolTip:
    """Class that creates a tooltip for a given widget."""

    def __init__(
        self,
        main_widget,
        *child_widgets,
        text="tool tip",
        delay=500,
        wraplength=180,
        x_offset=25,
        y_offset=30,
        anchor_widget=None,
    ):
        """Entering *any* of the widgets is sufficient to trigger the tooltip, but you must leave *all* of them for it
        to time out again. The main widget will be used to determine tooltip coordinates (generally the largest)."""
        self.delay = delay
        self.wraplength = wraplength
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.widgets = [main_widget] + list(child_widgets)
        self.widget_status = {id(w): False for w in self.widgets}
        self.anchor_widget = main_widget if anchor_widget is None else anchor_widget
        self.text = text
        for widget in self.widgets:
            widget.bind("<Enter>", lambda _: self.enter(widget))
            widget.bind("<Leave>", lambda _: self.leave(widget))
            widget.bind("<ButtonPress>", lambda _: self.leave(widget))
        self.schedule_id = None
        self.tip_box = None

    def enter(self, widget):
        if self.text is None:
            return
        schedule_tip = not any(self.widget_status.values())
        self.widget_status[id(widget)] = True
        if schedule_tip:
            self.schedule()

    def leave(self, widget):
        if self.text is None:
            return
        self.widget_status[id(widget)] = False
        if not any(self.widget_status.values()):
            self.unschedule()
            self.hide_tip()

    def schedule(self):
        self.unschedule()
        self.schedule_id = self.widgets[0].after(self.delay, self.show_tip)

    def unschedule(self):
        schedule_id, self.schedule_id = self.schedule_id, None
        if schedule_id:
            self.widgets[0].after_cancel(schedule_id)

    def show_tip(self, _=None):
        x, y, cx, cy = self.anchor_widget.bbox("insert")
        x += self.anchor_widget.winfo_rootx() + self.x_offset
        y += self.anchor_widget.winfo_rooty() + self.y_offset
        self.tip_box = tk.Toplevel(self.anchor_widget)
        self.tip_box.wm_overrideredirect(True)  # remove border
        self.tip_box.wm_geometry(f"+{x}+{y}")
        tip_message = tk.Label(
            self.tip_box,
            text=self.text,
            justify="left",
            bg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            wraplength=self.wraplength,
        )
        tip_message.pack(ipadx=1)

    def hide_tip(self):
        tip_box, self.tip_box = self.tip_box, None
        if tip_box:
            tip_box.destroy()

    def destroy(self):
        if self.tip_box:
            self.tip_box.destroy()
