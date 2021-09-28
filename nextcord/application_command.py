from __future__ import annotations
from typing import TYPE_CHECKING, Union, Optional, List
from enum import IntEnum
from .enums import try_enum
from .mixins import Hashable
from . import utils

if TYPE_CHECKING:
    from .state import ConnectionState
    from .guild import Guild


class ApplicationCommandRequest:
    pass

class ApplicationCommandResponse:
    pass


# def unwrap_function(function: Callable[..., Any]) -> Callable[..., Any]:
#     partial = functools.partial
#     while True:
#         if hasattr(function, '__wrapped__'):
#             function = function.__wrapped__
#         elif isinstance(function, partial):
#             function = function.func
#         else:
#             return function
#
#
# def get_signature_parameters(function: Callable[..., Any], globalns: Dict[str, Any]) -> Dict[str, inspect.Parameter]:
#     signature = inspect.signature(function)
#     params = {}
#     cache: Dict[str, Any] = {}
#     eval_annotation = nextcord.utils.evaluate_annotation
#     for name, parameter in signature.parameters.items():
#         annotation = parameter.annotation
#         if annotation is parameter.empty:
#             params[name] = parameter
#             continue
#         if annotation is None:
#             params[name] = parameter.replace(annotation=type(None))
#             continue
#
#         annotation = eval_annotation(annotation, globalns, globalns, cache)
#         # if annotation is Greedy:
#         #     raise TypeError('Unparameterized Greedy[...] is disallowed in signature.')
#
#         params[name] = parameter.replace(annotation=annotation)
#
#     return params
#
#
# # class ApplicationCommand:
# #     __slots__: Tuple[str, ...] = (
# #         'id',
# #         'application_id',
# #         'name',
# #         'description',
# #         'version',
# #         'default_permission',
# #         'type',
# #         'guild_id',
# #     )
# #
# #     def __init__(self, data: dict, state: ConnectionState):
# #         self._state: ConnectionState = state
# #         self._session: ClientSession = state.http._HTTPClient__session
# #         self._from_data(data)
# #
# #     def _from_data(self, data: dict):
# #         self.id: int = int(data['id'])
# #         self.application_id: int = int(data.get('application_id'))


