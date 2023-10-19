import discord
from discord.ext import commands
from discord import utils
import os  # default module
from dotenv import load_dotenv
import sqlite3


class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.green, custom_id="ticket_button")
    async def ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        ticket = utils.get(interaction.guild.text_channels, name=f"тикет-пользователя-{interaction.user.name}")
        if ticket is not None:
            await interaction.response.send_message("У тебя уже создан тикет!", ephemeral=True)
        else:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True,
                                                              embed_links=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                                  attach_files=True, embed_links=True,
                                                                  read_message_history=True)
            }
            channel = await interaction.guild.create_text_channel(f"Тикет пользователя {interaction.user.name}",
                                                                  overwrites=overwrites)
            await channel.send(f"{interaction.user.mention} создал тикет!", view=TicketTerminator())
            await interaction.response.send_message(f"Канал {channel.mention} создан!", ephemeral=True)


class ConfirmTermination(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Подтверждаю!", style=discord.ButtonStyle.red, custom_id="ticket_close_button")
    async def close_confirmation(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await interaction.channel.delete()
        except NameError:
            await interaction.response.send_message(
                "Произошла ошибка! Убедитесь, что тикет ещё существует или есть соответствующие права!", ephemeral=True)


class TicketTerminator(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.red, custom_id="ensure_close_button")
    async def ticket_close(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="Вы уверены, что хотите закрыть тикет?", color=discord.Colour.brand_green())
        await interaction.response.send_message(embed=embed, view=ConfirmTermination(), ephemeral=True)


# Connect to the database
conn = sqlite3.connect('discord_users.db')
cursor = conn.cursor()

# Create the table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        discord_id INTEGER PRIMARY KEY,
        level INTEGER,
        balance INTEGER,
        warnds INTEGER
    )
''')

load_dotenv()  # load all the variables from the env file
bot = discord.Bot()


@bot.event
async def on_ready():
    embed = discord.Embed(
        title="Возник вопрос или нужна помощь? Создай тикет и пообщайся с администрацией",
        color=discord.Colour.brand_green(),
    )
    channel = bot.get_channel(1162898434488016988)
    await channel.purge(limit=1)
    await channel.send(embed=embed, view=TicketLauncher())

    for channel in bot.get_all_channels():
        if channel.name.startswith("тикет-пользователя-"):
            await channel.send(
                f"Пожалуйста, после того, как вопрос будет исчерпан, воспользуйтесь кнопкой ниже, чтобы закрыть тикет!",
                view=TicketTerminator())

    print(f"{bot.user} is ready and online!")


@bot.command()
@commands.has_any_role("Модератор Института")
async def add_user(ctx, user: discord.User):
    cursor.execute("INSERT INTO users VALUES(?, ?, ?)", (user.id, 0, 0))
    conn.commit()
    await ctx.respond(f"Пользователь {user.mention} добавлен в базу данных!", ephemeral=True)


@bot.command()
@commands.has_permissions(administrator=True)
async def level_up(ctx, user: discord.User):
    current_level = cursor.execute("SELECT level FROM users WHERE discord_id = ?", (user.id,)).fetchone()
    cursor.execute("UPDATE users SET level = ? WHERE discord_id = ?", (current_level[0] + 1, user.id,))
    conn.commit()
    await ctx.respond(f"Пользователь {user.mention} повысил уровень!")


@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def clear_it(ctx, amount: int = 10):
    if amount < 1:
        await ctx.respond("Число должно быть положительным!")
    await ctx.channel.purge(limit=amount)
    await ctx.respond(f"Успешно очищено **{amount}** сообщений!")


@bot.command(guild=os.getenv('GUILD_ID'))
async def ticketing(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Возник вопрос или нужна помощь? Создай тикет и пообщайся с администрацией",
        color=discord.Colour.brand_green(),
    )
    await interaction.channel.send(embed=embed, view=TicketLauncher())
    await interaction.response.send_message("Тикет-система запущена!", ephemeral=True)


@bot.command(guild=os.getenv('GUILD_ID'))
async def ticket_close(interaction: discord.Interaction):
    if "тикет-пользователя-" in interaction.channel.name:
        embed = discord.Embed(
            title="Вы уверены, что хотите закрыть тикет?",
            colour=discord.Colour.brand_green(),
        )
        await interaction.response.send_message(embed=embed, view=ConfirmTermination(), ephemeral=True)
    else:
        await interaction.response.send_message("Это не тикет!", ephemeral=True)


@bot.command()
async def hello(ctx):
    embed = discord.Embed(
        title="Мощнейщий бот!",
        description="Эмбед-сообщения - это очень очень вкусно",
        color=discord.Colour.brand_green(),  # Pycord provides a class with default colors you can choose from
    )
    embed.add_field(name="Обычное текстовое поле",
                    value="Очень удобное представление. **А тут ещё и форматирование текста???**")

    embed.add_field(name="Инлайн1", value="Инлайн текст", inline=True)
    embed.add_field(name="Инлайн2", value="Инлайн текст", inline=True)
    embed.add_field(name="Инлайн3", value="Инлайн текст", inline=True)

    embed.set_footer(text="Кчау! Мощный эмбед подходит к концу.")  # footers can have icons too
    embed.set_author(name="PolyCord Dev", icon_url="https://naked-science.ru/includ092119937/poli.jpg")
    embed.set_thumbnail(url="https://naked-science.ru/includ092119937/poli.jpg")
    embed.set_image(url="https://www.kop.ru/upload/iblock/112/11259b79643fb595f806ab269ab2c543.jpg")

    await ctx.respond("алё лови аптечку", embed=embed)  # Send the embed with some text


bot.run(os.getenv('TOKEN'))
