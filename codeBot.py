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
    datefmt='%H:%M'  # Formato de hora e minuto
)
logger = logging.getLogger()

# Configurar API do Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

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
intents.members = True  # Para aceder informações dos membros
intents.presences = True  # Para aceder atividades (presenças)
intents.voice_states = True  # Para monitorar estados de voz
intents.message_content = True  # Para aceder conteúdo das mensagens

# Defina o command_prefix como uma string vazia ou um prefixo que não será usado
bot = commands.Bot(command_prefix='', intents=intents)

# IDs e nomes das salas de voz (constantes)
VOICE_CHANNEL_IDS = [
    int(get_env_variable('VOICE_CHANNEL_1_ID')),
    int(get_env_variable('VOICE_CHANNEL_2_ID')),
    int(get_env_variable('VOICE_CHANNEL_3_ID')),
    int(get_env_variable('VOICE_CHANNEL_4_ID')),
]
VOICE_CHANNEL_NAMES = [
    "Chill Out 1", "Chill Out 2",
    "Studio 1", "Studio 2"
]

# Dicionário para mapear IDs de salas para seus nomes originais
voice_channel_mapping = dict(zip(VOICE_CHANNEL_IDS, VOICE_CHANNEL_NAMES))

# Definir os IDs dos canais como variáveis globais
TEXT_CHANNEL_ID = int(get_env_variable("TEXT_CHANNEL_ID", 0))
MAIN_CHANNEL_ID = int(get_env_variable("MAIN_CHANNEL_ID", 0))
LOGS_CHANNEL_ID = int(get_env_variable("LOGS_CHANNEL_ID", 0))

# Nome do bot (constantes)
BOT_NAME = ["uB|codeBot", "ub|codebot", "codebot", "CodeBot", "CODEBOT"]

# Mensagens estáticas de fallback
STATIC_WELCOME_MESSAGE = "hey... , {member.mention}, bem-vindo/a ao Discord dos **#code.lab**! Para saberes mais sobre nós, passa na sala <#{os.getenv('INFO_CHANNEL_ID')}>"
STATIC_MENTION_RESPONSE = "Olá, disseste o meu nome? Desculpa não poder dar atenção, neste momento estou um pouco ocupado... "

# Lista de linguagens predefinidas para a atividade do bot
GAMES_LIST = ["Python", "Rust", "Java Script", "Visual Studio Code", "PHP"]
GAMES_LIST2 = ["Python", "Rust", "Java Script", "C++", "PHP"]

# Função para gerar mensagem dinâmica com IA
async def generate_ai_message(prompt):
    """Gera uma mensagem usando a API Gemini."""
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Erro ao gerar mensagem com IA: {e}")
        return None

# Função para gerar uma frase curiosa sobre uma linguagem
async def gerar_frase_desafiante():
    """Gera uma frase curiosa sobre uma linguagem aleatória."""
    jogo = random.choice(GAMES_LIST2)  # Escolhe uma linguagem aleatoriamente
    prompt = f"Uma frase curta em português de Portugal, com uma curiosidade ou um facto interessante sobre linguagem de programação {jogo})"
    
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        frase = response.text.strip() if response.text else "Não consegui gerar uma frase."
    except Exception as e:
        logger.error(f"Erro ao gerar frase: {e}")
        frase = "O silêncio na guerra também pode ser uma mensagem."

    return f"🔹***code**Facts*: *{frase}*"

# Função para mudar a atividade do bot para "playing <game>"
async def change_activity_to_game():
    """Muda a atividade do bot para 'playing <game>'."""
    game = random.choice(GAMES_LIST)  # Escolhe um jogo aleatório da lista
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=game))
        logger.info(f"Atividade alterada para 'playing {game}'")
    except Exception as e:
        logger.error(f"Erro ao alterar atividade: {e}")

# Função para retornar à atividade padrão
async def reset_activity():
    """Retorna a atividade do bot para o padrão."""
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="#code.lab"))
        logger.info("Atividade restaurada para 'watching #code.lab'")
    except Exception as e:
        logger.error(f"Erro ao restaurar atividade: {e}")

# Tarefa periódica para mudar a atividade do bot
@tasks.loop(hours=1)
async def change_activity_task():
    """Muda a atividade do bot periodicamente."""
    try:
        await change_activity_to_game()  # Muda para "playing <game>"
        await asyncio.sleep(1200)  # Aguarda 20 minutos (1200 segundos)
        await reset_activity()  # Retorna à atividade padrão
    except Exception as e:
        logger.error(f"Erro na tarefa de mudança de atividade: {e}")
        logger.error(traceback.format_exc())

