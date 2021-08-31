from typing import Generic, TypeVar
from .user_input_error import UserInputError

ArgT = TypeVar('ArgT')
class BadArgument(UserInputError, Generic[ArgT]):
    """Exception raised when a parsing or conversion failure is encountered
    on an argument to pass into a command.

    This inherits from :exc:`UserInputError`
    """
    def __init__(self, message: str = None, argument: ArgT = None, *args):
        super().__init__(message, *args)
        self.argument = argument
