class MenuError(Exception):
    pass


class CannotEmbedLinks(MenuError):
    def __init__(self):
        super().__init__("Bot does not have embed links permission in this channel.")


class CannotSendMessages(MenuError):
    def __init__(self):
        super().__init__("Bot cannot send messages in this channel.")


class CannotAddReactions(MenuError):
    def __init__(self):
        super().__init__("Bot cannot add reactions in this channel.")


class CannotReadMessageHistory(MenuError):
    def __init__(self):
        super().__init__("Bot does not have Read Message History permissions in this channel.")
