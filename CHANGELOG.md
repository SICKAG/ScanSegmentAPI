# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.1] - 2026-05-05

### Changed

* Switched from plain `print` to `logging`

### Fixed

* Fixed a bug where connections where not closed properly

## [3.0.0] - 2024-09-26

### Added

* Added support for TCP
* Migrated code from scansegmentdecoding to this package

### Changed

* Changed from camelCase to snake_case in method and variable names

## [2.0.1] - 2023-10-10

### Added

* Package can now be installed
* Added examples in readme

## [2.0.0] - 2023-05-17

### Added

* Added support for Compact format telegram type 1 format version 4
* Added the distance scaling factor
* Added a long form parameter for the number of segments that shall be received
* Added examples

### Fixed

* Fixed a bug in the Compact format telegram type 1 format where the theta and properties channels were switched

### Removed

* Compact format telegram type 1 version 3 is no longer supported

## [1.0.0] - 2023-03-14

### Added

* Added unit tests
* Added documentation

### Changed

* Refactored application to match quality standards
