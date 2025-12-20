# Changelog

All notable changes to this project will be documented in this file.

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
