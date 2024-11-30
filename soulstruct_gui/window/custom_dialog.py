from __future__ import annotations

__all__ = ["CustomDialog"]

from .super_frame import SuperFrame


class CustomDialog(SuperFrame):
    def __init__(
        self,
        master: FRAMELIKE_TYPING,
        title="Custom Dialog",
        message="",
        font: FONT_TYPING = None,
        button_names=(),
        button_kwargs=(),
        style_defaults=None,
        default_output=None,
        cancel_output=None,
        return_output=None,
        escape_enabled=True,
        **kwargs,
    ):
        if kwargs:
            raise ValueError("Base `CustomDialog` class does not support any kwargs.")

        if style_defaults:
            self.STYLE_DEFAULTS = style_defaults
        if button_kwargs and len(button_names) != len(button_kwargs):
            raise ValueError("Number of `button_kwargs` dicts (if any are given) must match number of `button_names`.")
        super().__init__(toplevel=True, window_title=title, master=master)
        self.output = default_output
        self.cancel_output = cancel_output
        self.default_output = default_output

        self.build(message, font, button_names, button_kwargs)

        self.protocol("WM_DELETE_WINDOW", self.wm_delete_window)
        self.resizable(width=False, height=False)
        if escape_enabled:
            bind_to_all_children(self.toplevel, "<Escape>", lambda _: self.wm_delete_window())
        self.return_output = return_output
        bind_to_all_children(self.toplevel, "<Return>", self.return_event)

        self.set_geometry(relative_position=(0.5, 0.3), transient=True)

    def build(self, message, font, button_names, button_kwargs):
        """You can override this as desired, as long as you call `self.build_buttons()` at some point.

        Otherwise you can construct your own buttons with commands `lambda s=self, output=i: s.done(output)` for each
        button index `i`).
        """
        with self.set_master(auto_rows=0, padx=20, pady=20):
            self.Label(text=message, font=font, pady=20)
            self.build_buttons(button_names, button_kwargs)

    def build_buttons(self, button_names, button_kwargs):
        with self.set_master(auto_columns=0, pady=20):
            for i in range(len(button_names)):
                button = self.Button(
                    text=button_names[i],
                    command=lambda output=i: self.done(output),
                    padx=5,
                    **(button_kwargs[i] if button_kwargs else {}),
                )
                if i == self.default_output:
                    button["relief"] = RIDGE

    def go(self):
        self.toplevel.wait_visibility()
        self.toplevel.grab_set()
        self.toplevel.mainloop()
        self.toplevel.destroy()
        return self.output

    def return_event(self, _):
        """Event that occurs when the user presses the Enter key. Returns `self.return_output` if specified, or rings
        bell."""
        if self.return_output is None:
            self.toplevel.bell()
        else:
            self.done(self.return_output)

    def wm_delete_window(self):
        """Function that occurs when the user closes the window using the corner X, Alt-F4, etc. Returns
        `self.cancel_output` if specified, or rings bell.

        If dialog was created with `escape_enabled=True`, pressing Escape will also close the window (if.
        """
        if self.cancel_output is None:
            self.toplevel.bell()
        else:
            self.done(self.cancel_output)

    def done(self, num):
        self.output = num
        self.toplevel.quit()