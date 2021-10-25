import asyncio
import inspect
from collections import OrderedDict
from typing import (Any, Callable, Coroutine, Mapping, NoReturn, Optional,
                    OrderedDict, Union)

import nextcord
from nextcord.ext import commands
from nextcord.permissions import Permissions

from .constants import DEFAULT_TIMEOUT, EmojiType, log
from .exceptions import (CannotAddReactions, CannotEmbedLinks,
                         CannotReadMessageHistory, CannotSendMessages,
                         MenuError)
from .utils import Position, _cast_emoji


class Button:
    """Represents a reaction-style button for the :class:`Menu`.

    There are two ways to create this, the first being through explicitly
    creating this class and the second being through the decorator interface,
    :func:`button`.

    The action must have both a ``self`` and a ``payload`` parameter
    of type :class:`nextcord.RawReactionActionEvent`.

    Attributes
    ------------
    emoji: :class:`nextcord.PartialEmoji`
        The emoji to use as the button. Note that passing a string will
        transform it into a :class:`nextcord.PartialEmoji`.
    action
        A coroutine that is called when the button is pressed.
    skip_if: Optional[Callable[[:class:`Menu`], :class:`bool`]]
        A callable that detects whether it should be skipped.
        A skipped button does not show up in the reaction list
        and will not be processed.
    position: :class:`Position`
        The position the button should have in the initial order.
        Note that since nextcord does not actually maintain reaction
        order, this is a best effort attempt to have an order until
        the user restarts their client. Defaults to ``Position(0)``.
    lock: :class:`bool`
        Whether the button should lock all other buttons from being processed
        until this button is done. Defaults to ``True``.
    """
    __slots__ = ('emoji', '_action', '_skip_if', 'position', 'lock')

    def __init__(self, emoji: nextcord.PartialEmoji, action: Coroutine, *, skip_if: Optional[Callable[["Menu"], bool]] = None,
                 position: Optional[Position] = None, lock: Optional[bool] = True):

        self.emoji = _cast_emoji(emoji)
        self.action = action
        self.skip_if = skip_if
        self.position = position or Position(0)
        self.lock = lock

    @property
    def skip_if(self) -> Optional[Callable[["Menu"], bool]]:
        return self._skip_if

    @skip_if.setter
    def skip_if(self, value: Optional[Callable[["Menu"], bool]]):
        if value is None:
            self._skip_if = lambda _: False
            return

        try:
            menu_self = value.__self__
        except AttributeError:
            self._skip_if = value
        else:
            # Unfurl the method to not be bound
            if not isinstance(menu_self, Menu):
                raise TypeError(
                    'skip_if bound method must be from Menu not %r' % menu_self)

            self._skip_if = value.__func__

    @property
    def action(self) -> Coroutine:
        return self._action

    @action.setter
    def action(self, value: Coroutine):
        try:
            menu_self = value.__self__
        except AttributeError:
            pass
        else:
            # Unfurl the method to not be bound
            if not isinstance(menu_self, Menu):
                raise TypeError(
                    'action bound method must be from Menu not %r' % menu_self)

            value = value.__func__

        if not inspect.iscoroutinefunction(value):
            raise TypeError('action must be a coroutine not %r' % value)

        self._action = value

    def __call__(self, menu: "Menu", payload: nextcord.RawReactionActionEvent):
        if self.skip_if(menu):
            return
        return self._action(menu, payload)

    def __str__(self) -> str:
        return str(self.emoji)

    def is_valid(self, menu) -> bool:
        return not self.skip_if(menu)


def button(emoji: EmojiType, **kwargs):
    """Denotes a method to be button for the :class:`Menu`.

    The methods being wrapped must have both a ``self`` and a ``payload``
    parameter of type :class:`nextcord.RawReactionActionEvent`.

    The keyword arguments are forwarded to the :class:`Button` constructor.

    Example
    ---------

    .. code-block:: python3

        class MyMenu(Menu):
            async def send_initial_message(self, ctx, channel):
                return await channel.send(f'Hello {ctx.author}')

            @button('\\N{THUMBS UP SIGN}')
            async def on_thumbs_up(self, payload):
                await self.message.edit(content=f'Thanks {self.ctx.author}!')

            @button('\\N{THUMBS DOWN SIGN}')
            async def on_thumbs_down(self, payload):
                await self.message.edit(content=f"That's not nice {self.ctx.author}...")

    Parameters
    ------------
    emoji: Union[:class:`str`, :class:`nextcord.PartialEmoji`]
        The emoji to use for the button.
    """
    def decorator(func: Callable) -> Callable:
        func.__menu_button__ = _cast_emoji(emoji)
        func.__menu_button_kwargs__ = kwargs
        return func
    return decorator


