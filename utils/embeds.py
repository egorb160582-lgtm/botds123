import discord
from datetime import datetime
from typing import Optional, Dict, Any

# Цвета для логов
LOG_COLOR_ACCEPTED = 0x00FF00  # Ярко-зеленый
LOG_COLOR_REJECTED = 0xFF0000  # Ярко-красный


def create_application_embed(
    user: discord.Member,
    static: str,
    hours_per_day: str,
    age_oos: str,
    ready_online: str,
    how_found: Optional[str],
    application_id: int
) -> discord.Embed:
    """Создает embed с данными заявки."""
    embed = discord.Embed(
        title="Заявление",
        color=0x2b2d31,
        timestamp=datetime.now()
    )

    embed.add_field(name="#Статик", value=static, inline=False)
    embed.add_field(name="Сколько часов в день играешь?", value=hours_per_day, inline=False)
    embed.add_field(name="Возраст ООС", value=age_oos, inline=False)
    embed.add_field(name="Готовы онлайнить?", value=ready_online, inline=False)

    if how_found:
        embed.add_field(name="Как узнали о семье", value=how_found, inline=False)

    embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.add_field(name="Пользователь", value=f"@{user.name}", inline=True)
    embed.add_field(name="Username", value=user.name, inline=True)
    embed.add_field(name="ID", value=str(user.id), inline=True)

    embed.set_footer(text=f"Заявка #{application_id}")

    return embed


def create_log_embed(
    application: Dict[str, Any],
    moderator: discord.Member,
    applicant: discord.Member,
    action: str,
    reason: Optional[str] = None
) -> discord.Embed:
    """Создает embed для лога заявки.

    Args:
        application: Данные заявки из БД
        moderator: Модератор, который рассмотрел заявку
        applicant: Пользователь, подавший заявку
        action: 'accepted' или 'rejected'
        reason: Причина отклонения (только для rejected)
    """
    is_accepted = action == 'accepted'

    embed = discord.Embed(
        color=LOG_COLOR_ACCEPTED if is_accepted else LOG_COLOR_REJECTED,
        timestamp=datetime.now()
    )

    # Заголовок заявки
    embed.title = "Заявление"

    # Поля заявки
    embed.add_field(name="#Статик", value=application.get('static', 'Не указано'), inline=False)
    embed.add_field(name="Сколько часов в день играешь?", value=application.get('hours_per_day', 'Не указано'), inline=False)
    embed.add_field(name="Возраст ООС", value=f"Мне {application.get('age_oos', 'Не указано')}", inline=False)

    if application.get('how_found'):
        embed.add_field(name="Как узнали о семье", value=application.get('how_found'), inline=False)

    embed.add_field(name="Готовы онлайнить?", value=application.get('ready_online', 'Не указано'), inline=False)

    # Разделитель
    embed.add_field(name="\u200b", value="\u200b", inline=False)

    # Информация о пользователе
    embed.add_field(name="Пользователь", value=f"@{applicant.name}" if applicant else f"@{application.get('username', 'Unknown')}", inline=True)
    embed.add_field(name="Username", value=application.get('username', 'Unknown'), inline=True)
    embed.add_field(name="ID", value=str(application.get('user_id', 'Unknown')), inline=True)

    # Разделитель
    embed.add_field(name="\u200b", value="\u200b", inline=False)

    # Кто и кого
    if is_accepted:
        embed.add_field(
            name="Кого",
            value=applicant.mention if applicant else f"<@{application.get('user_id')}>",
            inline=True
        )
        embed.add_field(
            name="Принял",
            value=moderator.mention,
            inline=True
        )
    else:
        embed.add_field(
            name="Кого",
            value=applicant.mention if applicant else f"<@{application.get('user_id')}>",
            inline=True
        )
        embed.add_field(
            name="Отклонил",
            value=moderator.mention,
            inline=True
        )

    # Текст внизу
    if is_accepted:
        footer_text = f"{moderator.display_name} рассмотрел заявку и принял {applicant.display_name if applicant else application.get('username', 'Unknown')}"
    else:
        footer_text = f"{moderator.display_name} рассмотрел заявку и отклонил {applicant.display_name if applicant else application.get('username', 'Unknown')}"

    embed.set_footer(text=footer_text)

    # Добавляем причину отклонения если есть
    if not is_accepted and reason:
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="**Причина:**", value=reason, inline=False)

    return embed


async def send_log(
    guild: discord.Guild,
    application: Dict[str, Any],
    moderator: discord.Member,
    applicant: discord.Member,
    action: str,
    reason: Optional[str] = None
) -> bool:
    """Отправляет лог в канал логов.

    Returns:
        True если лог отправлен, False если канал не настроен
    """
    from database import get_guild_settings

    guild_settings = get_guild_settings(guild.id)
    if not guild_settings:
        return False

    logs_channel_id = guild_settings.get('logs_channel_id')
    if not logs_channel_id:
        return False

    logs_channel = guild.get_channel(logs_channel_id)
    if not logs_channel:
        return False

    embed = create_log_embed(application, moderator, applicant, action, reason)

    try:
        await logs_channel.send(embed=embed)
        return True
    except discord.Forbidden:
        return False
