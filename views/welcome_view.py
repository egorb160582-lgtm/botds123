import discord
from discord import ui


class WelcomeView(ui.View):
    """View с кнопкой получения роли в прихожей."""

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(label="Нажми для получения роли", style=discord.ButtonStyle.success, custom_id="get_welcome_role")
    async def get_role_button(self, interaction: discord.Interaction, button: ui.Button):
        """Выдает роль пользователю."""
        from database import get_guild_settings

        guild_settings = get_guild_settings(interaction.guild_id)

        if not guild_settings:
            await interaction.response.send_message(
                "Бот не настроен. Обратитесь к администратору.",
                ephemeral=True
            )
            return

        welcome_role_id = guild_settings.get('welcome_role_id')
        if not welcome_role_id:
            await interaction.response.send_message(
                "Роль не настроена. Обратитесь к администратору.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(welcome_role_id)
        if not role:
            await interaction.response.send_message(
                "Роль не найдена. Обратитесь к администратору.",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "У вас уже есть эта роль!",
                ephemeral=True
            )
            return

        try:
            await interaction.user.add_roles(role, reason="Получение роли через панель")

            embed = discord.Embed(
                title="Управление ролями",
                color=0x57F287
            )

            embed.add_field(
                name="",
                value=f"Роли были **выданы**!",
                inline=False
            )

            embed.add_field(
                name="Выданные роли:",
                value=f"@{role.name}",
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message(
                "Не удалось выдать роль. Проверьте права бота.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Произошла ошибка: {e}",
                ephemeral=True
            )
