from __future__ import annotations
from typing import Awaitable, Callable, TYPE_CHECKING
from discord.ui import LayoutView, Container, TextDisplay, ActionRow, MediaGallery, button, Button
from discord import  Member, Message, MediaGalleryItem
from discord import Interaction
import discord
import re
from bot.logging import get_logger

logger = get_logger(name="views")

if TYPE_CHECKING:
    from bot.database.models import User

class DeleteQuoteButton(discord.ui.DynamicItem[discord.ui.Button], template=r"delete_quote_(?P<author>\d+)_(?P<caller>\d+)"):
    def __init__(self, author_id: int, caller_id: int):
        super().__init__(
            discord.ui.Button(
                label="Remove my quote",
                style=discord.ButtonStyle.danger,
                custom_id=f"delete_quote_{author_id}_{caller_id}"
            )
        )
        self.author_id = author_id
        self.caller_id = caller_id

    @classmethod
    async def from_custom_id(cls, interaction: Interaction, item: discord.ui.Button, match: re.Match): #type: ignore
        return cls(int(match["author"]), int(match["caller"]))

    async def callback(self, interaction: Interaction):
        allowed = {self.author_id, self.caller_id}

        if interaction.user.id not in allowed:
            await interaction.response.send_message(
                "You can't remove this quote.", ephemeral=True 
            )
            return

        try:
            if interaction.message:
                await interaction.message.delete()
                await interaction.response.send_message(
                    content="The quote message has been removed successfully",
                    delete_after=10,
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"error: {e}")


class QuoteButtons(ActionRow):
    def __init__(self, author_id: int, caller_id: int) -> None:
        super().__init__()
        self.add_item(DeleteQuoteButton(author_id, caller_id))



class QuoteView(LayoutView):
    def __init__(self, *, timeout: float | None = None,
                 message: Message, file_q: discord.File,
                 author_id: int, caller_id: int) -> None:
        super().__init__(timeout=timeout)
        self.message = message
        self.buttons = QuoteButtons(author_id, caller_id)
        self.text_display = TextDisplay(
            content=f"[Jump to the original message]({message.jump_url})", id=1
        )
        self.m_item = MediaGalleryItem(media=file_q)
        self.m_galley = MediaGallery(self.m_item, id=3)
        self.add_item(self.text_display)
        self.add_item(self.m_galley)
        self.add_item(self.buttons)




class SuccessUserDelete(LayoutView):
    def __init__(self, *, timeout: float | None = 180, user:"User") -> None:
        super().__init__(timeout=timeout)
        self.user = user
        self.container = Container(accent_color=discord.Colour.green())
        self.text_display = TextDisplay(
            content=f"user_id: {self.user.id}\nusername: {self.user.display_name}\nUser is successfully removed from database.", id=1
        )

        self.container.add_item(self.text_display)

        self.add_item(self.container)



class UserButtons(ActionRow):
    def __init__(self, view:"ConfirmUserDelete", user: "User", admin_id: int, delete_callback:Callable[[int], Awaitable]) -> None:
        super().__init__()
        self._view = view
        self.user = user
        self.admin_id = admin_id
        self.delete_user_callback = delete_callback


    @button(label="Delete User", style=discord.ButtonStyle.primary, disabled=True)
    async def delete_user_confirm(self, interaction: Interaction, button: Button) -> None:
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message(
                "You can't interact with this message.", ephemeral=True
            )
            return

        try:
            if interaction.message:
                await interaction.response.defer(ephemeral=True)
                await self.delete_user_callback(self.user.id)
                success_view = SuccessUserDelete(user=self.user)
                await interaction.edit_original_response(view=success_view)


        except Exception as e:
            logger.error(f"error: {e}")

        

class ConfirmUserDelete(LayoutView):
    def __init__(self, *, timeout: float | None = 180, user:"User", admin_id:int, delete_user_callback: Callable[[int], Awaitable]) -> None:
        super().__init__(timeout=timeout)
        self.user = user
        self.admin_id = admin_id
        
        self.buttons = UserButtons(view=self, user=self.user, admin_id=self.admin_id, delete_callback=delete_user_callback)
        self.title_display: TextDisplay = TextDisplay(content=f"*# WARNING\n")
        self.user_display: TextDisplay = TextDisplay(content=f"user_id: {self.user.id}\ndisplay_name: {self.user.display_name}\n")
        self.text_display = TextDisplay(
            content=f"Confirm this user will be removed from the database", id=1
        )
        self.container = Container(self.title_display, self.user_display, self.text_display, self.buttons, accent_colour=discord.Colour.red())

        
        self.add_item(self.container)

class HelpView(LayoutView):
    def __init__(self, dev_user: Member, rules_channel_url: str, timeout: int = 180) -> None:
        self.dev_user = dev_user
        self.rules_channel_url = rules_channel_url
        super().__init__(timeout=timeout)
        text = ("""**\nCOMMANDS**\n**/testtekin stats**\nDisplays the given user's statistics\nIf the user option not given it displays statistics of the user who called the command.\n
        \n**/bottekin make_it_quote**\nGenerates a quote imaage based on the given message content.\nIn order to use this command, right click on a message hover on apps and click make_it_quote. The message content should be more than 5 characters and less than 500 characters\nThe Original message's author can delete the bot's quote message by clicking remove my quote button.\n"Remove my quote button" is visible to everyone but only responsive to the original message's author and to the user who called the command"""
        f"**\nCONTACT**\nYou can send an email to aiden8hunter@gmail.com\nAnd feel free to send a dm to me {self.dev_user.mention}\n"
        f"**\nPRIVACY**\nThis bot cannot access any private data or does not store any private data.\nThe stored data are:\nuser id and username provided by discord API\nTrack titles you shared in the server\nFeedback message content and statistics of shared tracks, feedback messages, challenges you participated&won bot stores these data to present the statistics to you and the other members.\nBy default, the bot is set to **permanently** delete your data from database after you leave the server.\n**Optionally**, you can set the bot to keep your data by adding a :white_check_mark: to the message on {self.rules_channel_url}.This way, the bot will keep your data even if you leave the server and if you join the server again, your statistics will be preserved.")
 
        self.first_page_text = text
        self.title_display: TextDisplay = TextDisplay(content=f"**TESTTEKİN HELP** 🆘\n")
        self.content_display: TextDisplay = TextDisplay(content=self.first_page_text)
        self.container = Container(self.title_display, self.content_display, accent_colour=discord.Color.dark_purple())

        self.add_item(self.container)

