import nextcord
from rx.subject import Subject


class RxBot(nextcord.Client):
    messages = Subject()
    edited_messages = Subject()
    deleted_messages = Subject()

    async def on_message(self, message):
        self.messages.on_next(message)

    async def on_message_delete(self, message):
        self.deleted_messages.on_next(message)
    
    async def on_message_edit(self, before, after):
        self.edited_messages.on_next((before, after))
    
    reactions = Subject()
    removed_reactions = Subject()
    cleared_reactions = Subject()
    cleared_emoji_reactions = Subject()

    async def on_reaction_add(self, reaction, user):
        self.reactions.on_next((reaction, user))
    
    async def on_reaction_remove(self, reaction, user):
        self.removed_reactions.on_next((reaction, user))
    
    async def on_reaction_clear(self, reaction, user):
        self.cleared_reactions.on_next((reaction, user))
    
    async def on_reaction_clear_emoji(self, reaction):
        self.cleared_emoji_reactions.on_next(reaction)
