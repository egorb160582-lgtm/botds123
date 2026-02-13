import discord
from discord import ui
from datetime import datetime

# Ярко-зеленый цвет для всех DM сообщений
BRIGHT_GREEN = 0x00FF00


class RejectReasonModal(ui.Modal, title="Причина отклонения"):
    """Modal для ввода причины отклонения."""

    reason = ui.TextInput(
        label="Причина (необязательно)",
        placeholder="Укажите причину отклонения...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000
    )

    def __init__(self, bot, application_id: int):
        super().__init__()
        self.bot = bot
        self.application_id = application_id

    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отклонения заявки."""
        from database import get_application, update_application, get_guild_settings

        await interaction.response.defer(ephemeral=True)

        application = get_application(self.application_id)
        if not application:
            return

        guild_settings = get_guild_settings(interaction.guild_id)
        if not guild_settings:
            return

        applicant = interaction.guild.get_member(application['user_id'])

        update_application(self.application_id, status='rejected', moderator_id=interaction.user.id)

        channel_id = application.get('channel_id')
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.delete(reason="Заявка отклонена")
                except:
                    pass

        clan_name = guild_settings.get('clan_name', 'Клан')
        if applicant:
            try:
                embed = discord.Embed(
                    title="Отклонение заявки",
                    description=f"Ваша заявка в {clan_name} **отклонена**!",
                    color=BRIGHT_GREEN
                )

                if self.reason.value:
                    embed.add_field(
                        name="Причина:",
                        value=self.reason.value,
                        inline=False
                    )

                embed.add_field(
                    name="ID Дискорд сервера:",
                    value=str(interaction.guild_id),
                    inline=False
                )

                embed.add_field(
                    name="Дата отклонения:",
                    value=f"<t:{int(datetime.now().timestamp())}:R>",
                    inline=False
                )

                await applicant.send(embed=embed)
            except discord.Forbidden:
                pass

        # Отправляем лог об отклонении
        from utils.embeds import send_log
        await send_log(
            guild=interaction.guild,
            application=application,
            moderator=interaction.user,
            applicant=applicant,
            action='rejected',
            reason=self.reason.value if self.reason.value else None
        )


class ModerationView(ui.View):
    """View с кнопками модерации заявки."""

    def __init__(self, bot, application_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.application_id = application_id

    async def check_permissions(self, interaction: discord.Interaction) -> bool:
        """Проверяет права пользователя на использование кнопок."""
        from database import get_guild_settings

        guild_settings = get_guild_settings(interaction.guild_id)
        if not guild_settings:
            return False

        moderator_roles = guild_settings.get('moderator_roles', [])
        moderator_users = guild_settings.get('moderator_users', [])

        if interaction.user.id in moderator_users:
            return True

        user_role_ids = [role.id for role in interaction.user.roles]
        return any(role_id in user_role_ids for role_id in moderator_roles)

    @ui.button(label="Принять", style=discord.ButtonStyle.success, custom_id="accept_application")
    async def accept_button(self, interaction: discord.Interaction, button: ui.Button):
        """Принять заявку."""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message(
                "У вас нет прав для выполнения этого действия.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        from database import get_application, update_application, get_guild_settings

        application = get_application(self.application_id)
        if not application:
            return

        guild_settings = get_guild_settings(interaction.guild_id)
        if not guild_settings:
            return

        applicant = interaction.guild.get_member(application['user_id'])
        if not applicant:
            return

        member_role_id = guild_settings.get('member_role_id')
        if member_role_id:
            member_role = interaction.guild.get_role(member_role_id)
            if member_role:
                try:
                    await applicant.add_roles(member_role)
                except discord.Forbidden:
                    pass

        update_application(self.application_id, status='accepted', moderator_id=interaction.user.id)

        channel_id = application.get('channel_id')
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.delete(reason="Заявка принята")
                except:
                    pass

        branch_channel_id = guild_settings.get('branch_channel_id')

        if branch_channel_id:
            branch_channel = interaction.guild.get_channel(branch_channel_id)
            if branch_channel:
                try:
                    moderator_roles = guild_settings.get('moderator_roles', [])
                    moderator_users = guild_settings.get('moderator_users', [])

                    thread = await branch_channel.create_thread(
                        name=f"{applicant.name}",
                        type=discord.ChannelType.private_thread,
                        reason=f"Ветка для принятого участника {applicant.name}"
                    )

                    await thread.add_user(applicant)

                    for role_id in moderator_roles:
                        role = interaction.guild.get_role(role_id)
                        if role:
                            for member in role.members:
                                try:
                                    await thread.add_user(member)
                                except:
                                    pass

                    for user_id in moderator_users:
                        member = interaction.guild.get_member(user_id)
                        if member:
                            try:
                                await thread.add_user(member)
                            except:
                                pass

                    await thread.send(f"Добро пожаловать, {applicant.mention}! Ваша заявка была принята.")

                    update_application(self.application_id, member_thread_id=thread.id)

                except Exception as e:
                    print(f"Ошибка создания ветки: {e}")

        clan_name = guild_settings.get('clan_name', 'Клан')
        try:
            embed = discord.Embed(
                title="Принятие заявки.",
                description=f"Ваша заявка в {clan_name} **принята**!",
                color=BRIGHT_GREEN
            )

            embed.add_field(
                name="ID Дискорд сервера:",
                value=str(interaction.guild_id),
                inline=False
            )

            embed.add_field(
                name="Дата принятия:",
                value=f"<t:{int(datetime.now().timestamp())}:R>",
                inline=False
            )

            await applicant.send(embed=embed)
        except discord.Forbidden:
            pass

        # Отправляем лог о принятии
        from utils.embeds import send_log
        await send_log(
            guild=interaction.guild,
            application=application,
            moderator=interaction.user,
            applicant=applicant,
            action='accepted'
        )

    @ui.button(label="Взять на рассмотрение", style=discord.ButtonStyle.primary, custom_id="review_application")
    async def review_button(self, interaction: discord.Interaction, button: ui.Button):
        """Взять заявку на рассмотрение."""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message(
                "У вас нет прав для выполнения этого действия.",
                ephemeral=True
            )
            return

        from database import get_application, update_application, get_guild_settings

        application = get_application(self.application_id)
        if not application:
            await interaction.response.defer()
            return

        guild_settings = get_guild_settings(interaction.guild_id)
        clan_name = guild_settings.get('clan_name', 'Клан') if guild_settings else 'Клан'

        applicant = interaction.guild.get_member(application['user_id'])
        if not applicant:
            await interaction.response.defer()
            return

        update_application(self.application_id, status='reviewing', moderator_id=interaction.user.id)

        await interaction.response.send_message(
            f"Заявка взята на **рассмотрение** модератором {interaction.user.mention}"
        )

        try:
            embed = discord.Embed(
                title="Рассмотрение заявки.",
                description=f"Ваша заявка в {clan_name} **взята на рассмотрение**!",
                color=BRIGHT_GREEN
            )

            embed.add_field(
                name="Ссылка на заявку:",
                value=f"[{clan_name}]({interaction.message.jump_url})",
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

    @ui.button(label="Вызвать на обзвон", style=discord.ButtonStyle.secondary, custom_id="call_application")
    async def call_button(self, interaction: discord.Interaction, button: ui.Button):
        """Вызвать на обзвон."""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message(
                "У вас нет прав для выполнения этого действия.",
                ephemeral=True
            )
            return

        from database import get_application
        from views.channel_select import VoiceChannelSelect

        application = get_application(self.application_id)
        if not application:
            await interaction.response.defer()
            return

        view = VoiceChannelSelect(self.bot, self.application_id, application['user_id'], interaction.channel)
        await interaction.response.send_message(
            "Выберите голосовой канал для обзвона:",
            view=view,
            ephemeral=True
        )

    @ui.button(label="Отклонить", style=discord.ButtonStyle.danger, custom_id="reject_application")
    async def reject_button(self, interaction: discord.Interaction, button: ui.Button):
        """Отклонить заявку - открывает модальное окно для причины."""
        if not await self.check_permissions(interaction):
            await interaction.response.send_message(
                "У вас нет прав для выполнения этого действия.",
                ephemeral=True
            )
            return

        modal = RejectReasonModal(self.bot, self.application_id)
        await interaction.response.send_modal(modal)


class ApplicationPanelView(ui.View):
    """View с кнопкой подачи заявки."""

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(label="Подать заявку", style=discord.ButtonStyle.success, custom_id="submit_application")
    async def submit_button(self, interaction: discord.Interaction, button: ui.Button):
        """Открыть форму подачи заявки."""
        from views.application_modal import ApplicationModal

        modal = ApplicationModal(self.bot)
        await interaction.response.send_modal(modal)