# Função para renomear salas de voz
async def rename_voice_channel(channel, game):
    """Renomeia uma sala de voz com base no jogo atual do membro."""
    if game:
        try:
            await channel.edit(name=game)
            logger.info(f'Sala {channel.name} renomeada para {game}')
            return True
        except Exception as e:
            logger.error(f"Erro ao renomear sala de voz: {e}")
    return False

# Tarefa periódica para verificar salas de voz
@tasks.loop(minutes=20)
async def check_voice_channels():
    """Verifica se as salas de voz estão vazias e restaura o nome original."""
    try:
        for channel_id in VOICE_CHANNEL_IDS:
            channel = bot.get_channel(channel_id)
            if channel and not channel.members:  # Se a sala estiver vazia
                original_name = voice_channel_mapping.get(channel_id)
                if original_name:
                    await channel.edit(name=original_name)
                    logger.info(f'{channel.name} restaurado ao nome original após verificação.')
    except Exception as e:
        logger.error(f'Erro ao verificar salas de voz: {e}')
        logger.error(traceback.format_exc())

# Tarefa periódica para limpar o canal de atividade
@tasks.loop(minutes=20)
async def cleanup_activity_channel():
    """Mantém apenas os últimos 20 registros no canal activity."""
    try:
        channel = bot.get_channel(TEXT_CHANNEL_ID)
        if channel:
            messages = []
            async for message in channel.history(limit=100):
                messages.append(message)

            if len(messages) > 20:
                for message in messages[20:]:
                    await message.delete()
                logger.info(f'Removidas mensagens antigas no canal activity, mantendo apenas os últimos 20 registros.')
    except Exception as e:
        logger.error(f'Erro ao limpar mensagens antigas: {e}')
        logger.error(traceback.format_exc())

