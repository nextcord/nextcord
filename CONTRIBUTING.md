# Contributing to nextcord

First off, thanks for taking the time to contribute. It makes the library substantially better. :+1:

The following is a set of guidelines for contributing to the repository. These are guidelines, not hard rules.

## This is too much to read! I want to ask a question

Generally asking questions are better suited in our resources below.

- [The official support server](https://discord.gg/ZebatWssCB)
- [The FAQ in the documentation](https://nextcord.readthedocs.io/en/latest/faq.html)
- [StackOverflow's `nextcord` tag](https://stackoverflow.com/questions/tagged/nextcord)
- [The discussions page](https://github.com/nextcord/nextcord/discussions)

Please try your best not to ask questions in our issue tracker. Most of them don't belong there unless they provide value to a larger audience.

## Good Bug Reports

Please be aware of the following things when filing bug reports.

1. Don't open duplicate issues. Please search your issue to see if it has been asked already. Duplicate issues will be closed.
2. When filing a bug about exceptions, please include the *complete* traceback. Without the complete traceback the issue might be **unsolvable** and you will be asked to provide more information.
3. Make sure to provide enough information to make the issue workable. The issue template will generally walk you through the process but they are enumerated here as well:
    - A **summary** of your bug report. This is generally a quick sentence or two to describe the issue in human terms.
    - Guidance on **how to reproduce the issue**. Ideally, this should have a small code sample that allows us to run and see the issue for ourselves to debug. **Please make sure that the token is not displayed**. If you cannot provide a code snippet, then let us know what the steps were, how often it happens, etc.
    - Tell us **what you expected to happen**, that way we can meet that expectation.
    - Tell us **what actually happens**. What ends up happening in reality? It's not helpful to say "it fails" or "it doesn't work". Say *how* it failed, do you get an exception? Does it hang? How are the expectations different from reality?
    - Tell us **information about your environment**. What version of nextcord are you using? How was it installed? What operating system are you running on? These are valuable questions and information that we use.

If the bug report is missing this information then it'll take us longer to fix the issue. We will probably ask for clarification, and barring that if no response was given then the issue will be closed.

## Submitting a Pull Request

Submitting a pull request is fairly simple, just make sure it focuses on a single aspect and doesn't manage to have scope creep and it's probably good to go. It would be incredibly lovely if the style is consistent to that found in the project.

Please use the following to get your contributions up to spec:

- [Dependencies](#installing-development-dependencies-locally)
- [Code Style](#code-style)
- [Type Annotations](#type-annotations)
- [Commits](#commits)
- [Documentation](#documentation)
- [Gateway Events](#gateway-events)

## Installing Development Dependencies Locally

To install development dependencies locally, you can use the following command, prefixed with `py -m` or `python -m` if necessary.

```sh
pip install -r requirements-dev.txt
```

## Code Style

We use [Black](https://github.com/psf/black) for code formatting, [Isort](https://github.com/pycqa/isort) for import sorting, [Slotscheck](https://github.com/ariebovenberg/slotscheck) and several other [pre-commit hooks](https://github.com/pre-commit/pre-commit-hooks) for linting.

To run all of these but `slotscheck`, you can simply run `task lint` in the root of the project. To run `slotscheck`, you can run `task slotscheck`.

If you would like these to run automatically, you can use `task precommit` to install pre-commit hooks. This will run all of the above on every commit.

## Type Annotations

Nextcord uses [Pyright](https://github.com/microsoft/pyright) for type checking. To use it, run `task pyright` in the root directory of the project, or `python -m task pyright` (`py -m` etc) if that does not work.

If type annotations are new to you, here is a [guide](https://decorator-factory.github.io/typing-tips/) to help you with it.

## Commits

Nextcord follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) style. This means that your commit messages and PR titles should be formatted in a specific way. This is to help us generate changelogs and release notes, whilst also helping us review your pull requests as we can see what each commit does.

Your commit messages should be in the present (imperative, 2nd person) tense, such as `Add`, not `Added`.

More specifically, we use the [Angular Types List](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#type) for commit types, along with a few extra. This means that your commit messages should be formatted like this:

```text
<type>([scope]): <subject>
[BLANK LINE]
[body]
[BLANK LINE]
[footer]
```

> **Note**
> The type and subject are mandatory.

Examples include:

```text
feat: add support for forum channels
```

```text
refactor(commands)!: change name of Bot to CommandBot

This is a breaking change because the name of the class has changed.
```

```text
fix(app-cmds): resolve issue with negative numbers not converting to integers

Co-Authored-By: Some Person <email@example.com>
```

### Type

`<type>` is one of the following:

- **build**: Changes that affect the build system or external dependencies
- **chore**: Other miscellaneous changes which do not affect users
- **ci**: Changes to our CI configuration files and scripts such as GitHub Actions
- **docs**: Documentation only changes
- **feat**: A new feature
- **fix**: A bug fix
- **perf**: A code change that improves performance
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- **test**: Adding missing tests or correcting existing tests
- **typing**: Changes that affect type annotations

### Scope

`[scope]` is the name of the module affected (as perceived by the person reading the changelog generated from commit messages). Scope is not required when the change affects multiple modules. Some examples are:

- `application_command.py` - `app-cmds` is the scope
- `auto_moderation.py` - `automod` is the scope
- `ext/commands/*` - `commands` is the scope
- `ui/` - `ui` is the scope

### Subject

The subject should be a short summary of the commit, the body can be used for more info, so do not cram so much into the subject. Ideally this should be 50 characters or less, but it is not a hard limit, 72 characters is fine if necessary, such as if a long method name is described.

### Body

The body is an optional long description about the commit, this can be used to explain the motivation for the change, and can be used to give more context about the change. It is not required, but it is recommended.

### Footer

The footer contains optional metadata about the commit. These are sometimes added by git or similar tools, and examples include `Co-authored-by`, `Signed-off-by`, `Fixes`.

## Documentation

Nextcord uses [Sphinx](https://www.sphinx-doc.org/en/master/) for documentation compilation. Specifically, we use the numpy format ([Reference](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard), [Examples](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html)).

### Building the Docs

To install the documentation dependencies, run `pip install -r docs/requirements.txt` in the root of the project.

To build the docs that will autocompile on file changes, run `task docs` then open `http://localhost:8069` in your browser.

### Versioning

> **Note**
> If you are unsure about any of this, we can help you via a review or Discord. It just speeds the process up by doing it beforehand.

We use [`.. versionadded::`](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionadded) and [`.. versionchanged::`](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionchanged) to denote when a feature was added or changed. These should be used in the docstring of the feature, below the summary.

These should not be used in methods in a new class, since the whole class is new.

The current in-development version can be found in `nextcord/__init__.py` at `__version__`.

#### Versioning Example

```python
class Client:
    """A client to interface with Discord.

    This client is very barebones.

    .. versionadded:: 2.0
    """

    def start(self, token: Optional[str] = None) -> None:
        """Start the client.

        .. versionadded:: 2.1

        .. versionchanged:: 2.2

            Added the `token` parameter.
        """
```

### Operations

We use [`.. container:: operations`](https://docutils.sourceforge.io/docs/ref/rst/directives.html#container) to describe special methods. This should be below the summary and above the attributes.

#### Operations Example

```python
class Guild(Hashable):
    """Represents a Discord guild.

    This is referred to as a "server" in the official Discord UI.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.
```

### Class, Attribute, Method, ... Links

We use [Roles](https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#roles) to link to other parts of documentation.

`typing` is not linked to shorten the docstrings, and are simply described like this: ``List[:class:`str`]``.

#### Links Example

```python
    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: Returns all the members with this role."""

        ,,,
```

### Coroutines

Coroutines are denoted with `|coro|` on the first line, and `|maybecoro|` if it can be a coroutine or not (overriden methods).

#### Coroutines Example

```python
async def sleep_until(...) -> Optional[T]:
    """|coro|

    Sleep until a specified time.

    ...
    """

    ...
```

## Typed Payloads

We use [TypedDict](https://docs.python.org/3/library/typing.html#typing.TypedDict) to type payloads. This is a dictionary with a specific set of keys, where the values have a specific type.

These are stored in `nextcord/types`, where the file name relates to the `nextcord/` filename.

These are Python representations of Discord payloads found in the [Discord API docs](https://discord.dev). [`typing_extensions.NotRequired`](https://peps.python.org/pep-0655/) is used for keys which are omitted, represented by `name?` in the Discord docs. [`typing.Optional`](https://docs.python.org/3/library/typing.html#typing.Optional) is used for keys which may be `null` (`None`), represented by `?type` in the Discord docs.

`nextcord.types.snowflake.Snowflake` is used for Snowflakes, which are Discord IDs.

### Typed Payloads Example

This is an example of the [Auto Moderation Action Execution Payload](https://discord.com/developers/docs/topics/gateway-events#auto-moderation-action-execution-auto-moderation-action-execution-event-fields).

```python
class AutoModerationActionExecution(TypedDict):
    guild_id: Snowflake
    action: AutoModerationAction
    rule_id: Snowflake
    rule_trigger_type: AutoModerationTriggerType
    user_id: Snowflake
    matched_keyword: Optional[str]
    channel_id: NotRequired[Snowflake]
    message_id: NotRequired[Snowflake]
    alert_system_message_id: NotRequired[Snowflake]
    content: NotRequired[str]
    matched_content: NotRequired[Optional[str]]
```

## Gateway Events

[Gateway events](https://discord.com/developers/docs/topics/gateway-events#receive-events) are stored in `nextcord/state.py` as async methods of `ConnectionState`. These are named `parse_{event}` where event is the lowercase name of Discord's event name.

Client events are dispatched via `ConnectionState.dispatch`, which is a wrapper around `Client.dispatch`. The event name is the end-user event name, but without the `on_` prefix.

Documentation for events are in `api.rst`, below `.. _discord-api-events:`/`Event Reference`.

## Gateway Events Example

Here is a simple example of [`AUTO_MODERATION_RULE_CREATE`](https://discord.com/developers/docs/topics/gateway-events#auto-moderation-rule-create):

```python
def parse_auto_moderation_rule_create(self, data) -> None:
    self.dispatch(
        "auto_moderation_rule_create",
        AutoModerationRule(data=data, state=self),
    )
```
