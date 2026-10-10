import tkinter as tk
from tkinter import messagebox, font as tkFont
import os
import sys
import code # For debug console
import platform

# Define Theme Colors
DARK_THEME = {
    "APP_BG": "#2E2E2E", "WIDGET_BG": "#3C3C3C", "BUTTON_BG": "#505050",
    "BUTTON_ACTIVE_BG": "#6A6A6A", "TEXT_FG": "#E0E0E0", "TEXT_AREA_BG": "#1E1E1E",
    "TEXT_AREA_FG": "#D0D0D0", "SELECT_BG": "#4A4A4A", "BUTTON_TEXT_FG": "#FFFFFF",
    "ENTRY_INSERT_BG": "#E0E0E0"
}
LIGHT_THEME = {
    "APP_BG": "#F0F0F0", "WIDGET_BG": "#E0E0E0", "BUTTON_BG": "#D0D0D0",
    "BUTTON_ACTIVE_BG": "#B0B0B0", "TEXT_FG": "#1E1E1E", "TEXT_AREA_BG": "#FFFFFF",
    "TEXT_AREA_FG": "#000000", "SELECT_BG": "#C0C0C0", "BUTTON_TEXT_FG": "#000000",
    "ENTRY_INSERT_BG": "#000000"
}
LOGIN_DARK_COLOR_BG = "#2E2E2E"
LOGIN_TEXT_AREA_COLOR_BG = "#1E1E1E"
LOGIN_TEXT_AREA_COLOR_FG = "#D0D0D0"
LOGIN_TEXT_COLOR_FG = "#E0E0E0"
LOGIN_BUTTON_COLOR_BG = "#505050"
LOGIN_BUTTON_TEXT_COLOR_FG = "#FFFFFF"
LOGIN_BUTTON_COLOR_ACTIVE_BG = "#6A6A6A"


