# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-09-12

### Added

* end-to-end test which uploads a real video through the example form and
  verifies the rendered page and the database state
* tests for `Format.update_progress()` and `Format.reset_progress()`

### Changed

* migrated packaging and dependency management from poetry to uv with the
  hatchling build backend
* replaced tox, black, isort, flake8, autoflake and the pre-commit hooks with
  ruff, mypy and pytest
* the test matrix now runs Python 3.10 - 3.14 against Django 5.2, 6.0 and 6.1

### Removed

* dropped support for Python `< 3.10`
* dropped support for Django `< 5.2`
* removed the cruft/cookiecutter auto-update workflow

### Fixed

* `Format.update_progress()` now rejects percentages outside of `0` - `100`
  instead of writing them to the database
* `Format.reset_progress()` now resets `progress` instead of setting a
  non-existent `percent` attribute
* the `ffprobe` error message now reports the `ffprobe` path

## [1.0.0] - 2021-01-03

### Added

* support for django-storages, @lifenautjoe & @bashu
* add signals for encoding

### Changed

* remove deprecation warnings

### Removed

* dropped support for python `2.7` and `3.5`
* dropped support for Django `<2.2`

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

[Unreleased]: https://github.com/escaped/django-video-encoding/compare/2.0.0...HEAD
[2.0.0]: https://github.com/escaped/django-video-encoding/compare/1.0.0...2.0.0
[1.0.0]: https://github.com/escaped/django-video-encoding/compare/0.4.0...1.0.0
[0.4.0]: https://github.com/escaped/django-video-encoding/compare/0.3.1...0.4.0
[0.3.1]: https://github.com/escaped/django-video-encoding/compare/0.3.0...0.3.1
[0.3.0]: https://github.com/escaped/django-video-encoding/compare/0.3.0...0.2.0
[0.2.0]: https://github.com/escaped/django-video-encoding/compare/0.10...0.2.0
[0.1.0]: https://github.com/escaped/django-video-encoding/tree/0.1.0