class _MenuMeta(type):
    # noinspection PyMethodParameters
    @classmethod
    def __prepare__(cls, name, bases, **kwargs) -> OrderedDict:
        # This is needed to maintain member order for the buttons
        return OrderedDict()

    # noinspection PyMethodParameters
    def __new__(cls, name, bases, attrs, **kwargs) -> "_MenuMeta":
        buttons = []
        new_cls = super().__new__(cls, name, bases, attrs)

        inherit_buttons = kwargs.pop('inherit_buttons', True)
        if inherit_buttons:
            # walk MRO to get all buttons even in subclasses
            for base in reversed(new_cls.__mro__):
                for elem, value in base.__dict__.items():
                    try:
                        value.__menu_button__
                    except AttributeError:
                        continue
                    else:
                        buttons.append(value)
        else:
            for elem, value in attrs.items():
                try:
                    value.__menu_button__
                except AttributeError:
                    continue
                else:
                    buttons.append(value)

        new_cls.__inherit_buttons__ = inherit_buttons
        new_cls.__menu_buttons__ = buttons
        return new_cls

    def get_buttons(cls) -> OrderedDict:
        buttons = OrderedDict()
        for func in cls.__menu_buttons__:
            emoji = func.__menu_button__
            buttons[emoji] = Button(emoji, func, **func.__menu_button_kwargs__)
        return buttons


