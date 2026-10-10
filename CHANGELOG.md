# Changelog

All notable changes to this project will be documented in this file.

## [1.5.0] - 10 October 2026

### Fixed
- The app now logs in again automatically when the getodi.com session expires (before, it silently showed "No meals found" until restarted)
- A failed refresh no longer causes duplicate "New" notifications for the same restaurants once it works again
- Pages are no longer requested with Brotli compression, which could make every check come back empty when the optional `brotli` package wasn't installed
- The saved light/dark theme is no longer reset to dark on every login
- The reset settings (🗑) button now works, with a confirmation prompt
- The reset button's tooltip no longer throws an error on hover
- The app no longer crashes on startup on systems without the `tr_TR.UTF-8` locale
- System tray "Show" and "Exit" now run on the UI thread, avoiding possible crashes or freezes
- "Askıdan al" buttons written in capitals (and "Askıdan Ücretsiz Al") are detected; buttons marked `disabled`/`aria-disabled` are treated as unavailable
- A search term that matches several restaurants now reports all of them instead of only the first
- The icon is found even when the app is started from a different folder

### Changed
- Refreshing runs in the background, so the window no longer freezes during checks; the button shows "Refreshing..." meanwhile
- Re-login no longer opens pop-up dialogs; the result is shown in the main window
- City names load in the background with a timeout instead of possibly blocking startup
- New installs start with an empty restaurant list and a hint to add restaurants
- Removed unused code and duplicate imports

## [1.4.4] - 20 December 2025
- Updated to work with the new website interface structure, so meal available count is gone :(
- "getodi.com" button now redirects to the corresponding city page

## [1.4.3] - 10 August 2025

### Changed
- Updated to work with the new website interface structure
- Brought back the old display format (available meal count is back)

## [1.4.2] - 18 June 2025

### Changed
- Updated to work with the new website interface structure
- Replaced suspended meal count checking with "Askıdan Ücretsiz Al" button availability detection
- Improved data parsing to correctly extract information according to new HTML structure:
- Updated display format to show: Restaurant, Meal, Location, and Status instead of previous format
- Removed meal count display as it's no longer relevant with the new system

### Fixed
- Fixed compatibility issues with the updated getodi.com website structure

## [1.4.1] - 27 May 2025

### Fixed
- Fixed an error where meals with 0 available count were incorrectly included in results.

## [1.4.0] - 24 May 2025

### Added
- FIRST WINDOWS RELEASE! Now users can just run the .exe file to access the odiFinder.
- On Windows: The settings file (settings.json) is now stored under %APPDATA%/odiFinder/ when running as an exe, and in the current directory when running as a script.
- A trash can "reset settings" button was added to the UI, allowing users to reset all settings with a single click.

### Fixed
- Various issues and conflicts during settings reset have been resolved.

## [1.3.1] - 20 May 2025

### Added
- Console button in GUI

### Changed
- Codebase cleaned up, unused imports and legacy code removed.
- Application modularized: network and ui files separated.
- UI code fully moved to a separate file and modernized.
- Fixed background color of buttons in dark mode.
- Minor bug fixes and code improvements.

## [1.3.0] - 20 May 2025

### Added
- System tray support with custom icon
- Dark/Light theme toggle
- City selection support for all cities in Turkey
- Minimize to system tray functionality
- Custom window icon
- Improved window positioning and sizing
- Better error handling and user feedback
- Thread-safe system tray operations
- Added getodi.com button

### Changed
- Updated default window size to 750x450
- Moved minimize button to top bar
- Improved notification system
- Enhanced error messages and logging
- Better session management
- More robust window state handling

## [1.2.0] - 19 May 2025

### Added
- Auto-refresh interval configuration

## [1.1.0] - 19 May 2025

### Added
- Settings persistence
- Simple GUI improvements

### Changed
- Default refresh interval to 3 minutes
- Improved GUI layout

## [1.0.0] - 19 May 2025

### Added
- Initial release
