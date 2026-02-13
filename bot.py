import discord
from discord.ext import commands
import asyncio

from config import BOT_TOKEN, BOT_STATUS

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True


class ApplicationBot(commands.Bot):
    """Основной класс бота."""

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """Загрузка cogs и синхронизация команд."""
        # Загружаем cogs
        cogs = ['cogs.setup']
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"[+] Загружен cog: {cog}")
            except Exception as e:
                print(f"[-] Ошибка загрузки {cog}: {e}")

        # Регистрируем persistent views
        from views.moderation_buttons import ApplicationPanelView, ModerationView
        from views.welcome_view import WelcomeView

        self.add_view(ApplicationPanelView(self))
        self.add_view(WelcomeView(self))

        # Для ModerationView нужно восстановить все активные заявки
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM applications
            WHERE status IN ('pending', 'reviewing')
        """)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.add_view(ModerationView(self, row['id']))

        print(f"[+] Восстановлено {len(rows)} активных заявок")

    async def on_ready(self):
        """Событие при готовности бота."""
        print(f"{'='*50}")
        print(f"Бот запущен: {self.user.name}")
        print(f"ID: {self.user.id}")
        print(f"Серверов: {len(self.guilds)}")
        print(f"{'='*50}")

        # Устанавливаем статус
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=BOT_STATUS
        )
        await self.change_presence(activity=activity)

        # Синхронизируем команды для каждого сервера
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                print(f"[+] Синхронизировано {len(synced)} команд для сервера {guild.name}")
            except Exception as e:
                print(f"[-] Ошибка синхронизации для {guild.name}: {e}")

    async def on_member_remove(self, member: discord.Member):
        """Событие при выходе пользователя с сервера - удаляем его ветки."""
        from database import get_user_member_threads, update_application

        # Получаем все ветки участника
        threads = get_user_member_threads(member.guild.id, member.id)

        for thread_data in threads:
            thread_id = thread_data.get('member_thread_id')
            if thread_id:
                try:
                    thread = member.guild.get_thread(thread_id)
                    if not thread:
                        try:
                            thread = await member.guild.fetch_channel(thread_id)
                        except:
                            continue

                    if thread:
                        await thread.delete()
                        print(f"[+] Удалена ветка {thread.name} для пользователя {member.name}")
                        update_application(thread_data['id'], member_thread_id=None)
                except Exception as e:
                    print(f"[-] Ошибка удаления ветки: {e}")


async def main():
    """Запуск бота."""
    from database import init_database
    init_database()
    print("[+] База данных инициализирована")

    bot = ApplicationBot()

    async with bot:
        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
