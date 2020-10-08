# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2018-12-04

### Changed

* An `InvalidTimeError` is raise, when a thumbnail could not be generated
  * This can happens if the chosen time is too close to the end of the video or if the video is shorter.

## [0.3.1] - 2018-11-16

### Fixed

* add missing migration

## [0.3.0] 2018-11-16

### Added

* Example for Form usage

### Changed

* Switched to poetry for dependency management and packaging
* Support for Python 3.7
* Support for Django 2.1
* Dropped Support for Django <1.11

## [0.2.0] - 2018-01-21

### Added

* Support for django 1.11 and 2.0 (Thanks @goranpavlovic)

## [0.1.0] -2017-04-24

* Initial release

[Unreleased]: https://github.com/escaped/django-video-encoding/compare/0.4.0...HEAD
[0.4.0]: https://github.com/escaped/django-video-encoding/compare/0.3.1...0.4.0
[0.3.1]: https://github.com/escaped/django-video-encoding/compare/0.3.0...0.3.1
[0.3.0]: https://github.com/escaped/django-video-encoding/compare/0.3.0...0.2.0
[0.2.0]: https://github.com/escaped/django-video-encoding/compare/0.10...0.2.0
[0.1.0]: https://github.com/escaped/django-video-encoding/tree/0.1.0