class Menu(metaclass=_MenuMeta):
    r"""An interface that allows handling menus by using reactions as buttons.

    Buttons should be marked with the :func:`button` decorator. Please note that
    this expects the methods to have a single parameter, the ``payload``. This
    ``payload`` is of type :class:`nextcord.RawReactionActionEvent`.

    Attributes
    ------------
    timeout: :class:`float`
        The timeout to wait between button inputs.
    delete_message_after: :class:`bool`
        Whether to delete the message after the menu interaction is done.
    clear_reactions_after: :class:`bool`
        Whether to clear reactions after the menu interaction is done.
        Note that :attr:`delete_message_after` takes priority over this attribute.
        If the bot does not have permissions to clear the reactions then it will
        delete the reactions one by one.
    check_embeds: :class:`bool`
        Whether to verify embed permissions as well.
    ctx: Optional[:class:`commands.Context`]
        The context that started this pagination session or ``None`` if it hasn't
        been started yet.
    bot: Optional[:class:`commands.Bot`]
        The bot that is running this pagination session or ``None`` if it hasn't
        been started yet.
    message: Optional[:class:`nextcord.Message`]
        The message that has been sent for handling the menu. This is the returned
        message of :meth:`send_initial_message`. You can set it in order to avoid
        calling :meth:`send_initial_message`\, if for example you have a pre-existing
        message you want to attach a menu to.
    """

    def __init__(self, *, timeout: float = DEFAULT_TIMEOUT, delete_message_after: bool = False,
                 clear_reactions_after: bool = False, check_embeds: bool = False, message: Optional[nextcord.Message] = None):

        self.timeout = timeout
        self.delete_message_after = delete_message_after
        self.clear_reactions_after = clear_reactions_after
        self.check_embeds = check_embeds
        self._can_remove_reactions = False
        self.__tasks = []
        self._running = True
        self.message = message
        self.ctx = None
        self.bot = None
        self._author_id = None
        self._buttons = self.__class__.get_buttons()
        self._lock = asyncio.Lock()
        self._event = asyncio.Event()

    @nextcord.utils.cached_property
    def buttons(self) -> Mapping[str, Button]:
        """Retrieves the buttons that are to be used for this menu session.

        Skipped buttons are not in the resulting dictionary.

        Returns
        ---------
        Mapping[:class:`str`, :class:`Button`]
            A mapping of button emoji to the actual button class.
        """
        buttons = sorted(self._buttons.values(), key=lambda b: b.position)
        return {
            button.emoji: button
            for button in buttons
            if button.is_valid(self)
        }

    def add_button(self, button: Button, *, react: bool = False):
        """|maybecoro|

        Adds a button to the list of buttons.

        If the menu has already been started then the button will
        not be added unless the ``react`` keyword-only argument is
        set to ``True``. Note that when this happens this function
        will need to be awaited.

        If a button with the same emoji is added then it is overridden.

        .. warning::

            If the menu has started and the reaction is added, the order
            property of the newly added button is ignored due to an API
            limitation with nextcord and the fact that reaction ordering
            is not guaranteed.

        Parameters
        ------------
        button: :class:`Button`
            The button to add.
        react: :class:`bool`
            Whether to add a reaction if the menu has been started.
            Note this turns the method into a coroutine.

        Raises
        ---------
        MenuError
            Tried to use ``react`` when the menu had not been started.
        nextcord.HTTPException
            Adding the reaction failed.
        """

        self._buttons[button.emoji] = button

        if react:
            if self.__tasks:
                async def wrapped():
                    # Add the reaction
                    try:
                        await self.message.add_reaction(button.emoji)
                    except nextcord.HTTPException:
                        raise
                    else:
                        # Update the cache to have the value
                        self.buttons[button.emoji] = button

                return wrapped()

            async def dummy():
                raise MenuError('Menu has not been started yet')
            return dummy()

    def remove_button(self, emoji: Union[Button, str], *, react: bool = False) -> Union[Coroutine[Any, Any, None], NoReturn]:
        """|maybecoro|

        Removes a button from the list of buttons.

        This operates similar to :meth:`add_button`.

        Parameters
        ------------
        emoji: Union[:class:`Button`, :class:`str`]
            The emoji or the button to remove.
        react: :class:`bool`
            Whether to remove the reaction if the menu has been started.
            Note this turns the method into a coroutine.

        Raises
        ---------
        MenuError
            Tried to use ``react`` when the menu had not been started.
        nextcord.HTTPException
            Removing the reaction failed.
        """

        if isinstance(emoji, Button):
            emoji = emoji.emoji
        else:
            emoji = _cast_emoji(emoji)

        self._buttons.pop(emoji, None)

        if react:
            if self.__tasks:
                async def wrapped():
                    # Remove the reaction from being processable
                    # Removing it from the cache first makes it so the check
                    # doesn't get triggered.
                    self.buttons.pop(emoji, None)
                    await self.message.remove_reaction(emoji, self.__me)
                return wrapped()

            async def dummy():
                raise MenuError('Menu has not been started yet')
            return dummy()

    def clear_buttons(self, *, react: bool = False) -> Union[Coroutine[Any, Any, None], NoReturn]:
        """|maybecoro|

        Removes all buttons from the list of buttons.

        If the menu has already been started then the buttons will
        not be removed unless the ``react`` keyword-only argument is
        set to ``True``. Note that when this happens this function
        will need to be awaited.

        Parameters
        ------------
        react: :class:`bool`
            Whether to clear the reactions if the menu has been started.
            Note this turns the method into a coroutine.

        Raises
        ---------
        MenuError
            Tried to use ``react`` when the menu had not been started.
        nextcord.HTTPException
            Clearing the reactions failed.
        """

        self._buttons.clear()

        if react:
            if self.__tasks:
                return self.clear

            async def dummy():
                raise MenuError('Menu has not been started yet')

            return dummy()

    def should_add_reactions(self) -> bool:
        """:class:`bool`: Whether to add reactions to this menu session."""
        return len(self.buttons) > 0

    def should_add_buttons(self) -> bool:
        """:class:`bool`: Whether to add button components to this menu session."""
        return hasattr(self, 'children') and len(self.children) > 0

    def should_add_reactions_or_buttons(self) -> bool:
        """:class:`bool`: Whether to add reactions or buttons to this menu session."""
        return self.should_add_reactions() or self.should_add_buttons()

    def _verify_permissions(self, ctx: commands.Context, channel: nextcord.abc.Messageable, permissions: Permissions):
        if not permissions.send_messages:
            raise CannotSendMessages()

        if self.check_embeds and not permissions.embed_links:
            raise CannotEmbedLinks()

        self._can_remove_reactions = permissions.manage_messages
        if self.should_add_reactions():
            if not permissions.add_reactions:
                raise CannotAddReactions()
            if not permissions.read_message_history:
                raise CannotReadMessageHistory()

    def reaction_check(self, payload: nextcord.RawReactionActionEvent) -> bool:
        """The function that is used to check whether the payload should be processed.
        This is passed to :meth:`nextcord.ext.commands.Bot.wait_for <Bot.wait_for>`.

        There should be no reason to override this function for most users.

        Parameters
        ------------
        payload: :class:`nextcord.RawReactionActionEvent`
            The payload to check.

        Returns
        ---------
        :class:`bool`
            Whether the payload should be processed.
        """
        if payload.message_id != self.message.id:
            return False
        if payload.user_id not in {self.bot.owner_id, self._author_id, *self.bot.owner_ids}:
            return False

        return payload.emoji in self.buttons

    async def _internal_loop(self):
        try:
            self.__timed_out = False
            loop = self.bot.loop
            # Ensure the name exists for the cancellation handling
            tasks = []
            while self._running:
                tasks = [
                    asyncio.ensure_future(self.bot.wait_for(
                        'raw_reaction_add', check=self.reaction_check)),
                    asyncio.ensure_future(self.bot.wait_for(
                        'raw_reaction_remove', check=self.reaction_check))
                ]
                done, pending = await asyncio.wait(tasks, timeout=self.timeout, return_when=asyncio.FIRST_COMPLETED)
                for task in pending:
                    task.cancel()

                if len(done) == 0:
                    raise asyncio.TimeoutError()

                # Exception will propagate if e.g. cancelled or timed out
                payload = done.pop().result()
                loop.create_task(self.update(payload))

                # NOTE: Removing the reaction ourselves after it's been done when
                # mixed with the checks above is incredibly racy.
                # There is no guarantee when the MESSAGE_REACTION_REMOVE event will
                # be called, and chances are when it does happen it'll always be
                # after the remove_reaction HTTP call has returned back to the caller
                # which means that the stuff above will catch the reaction that we
                # just removed.

                # For the future sake of myself and to save myself the hours in the future
                # consider this my warning.

        except asyncio.TimeoutError:
            self.__timed_out = True
        finally:
            self._event.set()

            # Cancel any outstanding tasks (if any)
            for task in tasks:
                task.cancel()

            try:
                await self.finalize(self.__timed_out)
            except Exception:
                pass
            finally:
                self.__timed_out = False

            # Can't do any requests if the bot is closed
            if self.bot.is_closed():
                return

            if self.delete_message_after:
                await self.message.delete()
            elif getattr(self, "clear_buttons_after", self.clear_reactions_after):
                await self.clear()
            elif getattr(self, "disable_buttons_after", None):
                await self.disable()

    async def update(self, payload: nextcord.RawReactionActionEvent):
        """|coro|

        Updates the menu after an event has been received.

        Parameters
        -----------
        payload: :class:`nextcord.RawReactionActionEvent`
            The reaction event that triggered this update.
        """
        button = self.buttons[payload.emoji]
        if not self._running:
            return

        try:
            if button.lock:
                async with self._lock:
                    if self._running:
                        await button(self, payload)
            else:
                await button(self, payload)
        except Exception as exc:
            await self.on_menu_button_error(exc)

    async def on_menu_button_error(self, exc: Exception):
        """|coro|

        Handles reporting of errors while updating the menu from events.
        The default behaviour is to log the exception.

        This may be overriden by subclasses.

        Parameters
        ----------
        exc: :class:`Exception`
            The exception which was raised during a menu update.
        """
        # some users may wish to take other actions during or beyond logging
        # which would require awaiting, such as stopping an erroring menu.
        log.exception("Unhandled exception during menu update.", exc_info=exc)

    async def start(self, ctx: commands.Context, *, channel: Optional[nextcord.abc.Messageable] = None, wait: bool = False):
        """|coro|

        Starts the interactive menu session.

        Parameters
        -----------
        ctx: :class:`Context`
            The invocation context to use.
        channel: :class:`nextcord.abc.Messageable`
            The messageable to send the message to. If not given
            then it defaults to the channel in the context.
        wait: :class:`bool`
            Whether to wait until the menu is completed before
            returning back to the caller.

        Raises
        -------
        MenuError
            An error happened when verifying permissions.
        nextcord.HTTPException
            Adding a reaction failed.
        """

        # Clear the buttons cache and re-compute if possible.
        try:
            del self.buttons
        except AttributeError:
            pass

        self.bot = bot = ctx.bot
        self.ctx = ctx
        self._author_id = ctx.author.id
        channel = channel or ctx.channel
        me = channel.guild.me if hasattr(channel, 'guild') else ctx.bot.user
        permissions = channel.permissions_for(me)
        self.__me = nextcord.Object(id=me.id)
        self._verify_permissions(ctx, channel, permissions)
        self._event.clear()
        msg = self.message
        if msg is None:
            self.message = msg = await self.send_initial_message(ctx, channel)

        if self.should_add_reactions_or_buttons():
            # Start the task first so we can listen to reactions before doing anything
            for task in self.__tasks:
                task.cancel()
            self.__tasks.clear()

            self._running = True
            self.__tasks.append(bot.loop.create_task(self._internal_loop()))

            async def add_reactions_task():
                for emoji in self.buttons:
                    await msg.add_reaction(emoji)
            self.__tasks.append(bot.loop.create_task(add_reactions_task()))

            if wait:
                await self._event.wait()

    async def finalize(self, timed_out: bool):
        """|coro|

        A coroutine that is called when the menu loop has completed
        its run. This is useful if some asynchronous clean-up is
        required after the fact.

        Parameters
        --------------
        timed_out: :class:`bool`
            Whether the menu completed due to timing out.
        """
        pass

    async def send_initial_message(self, ctx: commands.Context, channel: nextcord.abc.Messageable) -> nextcord.Message:
        """|coro|

        Sends the initial message for the menu session.

        This is internally assigned to the :attr:`message` attribute.

        Subclasses must implement this if they don't set the
        :attr:`message` attribute themselves before starting the
        menu via :meth:`start`.

        Parameters
        ------------
        ctx: :class:`Context`
            The invocation context to use.
        channel: :class:`nextcord.abc.Messageable`
            The messageable to send the message to.

        Returns
        --------
        :class:`nextcord.Message`
            The message that has been sent.
        """
        raise NotImplementedError

    async def clear(self):
        """|coro|

        Removes all reaction buttons in the menu.
        """
        # Wrap it in another block anyway just to ensure
        # nothing leaks out during clean-up
        try:
            # A fast path if we have permissions
            if self._can_remove_reactions:
                try:
                    del self.buttons
                except AttributeError:
                    pass
                finally:
                    await self.message.clear_reactions()
                return

            # Remove the cache (the next call will have the updated buttons)
            reactions = list(self.buttons.keys())
            try:
                del self.buttons
            except AttributeError:
                pass

            for reaction in reactions:
                try:
                    await self.message.remove_reaction(reaction, self.__me)
                except nextcord.HTTPException:
                    continue
        except Exception:
            pass

    def stop(self):
        """Stops the internal loop."""
        self._running = False
        for task in self.__tasks:
            task.cancel()
        self.__tasks.clear()