# Função para obter o jogo atual de um membro
def get_current_game(member: discord.Member) -> str:
    """Retorna o jogo que o membro está a jogar, se houver."""
    for activity in member.activities:
        if activity.type == discord.ActivityType.playing:
            logger.info(f'{member.display_name} está a jogar {activity.name}')
            return activity.name
    logger.info(f'{member.display_name} não está a jogar nada.')
    return None

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Evento acionado quando um utilizador entra ou sai de uma sala de voz."""
    try:
        # Entrou em uma sala de voz
        if before.channel is None and after.channel is not None:
            if after.channel.id in VOICE_CHANNEL_IDS:
                game = get_current_game(member)
                if await rename_voice_channel(after.channel, game):
                    text_channel = bot.get_channel(TEXT_CHANNEL_ID)
                    if text_channel:
                        await text_channel.send(f'{member.display_name} iniciou {game} numa sala de voz. Junta-te ao desafio!')

        # Saiu de uma sala de voz
        elif before.channel is not None and after.channel is None:
            if before.channel.id in VOICE_CHANNEL_IDS:
                if not before.channel.members:  # Sala de voz está vazia
                    original_name = voice_channel_mapping.get(before.channel.id)
                    if original_name:
                        await before.channel.edit(name=original_name)
                        logger.info(f'{before.channel.name} voltou ao nome original: {original_name}')

        # Movendo-se entre salas de voz
        elif before.channel is not None and after.channel is not None:
            if after.channel.id in VOICE_CHANNEL_IDS:
                game = get_current_game(member)
                if await rename_voice_channel(after.channel, game):
                    text_channel = bot.get_channel(TEXT_CHANNEL_ID)
                    if text_channel:
                        await text_channel.send(f'{member.display_name} iniciou {game} numa sala de voz. Junta-te ao desafio!')

    except Exception as e:
        logger.error(f'Erro no evento on_voice_state_update: {e} (User: {member.id}, Channel: {after.channel.id if after.channel else None})')
        logger.error(traceback.format_exc())

# Comando de teste: /ping
@bot.tree.command(name="ping", description="Responde com a latência do bot.")
async def ping(interaction: discord.Interaction):
    try:
        latency = bot.latency * 1000  # Converte latência em milissegundos
        await interaction.response.send_message(f'Pong! Latência: {latency:.2f}ms')
    except Exception as e:
        logger.error(f'Erro no comando ping: {e}')
        logger.error(traceback.format_exc())

# Comando de teste: /coin
@bot.tree.command(name="coin", description="Lança uma moeda virtual e responde com o resultado.")
@app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
async def coin(interaction: discord.Interaction):
    try:
        outcome = '**Cara**' if random.randint(0, 1) == 0 else '**Coroa**'
        await interaction.response.send_message(f'A moeda rodou, e caiu em {outcome}')
    except Exception as e:
        logger.error(f'Erro no comando coin: {e}')
        logger.error(traceback.format_exc())

# Comando /send
@bot.tree.command(name="mem", description="Envia uma curiosidade sobre programação na sala lobby.")
async def send(interaction: discord.Interaction):
    """Envia uma curiosidade sobre programação quando o comando /mem é acionado."""
    try:
        channel = bot.get_channel(MAIN_CHANNEL_ID)
        if channel is None:
            logger.error("Erro: Canal não encontrado.")
            await interaction.response.send_message("Erro: Canal não encontrado.", ephemeral=True)
            return
        
        frase = await gerar_frase_desafiante()
        await channel.send(frase)
        await interaction.response.send_message("Frase enviada com sucesso!", ephemeral=True)
    except Exception as e:
        logger.error(f"Erro ao enviar frase enigmática: {e}")
        logger.error(traceback.format_exc())
        await interaction.response.send_message("Ocorreu um erro ao enviar a frase.", ephemeral=True)

# Comando /say
def is_admin(interaction: discord.Interaction) -> bool:
    """Verifica se o utilizador é um administrador."""
    return any(role.id == int(get_env_variable('ADMIN_ROLE_ID')) for role in interaction.user.roles)

class SayModal(discord.ui.Modal, title="Enviar Mensagem Anónima"):
    mensagem = discord.ui.TextInput(label="Mensagem", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        """Envia a mensagem e exibe a view para upload de imagem."""
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
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao processar a mensagem. Tenta novamente mais tarde.",
                ephemeral=True
            )

class UploadView(discord.ui.View):
    def __init__(self, mensagem: str):
        super().__init__(timeout=60)  # Timeout de 60 segundos
        self.mensagem = mensagem
        self.message = None  # Armazena a mensagem que contém a view

    async def send_message(self, interaction: discord.Interaction, file: discord.File = None):
        """Envia a mensagem no canal, com ou sem imagem."""
        if not await has_permissions(interaction.channel, discord.Permissions(send_messages=True)):
            await self.send_feedback(interaction, "❌ O bot não tem permissões para enviar mensagens neste canal.")
            return
        try:
            await interaction.channel.send(content=self.mensagem, file=file)
            await self.send_feedback(interaction, "✅ Mensagem enviada com sucesso!")
        except discord.HTTPException as e:
            await self.send_feedback(interaction, f"❌ Erro ao enviar a mensagem: {str(e)}")

    async def send_feedback(self, interaction: discord.Interaction, content: str):
        """Envia feedback ao utilizador de forma simplificada."""
        try:
            await interaction.followup.send(content, ephemeral=True)
        except discord.HTTPException:
            pass  # Ignora erros de envio de feedback

    @discord.ui.button(label="📤 Upload de Imagem", style=discord.ButtonStyle.primary)
    async def upload_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Permite ao utilizador enviar uma imagem para anexar à mensagem."""
        await interaction.response.send_message(
            "Agora envia a imagem aqui neste chat! Tens 60 segundos.",
            ephemeral=True
        )

        def check(m: discord.Message):
            return m.author == interaction.user and len(m.attachments) > 0

        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            file = await msg.attachments[0].to_file()

            if msg.channel.permissions_for(msg.guild.me).manage_messages:
                await msg.delete()

            await self.send_message(interaction, file=file)

        except discord.Forbidden:
            await self.send_feedback(interaction, "❌ O bot não tem permissões para apagar mensagens.")
        except discord.HTTPException as e:
            await self.send_feedback(interaction, f"❌ Erro ao processar a imagem: {str(e)}")
        except asyncio.TimeoutError:
            await self.send_feedback(interaction, "❌ O tempo para enviar a imagem expirou.")

    @discord.ui.button(label="📨 Enviar Sem Imagem", style=discord.ButtonStyle.secondary)
    async def send_text_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Envia apenas o texto se o utilizador não quiser adicionar uma imagem."""
        await interaction.response.defer(ephemeral=True)  # Evita erros de interação
        await self.send_message(interaction)  # Envia apenas o texto
        self.stop()  # Encerra a view

    async def on_timeout(self):
        """Método chamado quando o timeout da view é atingido."""
        if self.message:  # Verifica se o atributo message existe
            await self.message.edit(content="❌ Tempo esgotado. Ação cancelada.", view=None)

@bot.tree.command(name="say", description="Envia uma mensagem anonimamente")
@app_commands.check(is_admin)  # Aplica a verificação de permissões diretamente
async def say(interaction: discord.Interaction):
    """Abre um modal para o admin escrever a mensagem."""
    await interaction.response.send_modal(SayModal())

@say.error
async def say_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Trata erros de permissão no comando /say."""
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)

