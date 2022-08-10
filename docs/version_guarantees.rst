.. _version_guarantees:

Version Guarantees
==================

Nextcord does not follow semantic versioning exactly, the main difference is that breaking changes may also be made on minor version bumps (similar to Python's scheme).
The reason for this is the Discord API lacks guarantees on breaking changes per API version, so library breaking changes unfortunately have to be made to match.
Breaking changes that are not forced by Discord will be deprecated but not removed in a minor version (special cases apply, such as low impact changes).

However, any breaking changes will always be marked as such in the release notes/changelogs.

Summary of The Versioning Scheme
--------------------------------

The version scheme ``major.minor.micro`` used aims to follow these rules:

- ``major`` bumps usually contain large refactors/changes (most likely containing breaking changes).
- ``minor`` bumps contain new features, sometimes bug fixes, and **may contain breaking changes**.
- ``micro`` bumps only contain bug fixes, so no new features and no breaking changes.

.. note::

    Breaking changes are not applied on **privately documented functions and classes**.
    A function/class is not part of the public API if it is not listed in the documentation.
    Attributes and functions that start with an underscore are also not part of the public API.

.. note::

    The examples below are non-exhaustive.

Examples of Breaking Changes
----------------------------

- Changing the default parameter value to something else.
- Renaming a function without an alias to an old function.
- Adding or removing parameters to an event.

Examples of Non-Breaking Changes
--------------------------------

- Adding or removing private underscored attributes.
- Adding an element into the ``__slots__`` of a data class.
- Changing the behaviour of a function to fix a bug.
- Changes in the documentation.
- Modifying the internal HTTP handling.
- Upgrading the dependencies to a new version, major or otherwise.