class ButtonMenu(Menu, nextcord.ui.View):
    r"""An interface that allows handling menus by using button interaction components.

    Buttons should be marked with the :func:`nextcord.ui.button` decorator. Please note that
    this expects the methods to have two parameters, the ``button`` and the ``interaction``.
    The ``button`` is of type :class:`nextcord.ui.Button`.
    The ``interaction`` is of type :class:`nextcord.Interaction`.

    Attributes
    ------------

    clear_buttons_after: :class:`bool`
        Whether to clear buttons after the menu interaction is done.
        Note that :attr:`delete_message_after` takes priority over this attribute.
    disable_buttons_after: :class:`bool`
        Whether to disable all buttons after the menu interaction is done.
        Note that :attr:`delete_message_after` and :attr:`clear_buttons_after` take priority over this attribute.
    """

    def __init__(self, timeout: float = DEFAULT_TIMEOUT, clear_buttons_after: bool = False,
                 disable_buttons_after: bool = False, *args, **kwargs):
        Menu.__init__(self, timeout=timeout, *args, **kwargs)
        nextcord.ui.View.__init__(self, timeout=timeout)
        self.clear_buttons_after = clear_buttons_after
        self.disable_buttons_after = disable_buttons_after

    async def _update_view(self):
        await self.message.edit(view=self)

    async def _set_all_disabled(self, disable: bool):
        """|coro|

        Enables or disable all :class:`nextcord.ui.Button` components in the menu.

        Parameters
        ------------
        disable: :class:`bool`
            Whether to disable or enable the buttons.
        """
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = disable
        await self._update_view()

    async def enable(self):
        """|coro|

        Enables all :class:`nextcord.ui.Button` components in the menu.
        """
        await self._set_all_disabled(False)

    async def disable(self):
        """|coro|

        Disables all :class:`nextcord.ui.Button` components in the menu.
        """
        await self._set_all_disabled(True)

    async def clear(self):
        """|coro|

        Removes all :class:`nextcord.ui.Button` components in the menu.
        """
        self.clear_items()
        await self._update_view()

    def stop(self):
        """Stops the internal loop and view interactions."""
        # stop the menu loop
        Menu.stop(self)
        # stop view interactions
        nextcord.ui.View.stop(self)