@bot.event
async def on_ready():
    """Evento acionado quando o bot está pronto para uso."""
    logger.info(f'Bot conectado como {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="#code.lab"))

    # Sincronizar comandos de aplicação (slash commands)
    try:
        synced = await bot.tree.sync()
        logger.info(f'Sincronizados {len(synced)} comandos de aplicação')
        logger.info(f'Comandos sincronizados: {[cmd.name for cmd in synced]}')  # Lista os comandos sincronizados
    except Exception as e:
        logger.error(f'Erro ao sincronizar comandos de aplicação: {e}')
        logger.error(traceback.format_exc())
    
    # Iniciar as tarefas de verificação periódica das salas de voz
    try:
        if not check_voice_channels.is_running():  # Verifica se a tarefa já está em execução
            check_voice_channels.start()
        if not cleanup_activity_channel.is_running():  # Verifica se a tarefa já está em execução
            cleanup_activity_channel.start()
        if not change_activity_task.is_running():  # Verifica se a tarefa já está em execução
            change_activity_task.start()
        logger.info("Tarefas periódicas iniciadas.")
    except Exception as e:
        logger.error(f'Erro ao iniciar tarefas periódicas: {e}')
        logger.error(traceback.format_exc())

@bot.event
async def on_message(message):
    """Evento acionado quando uma mensagem é enviada."""
    if message.author.bot:
        return  # Ignorar mensagens de outros bots

    content = message.content.lower()

    # Verifica se o bot foi mencionado oficialmente ou se o nome do bot está na mensagem
    if bot.user.mentioned_in(message) or any(name in content for name in BOT_NAME):
        prompt = f"imagina-te o codeBot, mestre da progamação, membro principal do **#code.lab**, e dá uma pequena resposta em português de Portugal à mensagem de {message.author.name}: {message.content}"
        ai_message = await generate_ai_message(prompt)
        if ai_message:
            await message.channel.send(ai_message)
        else:
            await message.channel.send(STATIC_MENTION_RESPONSE)

@bot.event
async def on_member_join(member):
    """Evento acionado quando um novo membro entra no servidor e envia uma mensagem pública na sala Lobby e no canal de logs."""
    
    # Enviar mensagem na sala principal (Lobby)
    channel = bot.get_channel(MAIN_CHANNEL_ID)
    if channel:
        prompt = (
            f"imagina-te o codeBot, mestre da programação. Escreve uma pequena frase de bem vindo/a em português de Portugal, a tratar por tu, como neste exemplo:'Olá , {member.mention}, bem-vindo/a ao Discord dos **#code.lab**! Para saberes mais sobre nós, passa na sala <#{os.getenv('INFO_CHANNEL_ID')}>.'"
        )
        ai_message = await generate_ai_message(prompt)
        
        # Mensagem padrão caso a IA falhe
        default_message = (
            f"Hey... {member.mention}, bem-vindo/a ao Discord dos **#code.lab**! "
            f"Para saberes mais sobre nós, passa na sala <#{os.getenv('INFO_CHANNEL_ID')}>."
        )
        await channel.send(ai_message if ai_message else default_message)
    else:
        logger.error(f"Canal Lobby ({MAIN_CHANNEL_ID}) não encontrado.")

    # Enviar mensagem na sala de logs
    log_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"🔹 O utilizador **{member.name}** entrou no servidor.")
    else:
        logger.error(f"Canal de logs ({LOGS_CHANNEL_ID}) não encontrado.")

@bot.event
async def on_member_remove(member):
    """Evento acionado quando um membro sai do servidor e envia uma mensagem na sala de logs."""
    
    log_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"🔸 O utilizador **{member.name}** saiu do servidor.")
    else:
        logger.error(f"Canal de logs ({LOGS_CHANNEL_ID}) não encontrado.")

# Inicie o bot com o token
bot.run(get_env_variable('DISCORD_TOKEN'))  # Use variáveis de ambiente para o token