class OdiFinderUI:
    def __init__(self, callbacks, icon_path):
        self.callbacks = callbacks if callbacks is not None else {} # Ensure callbacks is a dict
        self.icon_path = icon_path
        self.app_root = None
        self.login_window = None
        self.system_tray_icon = None # Managed by main app, but UI might interact
        self.tooltip = None  # Initialize tooltip attribute

        self.username_entry = None
        self.password_entry = None
        
        self.current_theme_name = 'dark'
        self.active_colors = DARK_THEME

        # Main window widgets that need to be accessed
        self.settings_frame = None
        self.console_button = None
        self.minimize_button = None
        self.notifications_toggle = None
        self.notifications_var = None
        self.edit_restaurants_button = None
        self.city_id_label = None
        self.city_id_entry = None
        self.save_city_button = None
        self.theme_toggle_button = None
        self.meals_text_area = None
        self.controls_frame = None
        self.last_refreshed_label = None
        self.interval_frame = None
        self.interval_prompt_label = None
        self.interval_entry = None
        self.save_interval_button = None
        self.refresh_button = None
        self.getodi_button = None
        self.reset_settings_button = None
        self.button_frame_main = None
        
        # Debug console state
        self._debug_console_state = {
            "window": None, "console_instance": None, "original_stdout": None,
            "original_stderr": None, "ps1": ">>> ", "ps2": "... ",
            "cleanup_func_registered": False, "output_text_widget": None,
            "input_entry_widget": None,
            "debug_run_button": None # Added to store debug run button
        }
        try:
            self._debug_console_state["ps1"] = sys.ps1
            self._debug_console_state["ps2"] = sys.ps2
        except AttributeError:
            pass


    def _get_callback(self, callback_name, *default_args_for_lambda):
        """Safely retrieves a callback, returning a no-op lambda if not found."""
        if not isinstance(self.callbacks, dict):
             self.callbacks = {} # Should not happen if __init__ is correct
        
        # For callbacks that take arguments, create a lambda that can accept them but does nothing.
        # This requires knowing the number of arguments, or using a generic lambda *args, **kwargs.
        # For simplicity, specific lambdas are used where arity is known (e.g., login)
        # For others, a simple no-arg lambda is fine if the call site doesn't pass args or handles None.
        if callback_name == 'on_login_attempt':
            return self.callbacks.get(callback_name, lambda u, p: None)
        # Add other specific arity lambdas if needed
        # Default for no-argument callbacks or where None is handled by caller
        return self.callbacks.get(callback_name, lambda: None)

    def _set_icon_for_window(self, window_instance):
        if not (self.icon_path and os.path.exists(self.icon_path)): return
        try: window_instance.iconbitmap(default=self.icon_path)
        except Exception as e: print(f"Could not set program icon ({self.icon_path}): {e}")

    def display_login_window(self, initial_username=""):
        self.login_window = tk.Tk()
        self.login_window.title("Login")
        self._set_icon_for_window(self.login_window)
        self.login_window.configure(bg=LOGIN_DARK_COLOR_BG)
        self.login_window.geometry(f"300x150+{(self.login_window.winfo_screenwidth() - 300) // 2}+{(self.login_window.winfo_screenheight() - 150) // 2}")

        username_frame = tk.Frame(self.login_window, bg=LOGIN_DARK_COLOR_BG)
        username_frame.pack(pady=15)
        tk.Label(username_frame, text="Username:", bg=LOGIN_DARK_COLOR_BG, fg=LOGIN_TEXT_COLOR_FG).pack(side=tk.LEFT, padx=5)
        self.username_entry = tk.Entry(username_frame, width=30, bg=LOGIN_TEXT_AREA_COLOR_BG, fg=LOGIN_TEXT_AREA_COLOR_FG, insertbackground=LOGIN_TEXT_AREA_COLOR_FG)
        self.username_entry.pack(side=tk.LEFT)
        self.username_entry.insert(0, initial_username)
        
        password_frame = tk.Frame(self.login_window, bg=LOGIN_DARK_COLOR_BG)
        password_frame.pack(pady=10)
        tk.Label(password_frame, text="Password:", bg=LOGIN_DARK_COLOR_BG, fg=LOGIN_TEXT_COLOR_FG).pack(side=tk.LEFT, padx=5)
        self.password_entry = tk.Entry(password_frame, width=30, show="*", bg=LOGIN_TEXT_AREA_COLOR_BG, fg=LOGIN_TEXT_AREA_COLOR_FG, insertbackground=LOGIN_TEXT_AREA_COLOR_FG)
        self.password_entry.pack(side=tk.LEFT)
        def _login_action():
            # Guard against None before calling get()
            if self.username_entry is None or self.password_entry is None:
                messagebox.showerror("Error", "Login form not properly initialized", parent=self.login_window)
                return
                
            username = self.username_entry.get().strip()
            password = self.password_entry.get()
            if not (username and password):
                messagebox.showerror("Error", "Username and password are required!", parent=self.login_window)
                return
            self._get_callback('on_login_attempt')(username, password)
        
        self.username_entry.bind('<Return>', lambda e: _login_action())
        self.password_entry.bind('<Return>', lambda e: _login_action())
        login_button = tk.Button(self.login_window, text="Login", command=_login_action, bg=LOGIN_BUTTON_COLOR_BG, fg=LOGIN_BUTTON_TEXT_COLOR_FG, activebackground=LOGIN_BUTTON_COLOR_ACTIVE_BG, activeforeground=LOGIN_BUTTON_TEXT_COLOR_FG)
        login_button.pack(pady=10)
        
        self.login_window.mainloop()

    def close_login_window(self):
        if self.login_window:
            self.login_window.destroy()
            self.login_window = None
            
    def show_login_error(self, title="Login Failed", message="Incorrect username or password."):
        if self.login_window:
            messagebox.showerror(title, message, parent=self.login_window)

    def initialize_main_window(self, initial_settings):
        self.app_root = tk.Tk()
        self.app_root.title(f"odiFinder {initial_settings.get('version', '')}".strip())
        self._set_icon_for_window(self.app_root)
        self.app_root.geometry(f"750x450+{(self.app_root.winfo_screenwidth() - 750) // 2}+{(self.app_root.winfo_screenheight() - 450) // 2}")

        self.current_theme_name = initial_settings.get('theme', 'dark')
        self.active_colors = DARK_THEME if self.current_theme_name == 'dark' else LIGHT_THEME
        
        self.settings_frame = tk.Frame(self.app_root)
        self.settings_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.console_button = tk.Button(self.settings_frame, text=">_", command=self._get_callback('open_debug_console'), relief=tk.FLAT, borderwidth=0, padx=5, pady=2, font=("Consolas", 9))
        self.console_button.pack(side=tk.RIGHT, padx=(0, 0))

        self.minimize_button = tk.Button(self.settings_frame, text="Minimize", command=self._get_callback('on_minimize_to_tray'), relief=tk.FLAT, borderwidth=0, padx=5, pady=2)
        self.minimize_button.pack(side=tk.RIGHT, padx=5)

        self.notifications_var = tk.BooleanVar(value=initial_settings.get('notifications_enabled', True))
        self.notifications_toggle = tk.Checkbutton(self.settings_frame, text="Send Notifications", variable=self.notifications_var, command=self._get_callback('on_toggle_notifications'), highlightthickness=0, borderwidth=0)
        self.notifications_toggle.pack(side=tk.LEFT, padx=5)

        self.edit_restaurants_button = tk.Button(self.settings_frame, text="Edit Restaurants", command=self._get_callback('on_edit_restaurants'), relief=tk.FLAT, borderwidth=0, padx=5, pady=2)
        self.edit_restaurants_button.pack(side=tk.LEFT, padx=5)
        
        self.city_id_label = tk.Label(self.settings_frame, text="City ID (Plate):")
        self.city_id_label.pack(side=tk.LEFT, padx=(10, 0))
        self.city_id_entry = tk.Entry(self.settings_frame, width=4, relief=tk.SOLID, borderwidth=1)
        self.city_id_entry.pack(side=tk.LEFT, padx=(2,5))
        self.city_id_entry.insert(0, initial_settings.get('city_id', "35"))
        
        self.save_city_button = tk.Button(self.settings_frame, text="Set City", command=self._get_callback('on_save_city_id'), relief=tk.FLAT, borderwidth=0, padx=5, pady=2)
        self.save_city_button.pack(side=tk.LEFT, padx=5)

        self.theme_toggle_button = tk.Button(self.settings_frame, text="Light Mode" if self.current_theme_name == "dark" else "Dark Mode", command=self._get_callback('on_toggle_theme'), relief=tk.FLAT, borderwidth=0, padx=5, pady=2)
        self.theme_toggle_button.pack(side=tk.LEFT, padx=5)

        # Add reset settings button with trash can icon
        self.reset_settings_button = tk.Button(
            self.settings_frame,
            text="🗑",  # Trash can emoji
            command=self._get_callback('on_reset_settings'),
            relief=tk.FLAT,
            borderwidth=0,
            padx=5,
            pady=2,
            font=("Segoe UI Emoji", 10),  # Use emoji font for better icon display
            bg=self.active_colors["BUTTON_BG"],
            fg=self.active_colors["BUTTON_TEXT_FG"],
            activebackground=self.active_colors["BUTTON_ACTIVE_BG"],
            activeforeground=self.active_colors["BUTTON_TEXT_FG"]
        )
        self.reset_settings_button.pack(side=tk.LEFT, padx=5)
        # Add tooltip
        self._create_tooltip(self.reset_settings_button, "Reset all settings to default")

        self.meals_text_area = tk.Text(self.app_root, wrap=tk.WORD, height=15, width=60, font=tkFont.Font(family="Arial", size=12), relief=tk.SOLID, borderwidth=1, bd=1, state=tk.DISABLED)
        self.meals_text_area.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)

        self.controls_frame = tk.Frame(self.app_root)
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.last_refreshed_label = tk.Label(self.controls_frame, text="Last Refreshed: N/A")
        self.last_refreshed_label.pack(side=tk.LEFT, padx=5)
        
        self.interval_frame = tk.Frame(self.controls_frame)
        self.interval_frame.pack(side=tk.LEFT, padx=5)
        self.interval_prompt_label = tk.Label(self.interval_frame, text="Auto-refresh interval (minutes):")
        self.interval_prompt_label.pack(side=tk.LEFT, padx=5)
        self.interval_entry = tk.Entry(self.interval_frame, width=5)
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        self.interval_entry.insert(0, str(initial_settings.get('refresh_interval', 3)))
        
        self.save_interval_button = tk.Button(self.interval_frame, text="Save", command=self._get_callback('on_save_interval'), relief=tk.FLAT, borderwidth=0, padx=5, pady=2)
        self.save_interval_button.pack(side=tk.LEFT, padx=5)
        
        button_frame_main = tk.Frame(self.controls_frame)
        button_frame_main.pack(side=tk.RIGHT)
        self.button_frame_main = button_frame_main
        self.refresh_button = tk.Button(button_frame_main, text="Refresh Now", command=self._get_callback('on_refresh_now'), relief=tk.FLAT, borderwidth=0, padx=5, pady=2, highlightthickness=0)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        self.getodi_button = tk.Button(button_frame_main, text="getodi.com", command=self._get_callback('on_open_getodi'), relief=tk.FLAT, borderwidth=0, padx=10, pady=2, highlightthickness=0)
        self.getodi_button.pack(side=tk.LEFT, padx=5)

        self.apply_theme(self.current_theme_name)
        
        self.app_root.protocol("WM_DELETE_WINDOW", self._get_callback('on_quit_application'))
        
    def run_ui(self):
        if self.app_root:
            self.app_root.mainloop()

    def destroy_main_window(self):
        if self.app_root:
            if self._debug_console_state["window"] and self._debug_console_state["window"].winfo_exists():
                self._on_debug_console_close_internal()
            self.app_root.destroy()
            self.app_root = None

    def apply_theme(self, theme_name):
        self.current_theme_name = theme_name
        self.active_colors = LIGHT_THEME if self.current_theme_name == "light" else DARK_THEME
        
        if self.theme_toggle_button: 
             self.theme_toggle_button.config(text="Dark Mode" if self.current_theme_name == "light" else "Light Mode")

        if not self.app_root or not self.app_root.winfo_exists():
            return

        self.app_root.configure(bg=self.active_colors["APP_BG"])
        
        widgets_to_theme = [
            (self.settings_frame, "WIDGET_BG", None), (self.notifications_toggle, "WIDGET_BG", "TEXT_FG"),
            (self.edit_restaurants_button, "BUTTON_BG", "BUTTON_TEXT_FG"), (self.city_id_label, "WIDGET_BG", "TEXT_FG"),
            (self.save_city_button, "BUTTON_BG", "BUTTON_TEXT_FG"), (self.theme_toggle_button, "BUTTON_BG", "BUTTON_TEXT_FG"),
            (self.controls_frame, "WIDGET_BG", None), (self.last_refreshed_label, "WIDGET_BG", "TEXT_FG"),
            (self.interval_frame, "WIDGET_BG", None), (self.interval_prompt_label, "WIDGET_BG", "TEXT_FG"),
            (self.save_interval_button, "BUTTON_BG", "BUTTON_TEXT_FG"), 
            (self.refresh_button, "BUTTON_BG", "BUTTON_TEXT_FG"), (self.minimize_button, "BUTTON_BG", "BUTTON_TEXT_FG"),
            (self.console_button, "BUTTON_BG", "BUTTON_TEXT_FG"), (self.button_frame_main, "WIDGET_BG", None)
        ]

        for widget, w_bg_key, w_fg_key in widgets_to_theme:
            if widget and widget.winfo_exists():
                conf = {}
                if w_bg_key: conf["bg"] = self.active_colors[w_bg_key]
                if w_fg_key: conf["fg"] = self.active_colors[w_fg_key]
                if w_bg_key and "BUTTON" in w_bg_key: 
                    conf["activebackground"] = self.active_colors["BUTTON_ACTIVE_BG"]
                    conf["activeforeground"] = self.active_colors["BUTTON_TEXT_FG"]
                    conf["highlightbackground"] = self.active_colors["BUTTON_BG"]
                widget.configure(**conf)

        if self.notifications_toggle and self.notifications_toggle.winfo_exists():
            self.notifications_toggle.configure(selectcolor=self.active_colors["SELECT_BG"], activebackground=self.active_colors["WIDGET_BG"], activeforeground=self.active_colors["TEXT_FG"])
        if self.city_id_entry and self.city_id_entry.winfo_exists():
            self.city_id_entry.configure(bg=self.active_colors["TEXT_AREA_BG"], fg=self.active_colors["TEXT_AREA_FG"], insertbackground=self.active_colors["ENTRY_INSERT_BG"])
        if self.getodi_button and self.getodi_button.winfo_exists():
            self.getodi_button.configure(bg="#ffcf26", fg="#000000", activebackground="#ffcf26", activeforeground="#000000")
        if self.meals_text_area and self.meals_text_area.winfo_exists():
            self.meals_text_area.configure(bg=self.active_colors["TEXT_AREA_BG"], fg=self.active_colors["TEXT_AREA_FG"])
        if self.interval_entry and self.interval_entry.winfo_exists():
            self.interval_entry.configure(bg=self.active_colors["TEXT_AREA_BG"], fg=self.active_colors["TEXT_AREA_FG"], insertbackground=self.active_colors["ENTRY_INSERT_BG"])

        if self._debug_console_state["window"] and self._debug_console_state["window"].winfo_exists():
            self._debug_console_state["window"].configure(bg=self.active_colors["APP_BG"])
            if self._debug_console_state["output_text_widget"]:
                self._debug_console_state["output_text_widget"].configure(bg=self.active_colors["TEXT_AREA_BG"], fg=self.active_colors["TEXT_AREA_FG"])
            if self._debug_console_state["input_entry_widget"]:
                 self._debug_console_state["input_entry_widget"].configure(bg=self.active_colors["TEXT_AREA_BG"], fg=self.active_colors["TEXT_AREA_FG"], insertbackground=self.active_colors["ENTRY_INSERT_BG"])
                 if self._debug_console_state.get("debug_run_button") and self._debug_console_state["debug_run_button"].winfo_exists():
                     self._debug_console_state["debug_run_button"].configure(bg=self.active_colors["BUTTON_BG"], fg=self.active_colors["BUTTON_TEXT_FG"], activebackground=self.active_colors["BUTTON_ACTIVE_BG"], activeforeground=self.active_colors["BUTTON_TEXT_FG"])

        if self.reset_settings_button and self.reset_settings_button.winfo_exists():
            self.reset_settings_button.configure(bg=self.active_colors["BUTTON_BG"], fg=self.active_colors["BUTTON_TEXT_FG"], activebackground=self.active_colors["BUTTON_ACTIVE_BG"], activeforeground=self.active_colors["BUTTON_TEXT_FG"])

    def update_meals_display(self, text_to_display, refresh_time_str):
        if not (self.app_root and self.app_root.winfo_exists()): return
        if self.last_refreshed_label and self.last_refreshed_label.winfo_exists():
            self.last_refreshed_label.config(text=f"Last Refreshed: {refresh_time_str}")
        if self.meals_text_area and self.meals_text_area.winfo_exists():
            self.meals_text_area.config(state=tk.NORMAL)
            self.meals_text_area.delete(1.0, tk.END)
            self.meals_text_area.insert(tk.END, text_to_display)
            self.meals_text_area.config(state=tk.DISABLED)
        if self.app_root and self.app_root.winfo_exists():
            self.app_root.update_idletasks()

    def get_city_id_entry(self):
        return self.city_id_entry.get().strip() if self.city_id_entry else ""

    def get_interval_entry(self):
        return self.interval_entry.get().strip() if self.interval_entry else ""

    def get_notifications_enabled(self):
        return self.notifications_var.get() if self.notifications_var else True
        
    def show_message(self, type="info", title="Info", message=""):
        parent = self.app_root if self.app_root and self.app_root.winfo_exists() else self.login_window
        if not parent or not parent.winfo_exists(): # Fallback if no window is available
            print(f"[{type.upper()}] {title}: {message}") # Print to console as last resort
            return

        if type == "error": messagebox.showerror(title, message, parent=parent)
        elif type == "warning": messagebox.showwarning(title, message, parent=parent)
        else: messagebox.showinfo(title, message, parent=parent)

    def ask_yes_no(self, title, message):
        parent = self.app_root if self.app_root and self.app_root.winfo_exists() else None
        return messagebox.askyesno(title, message, parent=parent)

    def set_refreshing(self, is_refreshing):
        if self.refresh_button and self.refresh_button.winfo_exists():
            self.refresh_button.config(text="Refreshing..." if is_refreshing else "Refresh Now",
                                       state=tk.DISABLED if is_refreshing else tk.NORMAL)
            
    def show_edit_restaurants_dialog(self, current_restaurants, save_callback):
        if not self.app_root: return

        edit_window = tk.Toplevel(self.app_root)
        edit_window.title("Edit Restaurant List")
        edit_window.configure(bg=self.active_colors["APP_BG"])
        edit_window.transient(self.app_root)
        edit_window.grab_set()
        self._set_icon_for_window(edit_window)
        
        if self.app_root.winfo_exists():
            edit_window.geometry(f"400x300+{(self.app_root.winfo_x() + (self.app_root.winfo_width() - 400) // 2)}+{(self.app_root.winfo_y() + (self.app_root.winfo_height() - 300) // 2)}")
        else: edit_window.geometry("400x300")
            
        tk.Label(edit_window, text="Enter restaurants (one per line):", bg=self.active_colors["APP_BG"], fg=self.active_colors["TEXT_FG"]).pack(pady=(10,5))
        text_area = tk.Text(edit_window, height=10, width=40, font=tkFont.Font(family="Arial", size=12), bg=self.active_colors["TEXT_AREA_BG"], fg=self.active_colors["TEXT_AREA_FG"], insertbackground=self.active_colors["ENTRY_INSERT_BG"], relief=tk.SOLID, borderwidth=1, bd=1)
        text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        text_area.insert('1.0', '\n'.join(current_restaurants))
        
        def _save_action():
            new_restaurants = [r.strip() for r in text_area.get('1.0', tk.END).split('\n') if r.strip()]
            if new_restaurants:
                save_callback(new_restaurants)
                edit_window.destroy()
            else: messagebox.showerror("Error", "Restaurant list cannot be empty!", parent=edit_window)
                
        button_frame_edit = tk.Frame(edit_window, bg=self.active_colors["APP_BG"])
        button_frame_edit.pack(pady=(5,10))
        tk.Button(button_frame_edit, text="Save", command=_save_action, bg=self.active_colors["BUTTON_BG"], fg=self.active_colors["BUTTON_TEXT_FG"], activebackground=self.active_colors["BUTTON_ACTIVE_BG"], activeforeground=self.active_colors["BUTTON_TEXT_FG"], relief=tk.FLAT, borderwidth=0, padx=10, pady=3).pack()

    class DebugConsoleRedirector:
        def __init__(self, text_widget):
            self.text_widget = text_widget
            self.buffer = ""
        def write(self, s):
            self.buffer += s
            if self.text_widget.winfo_exists():
                self.text_widget.after(0, self._update_text_widget)
        def _update_text_widget(self):
            if self.text_widget.winfo_exists():
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, self.buffer)
                self.text_widget.see(tk.END)
                self.text_widget.config(state=tk.DISABLED)
                self.buffer = ""
        def flush(self): pass

    def open_debug_console(self, console_context_provider):
        if self._debug_console_state["window"] and self._debug_console_state["window"].winfo_exists():
            self._debug_console_state["window"].lift()
            self._debug_console_state["window"].focus_force()
            return

        self._debug_console_state["window"] = tk.Toplevel(self.app_root)
        self._debug_console_state["window"].title("Debug Console")
        self._debug_console_state["window"].geometry("700x500")
        self._set_icon_for_window(self._debug_console_state["window"])
        self._debug_console_state["window"].configure(bg=self.active_colors["APP_BG"])

        self._debug_console_state["output_text_widget"] = tk.Text(self._debug_console_state["window"], wrap=tk.WORD, state=tk.DISABLED, bg=self.active_colors["TEXT_AREA_BG"], fg=self.active_colors["TEXT_AREA_FG"], font=("Consolas", 10) if platform.system() == "Windows" else ("Monospace", 10))
        self._debug_console_state["output_text_widget"].pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        input_frame = tk.Frame(self._debug_console_state["window"], bg=self.active_colors["APP_BG"])
        input_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        self._debug_console_state["input_entry_widget"] = tk.Entry(input_frame, bg=self.active_colors["TEXT_AREA_BG"], fg=self.active_colors["TEXT_AREA_FG"], insertbackground=self.active_colors["ENTRY_INSERT_BG"], font=("Consolas", 10) if platform.system() == "Windows" else ("Monospace", 10))
        self._debug_console_state["input_entry_widget"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))

        if not self._debug_console_state["original_stdout"]: self._debug_console_state["original_stdout"] = sys.stdout
        if not self._debug_console_state["original_stderr"]: self._debug_console_state["original_stderr"] = sys.stderr
        
        sys.stdout = OdiFinderUI.DebugConsoleRedirector(self._debug_console_state["output_text_widget"])
        sys.stderr = sys.stdout

        console_context = console_context_provider()
        self._debug_console_state["console_instance"] = code.InteractiveConsole(locals=console_context)
        console_context['console'] = self._debug_console_state["console_instance"]

        output_text = self._debug_console_state["output_text_widget"]
        output_text.config(state=tk.NORMAL)
        output_text.insert(tk.END, f"Python {sys.version.split()[0]} on {sys.platform}\nodiFinder Debug Console. Type 'help(console_context)' or 'get_vars()' for app variables.\n")
        output_text.insert(tk.END, self._debug_console_state["ps1"])
        output_text.config(state=tk.DISABLED)

        def push_line_console(event=None):
            line = self._debug_console_state["input_entry_widget"].get()
            self._debug_console_state["input_entry_widget"].delete(0, tk.END)
            if not self._debug_console_state["console_instance"]: return

            is_multiline = self._debug_console_state["console_instance"].push(line)
            
            current_output_widget = self._debug_console_state["output_text_widget"]
            current_output_widget.config(state=tk.NORMAL)
            current_prompt = self._debug_console_state["ps2"] if is_multiline else self._debug_console_state["ps1"]
            current_output_widget.insert(tk.END, current_prompt)
            current_output_widget.see(tk.END)
            current_output_widget.config(state=tk.DISABLED)
            self._debug_console_state["input_entry_widget"].focus_set()

        self._debug_console_state["input_entry_widget"].bind("<Return>", push_line_console)
        self._debug_console_state["debug_run_button"] = tk.Button(input_frame, text="Run", command=push_line_console, bg=self.active_colors["BUTTON_BG"], fg=self.active_colors["BUTTON_TEXT_FG"], activebackground=self.active_colors["BUTTON_ACTIVE_BG"])
        self._debug_console_state["debug_run_button"].pack(side=tk.LEFT, padx=(5,0))
            
        self._debug_console_state["window"].protocol("WM_DELETE_WINDOW", self._on_debug_console_close_internal)
        self._debug_console_state["cleanup_func_registered"] = True
        self._debug_console_state["input_entry_widget"].focus_set()

    def _on_debug_console_close_internal(self):
        if self._debug_console_state["original_stdout"]:
            sys.stdout = self._debug_console_state["original_stdout"]
            self._debug_console_state["original_stdout"] = None
        if self._debug_console_state["original_stderr"]:
            sys.stderr = self._debug_console_state["original_stderr"]
            self._debug_console_state["original_stderr"] = None
        
        if self._debug_console_state["window"] and self._debug_console_state["window"].winfo_exists():
            self._debug_console_state["window"].destroy()
        
        self._debug_console_state["window"] = None
        self._debug_console_state["console_instance"] = None
        self._debug_console_state["output_text_widget"] = None
        self._debug_console_state["input_entry_widget"] = None
        
        self._get_callback('on_debug_console_closed_message')()
        self._debug_console_state["cleanup_func_registered"] = False

    def deiconify_and_focus_main_window(self):
        if self.app_root and self.app_root.winfo_exists():
            try:
                self.app_root.deiconify()
                self.app_root.lift()
                self.app_root.focus_force()
            except Exception as e:
                print(f"Error showing main window: {e}")

    def withdraw_main_window(self):
        if self.app_root and self.app_root.winfo_exists():
            try:
                self.app_root.withdraw()
            except tk.TclError as e:
                print(f"Error minimizing main window: {e}")
                self.show_message("error", "Minimize Error", f"Could not minimize to tray: {e}")
                return False
        return True
        
    def quit_main_loop(self):
        if self.app_root and self.app_root.winfo_exists():
            self.app_root.quit()

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a given widget"""
        def show_tooltip(event):
            if self.tooltip is not None:
                self.tooltip.destroy()
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            
            # Create a toplevel window
            self.tooltip = tk.Toplevel(widget)
            # Leaves only the label and removes the app window
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=text, justify=tk.LEFT,
                           background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                           font=("tahoma", 8))  # Fixed font tuple
            label.pack(ipadx=1)
            
        def hide_tooltip(event):
            if self.tooltip is not None:
                self.tooltip.destroy()
                self.tooltip = None
                
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def update_settings_display(self, settings):
        """Update UI elements with new settings values"""
        if self.login_window and self.username_entry:
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, settings.get('username', ''))
        
        if self.notifications_var:
            self.notifications_var.set(settings.get('notifications_enabled', True))
            
        if self.city_id_entry:
            self.city_id_entry.delete(0, tk.END)
            self.city_id_entry.insert(0, settings.get('city_id', '35'))
            
        if self.interval_entry:
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, str(settings.get('refresh_interval', 3))) 