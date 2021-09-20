from typing import TYPE_CHECKING, Tuple, TypeVar, Type, Dict, Any, Union, Callable, Optional, List, Iterable, Coroutine
import nextcord
import inspect
import asyncio
import functools
from enum import IntEnum
from .utils import MISSING
from nextcord.interactions import Interaction

if TYPE_CHECKING:
    from .state import ConnectionState
    from aiohttp import ClientSession



def unwrap_function(function: Callable[..., Any]) -> Callable[..., Any]:
    partial = functools.partial
    while True:
        if hasattr(function, '__wrapped__'):
            function = function.__wrapped__
        elif isinstance(function, partial):
            function = function.func
        else:
            return function


def get_signature_parameters(function: Callable[..., Any], globalns: Dict[str, Any]) -> Dict[str, inspect.Parameter]:
    signature = inspect.signature(function)
    params = {}
    cache: Dict[str, Any] = {}
    eval_annotation = nextcord.utils.evaluate_annotation
    for name, parameter in signature.parameters.items():
        annotation = parameter.annotation
        if annotation is parameter.empty:
            params[name] = parameter
            continue
        if annotation is None:
            params[name] = parameter.replace(annotation=type(None))
            continue

        annotation = eval_annotation(annotation, globalns, globalns, cache)
        # if annotation is Greedy:
        #     raise TypeError('Unparameterized Greedy[...] is disallowed in signature.')

        params[name] = parameter.replace(annotation=annotation)

    return params


# class ApplicationCommand:
#     __slots__: Tuple[str, ...] = (
#         'id',
#         'application_id',
#         'name',
#         'description',
#         'version',
#         'default_permission',
#         'type',
#         'guild_id',
#     )
#
#     def __init__(self, data: dict, state: ConnectionState):
#         self._state: ConnectionState = state
#         self._session: ClientSession = state.http._HTTPClient__session
#         self._from_data(data)
#
#     def _from_data(self, data: dict):
#         self.id: int = int(data['id'])
#         self.application_id: int = int(data.get('application_id'))


class ApplicationCommandType(IntEnum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3


AppCmdType = ApplicationCommandType


class ApplicationCommandRequest:
    __original_kwargs: Dict[str, Any]
    # TODO: This is supposed to be the assembly for registering a command with Discord.

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.__original_kwargs__ = kwargs.copy()
        return self

    def __init__(self, callback: Coroutine, app_type: AppCmdType,
                 name: str = MISSING,
                 description: str = MISSING,
                 guild_ids: Union[int, Iterable] = MISSING, parent=MISSING):
        self._parent = parent  # TODO: Rewrite this all, this sucks.
        self._callback: Coroutine = callback
        # if app_type not in AppCmdType:
        if app_type not in (t for t in AppCmdType):
            raise TypeError('Unhandled Application Command Type given!')
        self.type = app_type
        name = name or callback.__name__
        if not isinstance(name, str):
            raise TypeError('Name of a command must be a string.')
        self.name = name
        self.description = description if description else " "
        if not guild_ids:
            self._guild_ids: Optional[List[int]] = list()
        elif isinstance(guild_ids, int):
            self._guild_ids = [guild_ids, ]
        else:
            try:
                self._guild_ids = list(guild_ids)
            except TypeError:
                raise TypeError("The guild_id of a Application Command Requests must be an int or list()-able.")

    @property
    def callback(self) -> Coroutine:
        return self._callback

    @property
    def payload(self) -> dict:
        ret = {"name": self.name, "type": self.type}
        if self.description:
            ret["description"] = self.description
        return ret

    @property
    def guild_ids(self) -> Optional[Tuple]:
        return tuple(self._guild_ids)


class ApplicationCommandResponse:
    def __init__(self, data: dict):
        self.id: int = int(data.get('id'))
        self.application_id: int = int(data.get('application_id'))
        self.name: str = data.get('name')
        self.description: str = data.get('description')
        self.version: int = int(data.get('version'))
        self.default_permission: bool = data.get('default_permission')
        self.type: int = int(data.get('type'))
        self.guild_id: int = int(guild_id) if (guild_id := data.get('guild_id')) else MISSING


class ApplicationCommand:
    def __init__(self, request: ApplicationCommandRequest, response: ApplicationCommandResponse):
        self.id: int = response.id
        self.application_id: int = response.application_id
        self.name: str = response.name
        self.description: str = response.description
        self.version: int = response.version
        self.default_permission: bool = response.default_permission
        self.type: int = response.type
        self.guild_id = response.guild_id
        self._parent = request._parent
        self.__original_kwargs__ = request.__original_kwargs__
        self._callback: Coroutine = request.callback

    async def invoke(self, interaction: Interaction):
        injected = hooked_wrapped_callback(self.callback)
        # await injected(interaction)
        if self._parent:
            await injected(self._parent, interaction)
        else:
            await injected(interaction)

    @property
    def callback(self) -> Coroutine:
        return self._callback


class SlashCommand(ApplicationCommand):
    # TODO: IDK what I'm doing with this.
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.__original_kwargs__ = kwargs.copy()
        return self

    def __init__(self, func, **kwargs):
        super().__init__(dict())
        self.name: str = kwargs.get('name')
        # self.id: int = 0
        pass


class UserCommand(ApplicationCommand):
    pass


class MessageCommand(ApplicationCommand):
    pass


def hooked_wrapped_callback(coro):
    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        try:
            ret = await coro(*args, **kwargs)
        except Exception as exc:
            # ctx.command_failed = True
            raise NotImplementedError(exc) from exc

        return ret
    return wrapped


# class SlashCommand:
#     __original_kwargs: Dict[str, Any]
#
#     def __new__(cls: Type[SlashCommandT], *args, **kwargs) -> SlashCommandT:
#         self = super().__new__(cls)
#         self.__original_kwargs__ = kwargs.copy()
#         return self
#
#     def __init__(self, func: Union[
#             Callable[Concatenate[CogT, ContextT, P], Coro[T]],
#             Callable[Concatenate[ContextT, P], Coro[T]],
#         ], **kwargs: Any):
#         if not asyncio.iscoroutinefunction(func):
#             raise TypeError('Callback must be a coroutine.')
#
#         name = kwargs.get('name') or func.__name__
#         if not isinstance(name, str):
#             raise TypeError('Name of a command must be a string.')
#         self.name: str = name
#         self.callback = func
#
#         self.description: Optional[str] = kwargs.get('description')
#
#         # TODO: Checks and Cooldowns. Also Aliases.
#
#         self.cog: Optional[CogT] = None
#         parent = kwargs.get('parent')
#         self.parent: Optional[GroupMixin] = parent if isinstance(parent, _BaseCommand) else None  # type: ignore
#
#     @property
#     def callback(self) -> Union[
#         Callable[Concatenate[CogT, Context, P], Coro[T]],
#         Callable[Concatenate[Context, P], Coro[T]],
#     ]:
#         return self._callback
#
#     @callback.setter
#     def callback(self, function: Union[
#         Callable[Concatenate[CogT, Context, P], Coro[T]],
#         Callable[Concatenate[Context, P], Coro[T]],
#     ]) -> None:
#         self._callback = function
#         unwrap = unwrap_function(function)
#         self.module = unwrap.__module__
#
#         try:
#             globalns = unwrap.__globals__
#         except AttributeError:
#             globalns = {}
#
#         self.params = get_signature_parameters(function, globalns)
#
#     @property
#     def json(self) -> dict:
#         ret = {}
#         ret['name'] = self.name
#         ret['description'] = self.description if self.description else ''
#         ret['type'] = 2
#
#         return ret


