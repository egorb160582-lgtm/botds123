import discord
from discord import ui
from datetime import datetime

# Ярко-зеленый цвет для всех DM сообщений
BRIGHT_GREEN = 0x00FF00


class VoiceChannelSelect(ui.View):
    """View для выбора голосового канала при вызове на обзвон."""

    def __init__(self, bot, application_id: int, applicant_id: int, channel=None):
        super().__init__(timeout=60)
        self.bot = bot
        self.application_id = application_id
        self.applicant_id = applicant_id
        self.channel = channel

    @ui.select(
        cls=ui.ChannelSelect,
        channel_types=[discord.ChannelType.voice],
        placeholder="Выберите голосовой канал...",
        min_values=1,
        max_values=1
    )
    async def select_channel(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        """Обработка выбора голосового канала."""
        from database import get_guild_settings

        await interaction.response.defer(ephemeral=True)

        voice_channel = select.values[0]
        applicant = interaction.guild.get_member(self.applicant_id)

        if not applicant:
            return

        guild_settings = get_guild_settings(interaction.guild_id)
        clan_name = guild_settings.get('clan_name', 'Клан') if guild_settings else 'Клан'

        if self.channel:
            await self.channel.send(
                f"{interaction.user.mention} вызвал на обзвон {applicant.mention}\n"
                f"Зайдите в голосовой канал {voice_channel.mention}"
            )

        try:
            embed = discord.Embed(
                title="Приглашение на обзвон",
                description="Вы были вызваны на **обзвон**!",
                color=BRIGHT_GREEN
            )

            embed.add_field(
                name="",
                value=f"Вас приглашают присоединиться к голосовому каналу: **{clan_name}**\n{voice_channel.mention}",
                inline=False
            )

            embed.add_field(
                name="ID Дискорд сервера:",
                value=str(interaction.guild_id),
                inline=False
            )

            embed.add_field(
                name="Дата события:",
                value=f"<t:{int(datetime.now().timestamp())}:R>",
                inline=False
            )

            await applicant.send(embed=embed)
        except discord.Forbidden:
            pass

        self.stop()

    async def on_timeout(self):
        """Обработка таймаута."""
        for item in self.children:
            item.disabled = True