class ApplicationCommandType(IntEnum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3


# AppCmdType = ApplicationCommandType

#
# class ApplicationCommandRequest:
#     def __init__(self):
#         pass
    # def __init__(self, callback: Coroutine, app_type: AppCmdType,
    #              name: str = MISSING,
    #              description: str = MISSING,
    #              guild_ids: Union[int, Iterable] = MISSING, parent=MISSING):
    #     self._parent = parent  # TODO: Rewrite this all, this sucks.
    #     self._callback: Coroutine = callback
    #     # if app_type not in AppCmdType:
    #     if app_type not in (t for t in AppCmdType):
    #         raise TypeError('Unhandled Application Command Type given!')
    #     self.type = app_type
    #     name = name or callback.__name__
    #     if not isinstance(name, str):
    #         raise TypeError('Name of a command must be a string.')
    #     self.name = name
    #     self.description = description if description else " "
    #     if not guild_ids:
    #         self._guild_ids: Optional[List[int]] = list()
    #     elif isinstance(guild_ids, int):
    #         self._guild_ids = [guild_ids, ]
    #     else:
    #         try:
    #             self._guild_ids = list(guild_ids)
    #         except TypeError:
    #             raise TypeError("The guild_id of a Application Command Requests must be an int or list()-able.")
    #
    # @property
    # def callback(self) -> Coroutine:
    #     return self._callback
    #
    # @property
    # def payload(self) -> dict:
    #     ret = {"name": self.name, "type": self.type}
    #     if self.description:
    #         ret["description"] = self.description
    #     return ret
    #
    # @property
    # def guild_ids(self) -> Optional[Tuple]:
    #     return tuple(self._guild_ids)
#
#
# class ApplicationCommandResponse:


class ApplicationCommandOptionType(IntEnum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10  # A double, AKA floating point, AKA decimal.


class ApplicationCommandOptionChoice:
    def __init__(self, payload: Optional[dict] = None):
        if not payload:
            payload = dict()
        self.name: str = payload.get('name')
        self.value: Union[str, int, float] = payload.get('value')

    def from_data(self, data: dict):
        self.__init__(data)


class ApplicationCommandOption:
    def __init__(self, payload: Optional[dict] = None):
        if payload:
            self._from_data(payload)

    def _from_data(self, data: dict):
        # self.type = try_enum(ApplicationCommandOptionType, data['type'])
        self.type = ApplicationCommandOptionType(int(data["type"]))
        self.name: str = data['name']
        self.description: str = data['description']
        self.required: Optional[bool] = data.get('required')
        self.choices: List[ApplicationCommandOptionChoice] = self.create_all_choices(data.get('choices', list()))
        self.options: List[ApplicationCommandOption] = self.create_all_options(data.get('options', list()))

    @staticmethod
    def create_all_choices(data: List[dict]) -> List[ApplicationCommandOptionChoice]:
        return [ApplicationCommandOptionChoice(raw_choice) for raw_choice in data]

    @staticmethod
    def create_all_options(data: List[dict]) -> List[ApplicationCommandOption]:
        return [ApplicationCommandOption(raw_option) for raw_option in data]


# class ApplicationCommandInteractionDataOption:
#     def __init__(self, *args, **kwargs):
#         raise NotImplementedError
#
#     def _from_data(self, data: dict):
#         self.name: str = None
#         self.type: int = None
#         self.value: Optional[int] = None
#         self.options: Optional[dict] = None


class ApplicationCommand(Hashable):

    def __init__(self, state: ConnectionState, payload: dict):
        self._state: ConnectionState = state
        self._from_data(payload)

    def _from_data(self, data: dict):
        self.id: int = int(data['id'])
        self.type: ApplicationCommandType = ApplicationCommandType(int(data['type']))
        self.application_id: int = int(data['application_id'])
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.name: str = data['name']
        self.description: str = data['description']
        self.options = ApplicationCommandOption.create_all_options(data.get('options', list()))
        self.default_permission: Optional[bool] = data.get('default_permission', True)

    @property
    def guild(self) -> Optional[Guild]:
        return self._state._get_guild(self.guild_id)

    async def edit(self, *args, **kwargs):
        raise NotImplementedError

    async def delete(self):
        if self.guild_id:
            await self._state.http.delete_guild_command(self.application_id, self.guild_id, self.id)
        else:
            await self._state.http.delete_global_command(self.application_id, self.id)

    async def fetch_permissions(self):
        raise NotImplementedError

    async def edit_permissions(self):
        raise NotImplementedError


#     def __init__(self, data: dict):
#         self.id: int = int(data.get('id'))
#         self.application_id: int = int(data.get('application_id'))
#         self.name: str = data.get('name')
#         self.description: str = data.get('description')
#         self.version: int = int(data.get('version'))
#         self.default_permission: bool = data.get('default_permission')
#         self.type: int = int(data.get('type'))
#         self.guild_id: int = int(guild_id) if (guild_id := data.get('guild_id')) else MISSING
#
#
# class ApplicationCommand:
#     def __init__(self, request: ApplicationCommandRequest, response: ApplicationCommandResponse):
#         self.id: int = response.id
#         self.application_id: int = response.application_id
#         self.name: str = response.name
#         self.description: str = response.description
#         self.version: int = response.version
#         self.default_permission: bool = response.default_permission
#         self.type: int = response.type
#         self.guild_id = response.guild_id
#         self._parent = request._parent
#         self.__original_kwargs__ = request.__original_kwargs__
#         self._callback: Coroutine = request.callback
#
#     async def invoke(self, interaction: Interaction):
#         injected = hooked_wrapped_callback(self.callback)
#         # await injected(interaction)
#         if self._parent:
#             await injected(self._parent, interaction)
#         else:
#             await injected(interaction)
#
#     @property
#     def callback(self) -> Coroutine:
#         return self._callback
#
#
# class SlashCommand(ApplicationCommand):
#     # TODO: IDK what I'm doing with this.
#     def __new__(cls, *args, **kwargs):
#         self = super().__new__(cls)
#         self.__original_kwargs__ = kwargs.copy()
#         return self
#
#     def __init__(self, func, **kwargs):
#         super().__init__(dict())
#         self.name: str = kwargs.get('name')
#         # self.id: int = 0
#         pass
#
#
# class UserCommand(ApplicationCommand):
#     pass
#
#
# class MessageCommand(ApplicationCommand):
#     pass
#
#
# def hooked_wrapped_callback(coro):
#     @functools.wraps(coro)
#     async def wrapped(*args, **kwargs):
#         try:
#             ret = await coro(*args, **kwargs)
#         except Exception as exc:
#             # ctx.command_failed = True
#             raise NotImplementedError(exc) from exc
#
#         return ret
#     return wrapped


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


