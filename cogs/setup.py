import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional


class SetupCog(commands.Cog):
    """Команды настройки бота."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="welcome", description="Настроить панель получения роли в прихожей")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        роль="Роль, которую получит пользователь",
        фото="Ссылка на изображение для панели"
    )
    async def welcome(
        self,
        interaction: discord.Interaction,
        роль: discord.Role,
        фото: Optional[str] = None
    ):
        """Создает панель получения роли."""
        from database import save_guild_settings
        from views.welcome_view import WelcomeView

        # Сохраняем настройки
        save_guild_settings(
            interaction.guild_id,
            welcome_role_id=роль.id,
            welcome_image_url=фото
        )

        # Отправляем панель
        view = WelcomeView(self.bot)

        if фото:
            await interaction.channel.send(content=фото, view=view)
        else:
            await interaction.channel.send(view=view)

        await interaction.response.send_message(
            f"Панель размещена! Роль для выдачи: {роль.mention}",
            ephemeral=True
        )

    @app_commands.command(name="zayava", description="Настроить панель заявок")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        название="Название клана/семьи",
        описание="Описание для панели (используй /n или | для переноса строки)",
        фото="Ссылка на изображение",
        роль="Роль, которую получит принятый участник",
        категория="Категория для создания каналов заявок",
        ветка="Канал для создания веток принятых участников"
    )
    async def zayava(
        self,
        interaction: discord.Interaction,
        название: Optional[str] = None,
        описание: Optional[str] = None,
        фото: Optional[str] = None,
        роль: Optional[discord.Role] = None,
        категория: Optional[discord.CategoryChannel] = None,
        ветка: Optional[discord.TextChannel] = None
    ):
        """Настройка и размещение панели заявок."""
        from database import save_guild_settings
        from views.moderation_buttons import ApplicationPanelView

        # Сохраняем настройки
        updates = {}

        if название:
            updates['clan_name'] = название
        if описание:
            text = описание.replace('\\n', '\n').replace('/n', '\n').replace('|', '\n')
            updates['panel_text'] = text
        if фото:
            updates['panel_image_url'] = фото
        if роль:
            updates['member_role_id'] = роль.id
        if категория:
            updates['applications_category_id'] = категория.id
        if ветка:
            updates['branch_channel_id'] = ветка.id

        if updates:
            save_guild_settings(interaction.guild_id, **updates)

        # Формируем панель
        final_name = название or "Клан"
        final_description = описание.replace('\\n', '\n').replace('/n', '\n').replace('|', '\n') if описание else None

        embed = discord.Embed(color=0x00b413)

        if название:
            embed.title = f"Заявки в {final_name}"

        if final_description:
            embed.description = final_description

        if фото:
            embed.set_image(url=фото)

        if not название and not final_description and not фото:
            embed.title = "Заявки в Клан"
            embed.description = "Нажми на кнопку ниже, чтобы подать заявку!"

        # Отправляем панель
        view = ApplicationPanelView(self.bot)
        await interaction.channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            f"Панель заявок размещена в {interaction.channel.mention}",
            ephemeral=True
        )

    @app_commands.command(name="moderators", description="Установить модераторов заявок")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        роль1="Роль модератора",
        роль2="Роль модератора",
        роль3="Роль модератора",
        роль4="Роль модератора",
        роль5="Роль модератора",
        юзер1="Пользователь-модератор",
        юзер2="Пользователь-модератор",
        юзер3="Пользователь-модератор",
        юзер4="Пользователь-модератор",
        юзер5="Пользователь-модератор"
    )
    async def moderators(
        self,
        interaction: discord.Interaction,
        роль1: Optional[discord.Role] = None,
        роль2: Optional[discord.Role] = None,
        роль3: Optional[discord.Role] = None,
        роль4: Optional[discord.Role] = None,
        роль5: Optional[discord.Role] = None,
        юзер1: Optional[discord.Member] = None,
        юзер2: Optional[discord.Member] = None,
        юзер3: Optional[discord.Member] = None,
        юзер4: Optional[discord.Member] = None,
        юзер5: Optional[discord.Member] = None
    ):
        """Устанавливает модераторов заявок."""
        from database import save_guild_settings

        roles = [r for r in [роль1, роль2, роль3, роль4, роль5] if r is not None]
        users = [u for u in [юзер1, юзер2, юзер3, юзер4, юзер5] if u is not None]

        role_ids = [r.id for r in roles]
        user_ids = [u.id for u in users]

        save_guild_settings(
            interaction.guild_id,
            moderator_roles=role_ids,
            moderator_users=user_ids
        )

        response_parts = []
        if roles:
            response_parts.append(f"**Роли:** {', '.join([r.mention for r in roles])}")
        if users:
            response_parts.append(f"**Пользователи:** {', '.join([u.mention for u in users])}")

        if response_parts:
            response = "**Модераторы установлены:**\n" + "\n".join(response_parts)
        else:
            response = "Модераторы очищены."

        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command(name="logs", description="Установить канал для логов заявок")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        канал="Канал для отправки логов"
    )
    async def logs(
        self,
        interaction: discord.Interaction,
        канал: discord.TextChannel
    ):
        """Устанавливает канал для логов заявок."""
        from database import save_guild_settings

        save_guild_settings(
            interaction.guild_id,
            logs_channel_id=канал.id
        )

        embed = discord.Embed(
            title="Канал логов установлен",
            description=f"Логи заявок будут отправляться в {канал.mention}",
            color=0x00FF00
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SetupCog(bot))
