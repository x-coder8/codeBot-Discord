### Discord codeBot by Shadowչ (x.coder) ###

import discord
from discord.ext import commands, tasks
from discord import app_commands
import traceback
import asyncio
import random
import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurar logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M'
)
logger = logging.getLogger()

# Configurar API do Gemini e criar modelo global
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
GEMINI_MODEL = genai.GenerativeModel("gemini-2.0-flash-lite")

# Classe para centralizar configurações
class Config:
    VOICE_CHANNELS = dict(zip(
        [int(os.getenv(f'VOICE_CHANNEL_{i}_ID')) for i in range(1, 5)],
        ["Chill Out 1", "Chill Out 2", "Studio 1", "Studio 2"]
    ))
    CHANNELS = {
        'text': int(os.getenv("TEXT_CHANNEL_ID", 0)),
        'main': int(os.getenv("MAIN_CHANNEL_ID", 0)),
        'logs': int(os.getenv("LOGS_CHANNEL_ID", 0)),
    }
    BOT_NAMES = ["ub|codebot", "codebot"]
    GAMES_LIST = ["Python", "Rust", "Java Script", "Visual Studio Code", "PHP"]
    GAMES_LIST2 = ["Python", "Rust", "Java Script", "C++", "PHP"]
    STATIC_WELCOME = f"hey... , {{member.mention}}, bem-vindo/a ao Discord do **#code.lab**! Para saberes mais sobre nós, passa na sala <#{os.getenv('INFO_CHANNEL_ID')}>"
    STATIC_MENTION = "Olá, disseste o meu nome? Desculpa não poder dar atenção, neste momento estou um pouco ocupado... "

# Cache global para canais
CHANNEL_CACHE = {}

# Função para validar variáveis de ambiente
def get_env_variable(key, default=None):
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"A variável de ambiente {key} não está definida.")
    return value

# Função para verificar permissões
async def has_permissions(channel, permissions):
    return channel.permissions_for(channel.guild.me) >= permissions

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='', intents=intents)

# Função para gerar mensagem dinâmica com IA
async def generate_ai_message(prompt):
    try:
        response = GEMINI_MODEL.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Erro ao gerar mensagem com IA: {e}")
        return None

# Função para gerar uma frase curiosa sobre uma linguagem
async def gerar_frase_desafiante():
    jogo = random.choice(Config.GAMES_LIST2)
    prompt = f"És um especialista em linguagens de programação, escreve uma pequena frase, em português de Portugal, útil sobre técnicas de programação em {jogo}, sem emoji's."
    try:
        response = GEMINI_MODEL.generate_content(prompt)
        frase = response.text.strip() if response.text else "Não consegui gerar uma frase."
    except Exception as e:
        logger.error(f"Erro ao gerar frase: {e}")
        frase = "O silêncio na guerra também pode ser uma mensagem."
    return f"🔹***code**Tips*: *{frase}*"

# Função para mudar a actividade do bot
async def change_activity_to_game():
    game = random.choice(Config.GAMES_LIST)
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=game))
        logger.info(f"Actividade alterada para 'playing {game}'")
    except Exception as e:
        logger.error(f"Erro ao alterar actividade: {e}")

# Função para restaurar a actividade padrão
async def reset_activity():
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="#code.lab"))
        logger.info("Actividade restaurada para 'watching #code.lab'")
    except Exception as e:
        logger.error(f"Erro ao restaurar actividade: {e}")

# Tarefa cíclica para gerir a actividade
@tasks.loop(minutes=60)  # A cada hora
async def activity_cycle():
    await change_activity_to_game()
    logger.info("Actividade será restaurada em 20 minutos.")
    await asyncio.sleep(1200)  # Espera 20 minutos
    await reset_activity()

# Função para renomear salas de voz
async def rename_voice_channel(channel, game):
    if game:
        try:
            await channel.edit(name=game)
            logger.info(f'Sala {channel.name} renomeada para {game}')
            return True
        except discord.Forbidden:
            logger.error(f'Sem permissões para renomear {channel.name}')
        except Exception as e:
            logger.error(f"Erro ao renomear sala de voz: {e}")
    return False

# Tarefa periódica para verificar salas de voz
@tasks.loop(minutes=20)
async def check_voice_channels():
    try:
        for channel_id, original_name in Config.VOICE_CHANNELS.items():
            channel = bot.get_channel(channel_id)
            if channel and not channel.members:
                await channel.edit(name=original_name)
                logger.info(f'{channel.name} (verificação e restauração do nome original).')
    except Exception as e:
        logger.error(f'Erro ao verificar salas de voz: {e}')

