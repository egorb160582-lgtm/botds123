import discord
from discord import ui


class ApplicationModal(ui.Modal, title="Подать заявку"):
    """Modal форма для подачи заявки в клан."""

    static = ui.TextInput(
        label="#Статик",
        placeholder="Никнейм который у тебя на данный момент",
        required=True,
        max_length=100
    )

    hours_per_day = ui.TextInput(
        label="Сколько часов в день играешь?",
        placeholder="если меньше 4 часов - заявка будет отклонена",
        required=True,
        max_length=100
    )

    age_oos = ui.TextInput(
        label="Возраст ООС",
        placeholder="Если тебе меньше 16, не подавай тикет!",
        required=True,
        max_length=50
    )

    ready_online = ui.TextInput(
        label="Готовы онлайнить?",
        placeholder="Готовы ли вы онлайнить?",
        required=True,
        max_length=500
    )

    how_found = ui.TextInput(
        label="Как узнали о семье (необязательно)",
        placeholder="Откуда узнал о нас, пару слов",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы."""
        from database import create_application, get_guild_settings, update_application
        from utils.embeds import create_application_embed

        await interaction.response.defer(ephemeral=True)

        guild_settings = get_guild_settings(interaction.guild_id)

        if not guild_settings:
            return

        category_id = guild_settings.get('applications_category_id')
        if not category_id:
            return

        category = interaction.guild.get_channel(category_id)
        if not category:
            return

        # Создаем заявку в базе данных
        application_id = create_application(
            guild_id=interaction.guild_id,
            user_id=interaction.user.id,
            username=interaction.user.name,
            static=self.static.value,
            hours_per_day=self.hours_per_day.value,
            age_oos=self.age_oos.value,
            ready_online=self.ready_online.value,
            how_found=self.how_found.value or None
        )

        # Получаем роли и пользователей модераторов
        moderator_roles = guild_settings.get('moderator_roles', [])
        moderator_users = guild_settings.get('moderator_users', [])

        # Создаем приватный канал
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True
            )
        }

        # Добавляем роли модераторов
        for role_id in moderator_roles:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )

        # Добавляем пользователей-модераторов
        for user_id in moderator_users:
            member = interaction.guild.get_member(user_id)
            if member:
                overwrites[member] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )

        try:
            channel = await interaction.guild.create_text_channel(
                name=f"заявка-{interaction.user.name}",
                category=category,
                overwrites=overwrites,
                reason=f"Заявка от {interaction.user.name}"
            )
        except:
            return

        # Создаем embed с заявкой
        embed = create_application_embed(
            user=interaction.user,
            static=self.static.value,
            hours_per_day=self.hours_per_day.value,
            age_oos=self.age_oos.value,
            ready_online=self.ready_online.value,
            how_found=self.how_found.value or None,
            application_id=application_id
        )

        # Импортируем view для кнопок
        from views.moderation_buttons import ModerationView

        # Отправляем сообщение с заявкой
        view = ModerationView(self.bot, application_id)
        message = await channel.send(
            content=f"{interaction.user.mention}",
            embed=embed,
            view=view
        )

        # Обновляем ID сообщения и канала в базе
        update_application(application_id, message_id=message.id, channel_id=channel.id)

        # Формируем список упоминаний
        mentions = []

        for role_id in moderator_roles:
            role = interaction.guild.get_role(role_id)
            if role:
                mentions.append(role.mention)

        for user_id in moderator_users:
            mentions.append(f"<@{user_id}>")

        # Отправляем пинг модераторам
        if mentions:
            await channel.send(" ".join(mentions))
