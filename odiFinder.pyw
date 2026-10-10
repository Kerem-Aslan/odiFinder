import requests
from datetime import datetime
import json
import os
from typing import Optional, List, Dict, Any, Set, Callable
import platform
import webbrowser
import sys
import threading
import queue
import traceback
from ui import OdiFinderUI
from network import login_to_odi, check_meals

try:
    from winotify import Notification
    WINOTIFY_AVAILABLE = True
except ImportError:
    WINOTIFY_AVAILABLE = False

try:
    import pystray
    from PIL import Image
    PILLOW_AVAILABLE = True
    PYSTRAY_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    PYSTRAY_AVAILABLE = False
    print("Pillow or pystray library not found. System tray icon will be default.")

def get_settings_path():
    if getattr(sys, 'frozen', False):  # Eğer exe'den çalışıyorsa
        if platform.system() == "Windows":
            appdata = os.getenv("APPDATA")
            if appdata:
                settings_dir = os.path.join(appdata, "odiFinder")
            else:
                # Fallback: use user home directory if APPDATA is not set
                settings_dir = os.path.join(os.path.expanduser("~"), "odiFinder")
            os.makedirs(settings_dir, exist_ok=True)
            return os.path.join(settings_dir, "settings.json")
        else:
            # Diğer platformlar için fallback
            return os.path.join(os.path.expanduser("~"), ".odiFinder_settings.json")
    else:  # py dosyasından çalışıyorsa
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# PyInstaller resource path helper
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', None)
    if base_path:
        return os.path.join(base_path, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

DEFAULT_CITY_ID = "35"
DEFAULT_REFRESH_INTERVAL_MIN = 3

class RefreshError(Exception):
    """A refresh failed in a way that should be shown to the user."""

class OdiFinderApp:
    APP_VERSION = "1.5.0"

    def __init__(self):
        self.session: Optional[requests.Session] = None
        self.username: str = ''
        self.password: str = ''
        self.target_texts: List[str] = []
        self.notifications_enabled: bool = True
        self.current_city_id: str = DEFAULT_CITY_ID
        self.city_names: Dict[str, str] = {DEFAULT_CITY_ID: "İzmir"}
        self.previously_found_meal_names: Set[str] = set()
        self.periodic_refresh_id: Optional[str] = None
        self.REFRESH_INTERVAL_MS: int = DEFAULT_REFRESH_INTERVAL_MIN * 60 * 1000
        # Work from background threads (refresh worker, tray icon) is handed to the Tk thread through this queue
        self._ui_queue: "queue.Queue[Callable[[], None]]" = queue.Queue()
        self._refresh_in_progress = False
        self._refresh_pending = False
        self.system_tray_icon: Optional[pystray.Icon] = None
        self.settings: Dict[str, Any] = {}
        self._cleanup_called_flag = False
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = resource_path('odiFinderlogo.ico')
        self.settings_path = get_settings_path()
        self.plyer_notification_available = False
        self.plyer_notification = None
        # Try plyer for all platforms as fallback
        try:
            from plyer import notification as plyer_notify_module
            self.plyer_notification = plyer_notify_module
            self.plyer_notification_available = True
        except ImportError:
            if platform.system() != "Windows":
                print("Plyer library not found for non-Windows. Notifications will be OS-dependent.")
        self._load_settings()
        threading.Thread(target=self._load_city_names, daemon=True).start()
        callbacks = {
            'on_login_attempt': self.handle_login_attempt,
            'open_debug_console': self.handle_open_debug_console,
            'on_minimize_to_tray': self.handle_minimize_to_tray,
            'on_toggle_notifications': self.handle_toggle_notifications,
            'on_edit_restaurants': self.handle_edit_restaurants,
            'on_save_city_id': self.handle_save_city_id,
            'on_toggle_theme': self.handle_toggle_theme,
            'on_save_interval': self.handle_save_interval,
            'on_refresh_now': self.handle_meal_refresh,
            'on_open_getodi': self.handle_open_getodi,
            'on_quit_application': self.handle_quit_application,
            'on_reset_settings': self.handle_reset_settings,
            'on_debug_console_closed_message': lambda: print("Debug console closed (via app callback).")
        }
        self.ui = OdiFinderUI(callbacks, self.icon_path)
        # Use the saved theme from the start, so saving settings before the main window exists doesn't overwrite it
        self.ui.current_theme_name = self.settings.get('theme', 'dark')

    def _load_settings(self):
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
            self.username = self.settings.get('username', self.username)
            self.target_texts = self.settings.get('restaurants', self.target_texts)
            self.notifications_enabled = self.settings.get('notifications_enabled', self.notifications_enabled)
            self.current_city_id = self.settings.get('city_id', self.current_city_id)
            self.REFRESH_INTERVAL_MS = self.settings.get('refresh_interval', DEFAULT_REFRESH_INTERVAL_MIN) * 60 * 1000
        except (FileNotFoundError, json.JSONDecodeError):
            print("Settings file not found or invalid. Using defaults.")
            self.settings = {}

    def _save_settings(self):
        self.settings['username'] = self.username
        self.settings['restaurants'] = self.target_texts
        self.settings['notifications_enabled'] = self.notifications_enabled
        self.settings['theme'] = self.ui.current_theme_name if self.ui else 'dark'
        self.settings['city_id'] = self.current_city_id
        self.settings['refresh_interval'] = self.REFRESH_INTERVAL_MS // (60 * 1000)
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def _load_city_names(self):
        try:
            import csv
            from io import StringIO
            city_csv_url = "https://gist.githubusercontent.com/mebaysan/7a4ba8531187fa8703ff1f22692d5fa6/raw/df4e85262ba2a4f6d6045f06f417b853fb67e78c/il.csv"
            response = requests.get(city_csv_url, timeout=10)
            if response.status_code == 200:
                city_names = {}
                csv_reader = csv.reader(StringIO(response.text))
                next(csv_reader)
                for row in csv_reader:
                    if len(row) >= 2:
                        city_names[row[0].zfill(2)] = row[1]
                if city_names:
                    self.city_names = city_names
        except Exception as e:
            print(f"Error loading city names: {e}")

    def run(self):
        self.ui.display_login_window(self.username)
        print("Exiting application run method after login window closes or fails.")

    def handle_login_attempt(self, username, password_attempt):
        self.session = login_to_odi(username, password_attempt)
        if self.session:
            self.username = username
            self.password = password_attempt
            self.settings['username'] = self.username
            self._save_settings()
            self.ui.close_login_window()
            self._initialize_main_app_components()
        else:
            self.ui.show_login_error()

    def _get_initial_ui_settings(self) -> Dict[str, Any]:
        return {
            'version': self.APP_VERSION,
            'theme': self.settings.get('theme', 'dark'),
            'notifications_enabled': self.notifications_enabled,
            'city_id': self.current_city_id,
            'refresh_interval': self.REFRESH_INTERVAL_MS // (60 * 1000)
        }

    def _initialize_main_app_components(self):
        initial_ui_settings = self._get_initial_ui_settings()
        self.ui.initialize_main_window(initial_ui_settings)
        self._process_ui_queue()
        self.handle_meal_refresh()
        self._schedule_next_refresh()
        self.ui.run_ui()

    def _run_on_ui_thread(self, func: Callable[[], None]):
        self._ui_queue.put(func)

    def _process_ui_queue(self):
        while True:
            try:
                func = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                func()
            except Exception:
                traceback.print_exc()
        if self.ui.app_root and self.ui.app_root.winfo_exists():
            self.ui.app_root.after(100, self._process_ui_queue)

    def handle_toggle_notifications(self):
        self.notifications_enabled = self.ui.get_notifications_enabled()
        self._save_settings()
        print(f"Notifications {'enabled' if self.notifications_enabled else 'disabled'}")

    def handle_edit_restaurants(self):
        self.ui.show_edit_restaurants_dialog(self.target_texts, self._save_edited_restaurants_callback)

    def _save_edited_restaurants_callback(self, new_restaurants: List[str]):
        self.target_texts = new_restaurants
        self._save_settings()
        print("Restaurant list updated.")
        self.handle_meal_refresh()

    def handle_save_city_id(self):
        new_city_id = self.ui.get_city_id_entry()
        if new_city_id.isdigit() and len(new_city_id) > 0:
            self.current_city_id = new_city_id.zfill(2)
            self._save_settings()
            print(f"City ID updated to {self.current_city_id}")
            self.handle_meal_refresh()
        else:
            self.ui.show_message(type="error", title="Error", message="City ID must be a valid number (e.g., 35).")

    def handle_toggle_theme(self):
        new_theme = "light" if self.ui.current_theme_name == "dark" else "dark"
        self.ui.apply_theme(new_theme)
        self._save_settings()
        print(f"Theme changed to {self.ui.current_theme_name}")

    def handle_reset_settings(self):
        if not self.ui.ask_yes_no("Reset Settings", "Reset all settings (restaurant list, city, theme, notifications, refresh interval) to default?"):
            return
        self.target_texts = []
        self.notifications_enabled = True
        self.current_city_id = DEFAULT_CITY_ID
        self.REFRESH_INTERVAL_MS = DEFAULT_REFRESH_INTERVAL_MIN * 60 * 1000
        self.ui.apply_theme('dark')
        self._save_settings()
        self.ui.update_settings_display(self.settings)
        print("Settings reset to defaults.")
        self._schedule_next_refresh()
        self.handle_meal_refresh()

    def handle_save_interval(self):
        try:
            interval_str = self.ui.get_interval_entry()
            interval_min = int(interval_str)
            if interval_min <= 0:
                self.ui.show_message(type="error", title="Error", message="Interval must be positive.")
                return
            self.REFRESH_INTERVAL_MS = interval_min * 60 * 1000
            self._save_settings()
            print(f"Auto-refresh interval updated to {interval_min} minutes.")
            self._cancel_periodic_refresh()
            self._schedule_next_refresh()
        except ValueError:
            self.ui.show_message(type="error", title="Error", message="Please enter a valid number for interval.")

    def handle_meal_refresh(self):
        if not self.ui.app_root or not self.ui.app_root.winfo_exists():
            print("Meal refresh called but UI not ready.")
            return
        if self._refresh_in_progress:
            # Settings changed mid-refresh: run again once the current refresh finishes
            self._refresh_pending = True
            return
        self._refresh_in_progress = True
        self.ui.set_refreshing(True)
        threading.Thread(target=self._refresh_worker, args=(list(self.target_texts), self.current_city_id), daemon=True).start()

    def _refresh_worker(self, target_texts: List[str], city_id: str):
        """Runs on a background thread so network calls don't freeze the window."""
        meals: Optional[List[Dict[str, Any]]] = None
        error_msg: Optional[str] = None
        try:
            if self.session is not None:
                meals = check_meals(self.session, target_texts, city_id)
            if meals is None:
                print("No active session or session expired. Attempting re-login...")
                meals = self._relogin_and_check_meals(target_texts, city_id)
        except RefreshError as e:
            error_msg = str(e)
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {e}"
        except Exception as e:
            traceback.print_exc()
            error_msg = f"Error updating meals: {e}"
        if error_msg:
            print(error_msg)
        self._run_on_ui_thread(lambda: self._apply_refresh_result(meals, error_msg, city_id))

    def _relogin_and_check_meals(self, target_texts: List[str], city_id: str) -> List[Dict[str, Any]]:
        if not self.username or not self.password:
            raise RefreshError("Cannot re-login: username or password not stored. Please restart the app.")
        new_session = login_to_odi(self.username, self.password)
        if not new_session:
            raise RefreshError("Session expired and re-login failed. Check your credentials/network.")
        self.session = new_session
        print("Re-login successful.")
        meals = check_meals(new_session, target_texts, city_id)
        if meals is None:
            raise RefreshError("Re-logged in, but getodi.com still shows the login page.")
        return meals

    def _apply_refresh_result(self, meals: Optional[List[Dict[str, Any]]], error_msg: Optional[str], city_id: str):
        self._refresh_in_progress = False
        self.ui.set_refreshing(False)
        refresh_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self._refresh_pending:
            self._refresh_pending = False
            self.ui.app_root.after(0, self.handle_meal_refresh)
        if error_msg or meals is None:
            # Keep previously_found_meal_names so the same restaurants don't trigger a new notification after a failed refresh
            self.ui.update_meals_display(f"{error_msg}\nWill retry on the next refresh.", refresh_time_str)
            return

        output_lines, current_meal_names_now = [], set()
        for meal in meals:
            output_lines.extend([f"Restaurant: {meal['restaurant_name']}", f"Meal: {meal['meal_name']}", f"Location: {meal['location']}", "Meals available", "-" * 40])
            current_meal_names_now.add(meal['restaurant_name'])
        newly_found = current_meal_names_now - self.previously_found_meal_names
        if newly_found and self.notifications_enabled:
            self._send_notification(f"New: {', '.join(sorted(newly_found))}"[:250])
        if not meals:
            if not self.target_texts:
                output_lines.append("No restaurants selected. Click \"Edit Restaurants\" to add the ones you want to track.")
            else:
                output_lines.append(f"No meals found for specified restaurants in {self.city_names.get(city_id, f'city {city_id}')} at this time.")
        self.previously_found_meal_names = current_meal_names_now
        self.ui.update_meals_display("\n".join(output_lines), refresh_time_str)
        print(f"GUI Refreshed: {refresh_time_str}. City: {city_id}. Found: {len(meals)}. New: {sorted(newly_found)}")

    def _send_notification(self, message_text: str):
        title = "odiFinder: New Restaurants!"
        icon_to_use = self.icon_path if self.icon_path and os.path.exists(self.icon_path) else None
        print(f"Debug _send_notification: platform={platform.system()}, WINOTIFY_AVAILABLE={WINOTIFY_AVAILABLE}, plyer_available={self.plyer_notification_available}, icon_path={self.icon_path}, icon_exists={icon_to_use is not None}")
        try:
            if platform.system() == "Windows" and WINOTIFY_AVAILABLE:
                notification = Notification(app_id="odiFinder", title=title, msg=message_text, duration="long", icon=icon_to_use or "")
                notification.show()
                print(f"Sent Winotify notification: {message_text}")
            elif self.plyer_notification_available and self.plyer_notification is not None:
                if callable(self.plyer_notification.notify):
                    self.plyer_notification.notify(title=title, message=message_text, app_name="odiFinder", timeout=10, app_icon=icon_to_use or "")
                    print(f"Sent Plyer notification: {message_text}")
                else:
                    print("Plyer notification object exists but notify() is not callable")
            else:
                print(f"Notification ready (but no backend): {title} - {message_text}")
                print(f"Debug: Windows={platform.system() == 'Windows'}, WINOTIFY={WINOTIFY_AVAILABLE}, PLYER={self.plyer_notification_available}")
                print("Please install winotify: pip install winotify")
        except Exception as e:
            print(f"Failed to send notification: {e}")
            traceback.print_exc()

    def handle_open_getodi(self):
        city_url = f"https://getodi.com/student/?city={self.current_city_id}"
        webbrowser.open_new_tab(city_url)

    def _schedule_next_refresh(self):
        self._cancel_periodic_refresh()
        if self.ui.app_root and self.ui.app_root.winfo_exists():
            self.periodic_refresh_id = self.ui.app_root.after(self.REFRESH_INTERVAL_MS, self._scheduled_refresh_task_wrapper)
            print(f"Scheduled next refresh in {self.REFRESH_INTERVAL_MS // 1000} seconds.")
        else:
            print("Cannot schedule refresh: UI not ready.")

    def _cancel_periodic_refresh(self):
        if self.periodic_refresh_id and self.ui.app_root and self.ui.app_root.winfo_exists():
            try:
                self.ui.app_root.after_cancel(self.periodic_refresh_id)
                print("Cancelled periodic refresh.")
            except Exception as e:
                print(f"Error cancelling refresh: {e}")
            self.periodic_refresh_id = None

    def _scheduled_refresh_task_wrapper(self):
        print("Auto-refresh triggered.")
        self.handle_meal_refresh()
        if self.ui.app_root and self.ui.app_root.winfo_exists():
            self._schedule_next_refresh()

    def handle_quit_application(self):
        print("Quit application requested.")
        self._cleanup()
        if self.ui:
            self.ui.quit_main_loop()

    def handle_minimize_to_tray(self):
        if not (PYSTRAY_AVAILABLE and PILLOW_AVAILABLE and self.icon_path and os.path.exists(self.icon_path)):
            missing = [dep for dep, avail in [("Pillow", PILLOW_AVAILABLE), ("pystray", PYSTRAY_AVAILABLE), ("icon", self.icon_path and os.path.exists(self.icon_path))] if not avail]
            msg = f"Cannot minimize to tray. Missing: {', '.join(missing)}."
            self.ui.show_message(type="warning", title="Minimize Info", message=msg + "\nWindow will be hidden. Use Task Manager to close if needed.")
            self.ui.withdraw_main_window()
            return
        if self.ui.withdraw_main_window():
            if self.system_tray_icon and getattr(self.system_tray_icon, 'visible', False):
                return
            try:
                if self.system_tray_icon:
                    self.system_tray_icon.stop()
                image = Image.open(self.icon_path)
                menu = pystray.Menu(
                    pystray.MenuItem("Show", self.handle_show_window_from_tray, default=True),
                    pystray.MenuItem("Exit", self.handle_exit_from_tray)
                )
                self.system_tray_icon = pystray.Icon("odiFinder", image, "odiFinder", menu)
                threading.Thread(target=self.system_tray_icon.run, daemon=True).start()
                print("System tray icon started.")
            except Exception as e:
                print(f"Failed to create/run system tray icon: {e}")
                self.ui.show_message(type="error", title="Tray Error", message=f"Could not minimize to tray: {e}")
                self.ui.deiconify_and_focus_main_window()

    def handle_show_window_from_tray(self):
        # Called on the tray icon's thread; Tk calls must happen on the main thread
        if self.system_tray_icon and getattr(self.system_tray_icon, 'visible', False):
            try:
                self.system_tray_icon.stop()
            except Exception as e:
                print(f"Error stopping tray icon: {e}")
        self.system_tray_icon = None
        self._run_on_ui_thread(self.ui.deiconify_and_focus_main_window)
        print("Application window shown from tray.")

    def handle_exit_from_tray(self):
        print("Exit requested from tray.")
        if self.system_tray_icon:
            try:
                self.system_tray_icon.stop()
            except Exception as e:
                print(f"Error stopping tray icon on exit: {e}")
            self.system_tray_icon = None
        self._run_on_ui_thread(self.handle_quit_application)

    def handle_open_debug_console(self):
        if self.ui:
            self.ui.open_debug_console(self._get_debug_console_context)
        else:
            print("Cannot open debug console: UI not initialized.")

    def _cleanup(self):
        if self._cleanup_called_flag:
            return
        self._cleanup_called_flag = True
        print("Application cleanup initiated...")
        self._cancel_periodic_refresh()
        if self.system_tray_icon:
            try:
                if getattr(self.system_tray_icon, 'visible', False):
                    self.system_tray_icon.stop()
            except Exception as e:
                print(f"Error stopping system tray icon during cleanup: {e}")
            self.system_tray_icon = None
        if self.ui and self.ui.app_root and self.ui.app_root.winfo_exists():
            print("Main UI window exists, attempting to destroy.")
            try:
                self.ui.destroy_main_window()
            except Exception as e:
                print(f"Error destroying main UI window during cleanup: {e}")
        elif self.ui and self.ui.login_window and self.ui.login_window.winfo_exists():
            print("Login UI window exists, attempting to destroy.")
            try:
                self.ui.close_login_window()
            except Exception as e:
                print(f"Error destroying login UI window during cleanup: {e}")
        print("Application cleanup finished.")

    def _get_debug_console_context(self) -> Dict[str, Any]:
        def _debug_target_texts_updater(new_list):
            if isinstance(new_list, list):
                self.target_texts = [str(item).strip() for item in new_list if str(item).strip()]
                self._save_settings()
                print(f"DebugConsole: target_texts updated and saved: {self.target_texts}")
                self.handle_meal_refresh()
            else:
                print("DebugConsole Error: Please provide a list for set_target_texts.")
        context = {
            'app': self, 'ui': self.ui,
            'get_settings': lambda: self.settings,
            'set_target_texts': _debug_target_texts_updater,
            'run_refresh': self.handle_meal_refresh,
            'get_vars': lambda: {
                "username": self.username,
                "current_theme": self.ui.current_theme_name if self.ui else 'N/A',
                "notifications": self.notifications_enabled,
                "city_id": self.current_city_id,
                "refresh_interval_ms": self.REFRESH_INTERVAL_MS,
                "previously_found_meals": self.previously_found_meal_names,
                "session_active": bool(self.session),
                "city_names_loaded": bool(self.city_names)
            }
        }
        return context

if __name__ == "__main__":
    app = OdiFinderApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nProgram terminated by user (Ctrl+C).")
    except SystemExit:
        print("Program exited via SystemExit.")
    except Exception as e:
        print(f"A critical unhandled error occurred: {e}")
        traceback.print_exc()
    finally:
        print("Top-level finally: Ensuring cleanup.")
        app._cleanup()
        print("odiFinder application has shut down.")