# Tarefa periódica para limpar canal de actividade
@tasks.loop(minutes=20)
async def cleanup_activity_channel():
    try:
        channel = CHANNEL_CACHE.get('text')
        if channel:
            messages = [msg async for msg in channel.history(limit=100)]
            if len(messages) > 20:
                for msg in messages[20:]:
                    await msg.delete()
                logger.info('Removidas mensagens antigas no canal activity.')
    except Exception as e:
        logger.error(f'Erro ao limpar mensagens antigas: {e}')

# Função para obter o jogo atual de um membro
def get_current_game(member: discord.Member) -> str:
    for activity in member.activities:
        if activity.type == discord.ActivityType.playing:
            logger.info(f'{member.display_name} está a jogar {activity.name}')
            return activity.name
    logger.info(f'{member.display_name} não está a jogar nada.')
    return None

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    try:
        if after.channel and after.channel.id in Config.VOICE_CHANNELS:
            game = get_current_game(member)
            if await rename_voice_channel(after.channel, game):
                text_channel = CHANNEL_CACHE.get('text')
                if text_channel:
                    await text_channel.send(f'{member.display_name} iniciou {game} numa sala de voz. Junta-te ao desafio!')
        
        if before.channel and not after.channel and before.channel.id in Config.VOICE_CHANNELS:
            if not before.channel.members:
                original_name = Config.VOICE_CHANNELS.get(before.channel.id)
                if original_name:
                    await before.channel.edit(name=original_name)
                    logger.info(f'{before.channel.name} voltou ao nome original: {original_name}')
    except discord.Forbidden:
        logger.error(f'Sem permissões para renomear sala para {member.id}')
    except Exception as e:
        logger.error(f'Erro no on_voice_state_update: {e}')

# Comando /ping
@bot.tree.command(name="ping", description="Responde com a latência do bot.")
async def ping(interaction: discord.Interaction):
    try:
        latency = bot.latency * 1000
        await interaction.response.send_message(f'Pong! Latência: {latency:.2f}ms')
    except Exception as e:
        logger.error(f'Erro no comando ping: {e}')

# Comando /coin
@bot.tree.command(name="coin", description="Lança uma moeda virtual.")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def coin(interaction: discord.Interaction):
    try:
        outcome = '**Cara**' if random.randint(0, 1) == 0 else '**Coroa**'
        await interaction.response.send_message(f'A moeda rodou, e caiu em {outcome}')
    except Exception as e:
        logger.error(f'Erro no comando coin: {e}')

