# codeBot - Discord by Shadowչ (x.coder)

Um bot para Discord desenvolvido em Python usando a biblioteca `discord.py`. O bot oferece funcionalidades como envio de mensagens anónimas, integração com AI (Gemini API, ou outras), salas de voz dinâmicas, e muito mais.

**Discord #code.lab** ( Live demo - https://discord.gg/2js9vZMPF3 )

## Funcionalidades Principais

- **Gerenciamento de Salas de Voz**: Salas de voz dinâmicas. Renomeia salas de voz automaticamente com base na actividade dos utilizadores (activity).
- **Envio de Mensagens Anónimas**: Administradores podem enviar mensagens anónimas em nome do bot, com ou sem anexos de imagem.
- **Integração com IA**: Responde a mensagens quando o nome do bot é referido, usando a API do Gemini (ou outra) para gerar respostas dinâmicas.
- **Comandos de Moderação**: Inclui comandos como `ping` e `coin` para interação básica.
- **Atividades Periódicas**: Muda a atividade do bot periodicamente para manter o servidor mais dinâmico.
- **Envio de frases curiosas**: Envia frase com dicas sobre linguagens de programação (ou outros temas definidos).
- **Mensagem de bem-vindo**: Envia mensagem de bem-vindo a novos membros.
- **Mensagens de actividade e logs**: Envia mensagens de log para os canais específicos.

## Como Usar

1. **Configuração**:
   - Clone este repositório:
     ```bash
     git clone https://github.com/x-coder8/codeBot-Discord.git
     ```
   - Instale as Bibliotecas necessárias

   - Configure as variáveis de ambiente no arquivo `.env` (veja `.env.example` para referência).

2. **Executando o Bot**:
   - Execute o bot com o comando:
     ```bash
     python codeBot.py
     ```

3. **Comandos Disponíveis**:
   - `/ping`: Verifica a latência do bot.
   - `/coin`: Lança uma moeda virtual e retorna como cara ou coroa.
   - `/tips`: Envia uma frase com dicas técnicas sobre um tema, gerada por AI.
   - `/say`: Envia uma mensagem anónima, com ou sem anexos de imagem. (apenas para administradores).

## Requisitos

- Python 3.8 ou superior.
- Bibliotecas: `discord.py`, `python-dotenv`, `google-generativeai`.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