# Comando /tips
@bot.tree.command(name="tips", description="Envia uma dica sobre programação na sala lobby.")
async def send(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        
        channel = CHANNEL_CACHE.get('main')
        if not channel:
            await interaction.followup.send("Erro: Canal não encontrado.", ephemeral=True)
            return
        
        frase = await gerar_frase_desafiante()
        await channel.send(frase)
        await interaction.followup.send("Frase enviada com sucesso!", ephemeral=True)
    except Exception as e:
        logger.error(f"Erro ao enviar frase: {e}")
        await interaction.followup.send("Ocorreu um erro ao enviar a frase.", ephemeral=True)

# Comando /say
def is_admin(interaction: discord.Interaction) -> bool:
    return any(role.id == int(get_env_variable('ADMIN_ROLE_ID')) for role in interaction.user.roles)

class SayModal(discord.ui.Modal, title="Enviar Mensagem Anónima"):
    mensagem = discord.ui.TextInput(label="Mensagem", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        if not await has_permissions(interaction.channel, discord.Permissions(send_messages=True)):
            await interaction.response.send_message("❌ O bot não tem permissões para enviar mensagens neste canal.", ephemeral=True)
            return
        try:
            view = UploadView(str(self.mensagem))
            await interaction.response.send_message(
                "Mensagem escrita! Queres anexar uma imagem? Se sim, clica no botão abaixo.",
                view=view,
                ephemeral=True
            )
            view.message = await interaction.original_response()
            await view.wait()
        except Exception as e:
            logger.error(f"Erro no envio do modal: {e}")
            await interaction.response.send_message("❌ Ocorreu um erro ao processar a mensagem.", ephemeral=True)

class UploadView(discord.ui.View):
    def __init__(self, mensagem: str):
        super().__init__(timeout=60)
        self.mensagem = mensagem
        self.message = None

    async def send_message(self, interaction: discord.Interaction, file: discord.File = None):
        if not await has_permissions(interaction.channel, discord.Permissions(send_messages=True)):
            await self.send_feedback(interaction, "❌ O bot não tem permissões para enviar mensagens neste canal.")
            return
        try:
            logger.info(f"Enviando mensagem: '{self.mensagem}' com arquivo: {file.filename if file else 'Nenhum'}")
            await interaction.channel.send(content=self.mensagem, file=file)
            await self.send_feedback(interaction, "✅ Mensagem enviada com sucesso!")
        except discord.HTTPException as e:
            await self.send_feedback(interaction, f"❌ Erro ao enviar a mensagem: {str(e)}")

    async def send_feedback(self, interaction: discord.Interaction, content: str):
        try:
            await interaction.followup.send(content, ephemeral=True)
        except discord.HTTPException:
            pass

    @discord.ui.button(label="📤 Upload de Imagem", style=discord.ButtonStyle.primary)
    async def upload_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Agora envia a imagem aqui neste chat! Tens 60 segundos.", ephemeral=True)
        def check(m: discord.Message):
            return m.author == interaction.user and len(m.attachments) > 0
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            file = await msg.attachments[0].to_file()
            if msg.channel.permissions_for(msg.guild.me).manage_messages:
                await msg.delete()
            await self.send_message(interaction, file=file)
        except asyncio.TimeoutError:
            await self.send_feedback(interaction, "❌ O tempo para enviar a imagem expirou.")
        except Exception as e:
            await self.send_feedback(interaction, f"❌ Erro ao processar a imagem: {str(e)}")

    @discord.ui.button(label="📨 Enviar Sem Imagem", style=discord.ButtonStyle.secondary)
    async def send_text_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.send_message(interaction)
        self.stop()

    async def on_timeout(self):
        if self.message:
            await self.message.edit(content="❌ Tempo esgotado. Ação cancelada.", view=None)

@bot.tree.command(name="say", description="Envia uma mensagem anonimamente")
@app_commands.check(is_admin)
async def say(interaction: discord.Interaction):
    await interaction.response.send_modal(SayModal())

@say.error
async def say_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)

@bot.event
async def on_ready():
    logger.info(f'Bot conectado como {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="#code.lab"))

    # Cachear canais
    CHANNEL_CACHE['text'] = bot.get_channel(Config.CHANNELS['text'])
    CHANNEL_CACHE['main'] = bot.get_channel(Config.CHANNELS['main'])
    CHANNEL_CACHE['logs'] = bot.get_channel(Config.CHANNELS['logs'])

    try:
        synced = await bot.tree.sync()
        logger.info(f'Sincronizados {len(synced)} comandos: {[cmd.name for cmd in synced]}')
    except Exception as e:
        logger.error(f'Erro ao sincronizar comandos: {e}')

    try:
        if not check_voice_channels.is_running():
            check_voice_channels.start()
        if not cleanup_activity_channel.is_running():
            cleanup_activity_channel.start()
        if not activity_cycle.is_running():
            activity_cycle.start()
        logger.info("Tarefas periódicas iniciadas.")
    except Exception as e:
        logger.error(f'Erro ao iniciar tarefas: {e}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.lower()
    if bot.user.mentioned_in(message) or "codebot" in content:
        prompt = f"imagina-te o codeBot, mestre da programação, membro principal do **#code.lab**, e dá uma pequena resposta em português de Portugal à mensagem de {message.author.name}: {message.content}"
        ai_message = await generate_ai_message(prompt)
        await message.channel.send(ai_message if ai_message else Config.STATIC_MENTION)

@bot.event
async def on_member_join(member):
    channel = CHANNEL_CACHE.get('main')
    if channel:
        prompt = f"imagina-te o codeBot, mestre da programação. Escreve uma pequena frase de bem-vindo/a em português de Portugal, a tratar por tu, como neste exemplo: 'Olá, {member.mention}, bem-vindo/a ao Discord do **#code.lab**! Para saberes mais sobre nós, passa na sala <#{os.getenv('INFO_CHANNEL_ID')}>.'"
        ai_message = await generate_ai_message(prompt)
        await channel.send(ai_message if ai_message else Config.STATIC_WELCOME.format(member=member))
    
    log_channel = CHANNEL_CACHE.get('logs')
    if log_channel:
        await log_channel.send(f"🔹 O utilizador **{member.name}** entrou no servidor.")

@bot.event
async def on_member_remove(member):
    log_channel = CHANNEL_CACHE.get('logs')
    if log_channel:
        await log_channel.send(f"🔸 O utilizador **{member.name}** saiu do servidor.")

# Iniciar o bot
bot.run(get_env_variable('DISCORD_TOKEN'))
