# Bot Consultor de Multas

Bot de automação RPA integrado ao Telegram para consulta de multas e emissão de documentos relacionados ao RENAVAM.

O projeto utiliza **Python**, **Playwright** e **Telegram Bot** para automatizar o acesso ao sistema web, consultar informações de multas, baixar documentos e enviar o resultado diretamente ao usuário pelo Telegram.

> Este projeto é educacional e não possui vínculo oficial com órgãos de trânsito.

---

## Funcionalidades

- Consulta de multas por RENAVAM
- Emissão de Certidão Negativa de Multas
- Identificação de multa em prazo de defesa
- Download da Notificação de Autuação
- Envio de print da tela da multa pelo Telegram
- Envio do PDF gerado pelo Telegram
- Exclusão automática dos arquivos locais após o envio
- Execução local no computador do usuário
- Integração com bot do Telegram

---

## Tecnologias utilizadas

- Python
- Playwright
- python-telegram-bot
- python-dotenv
- Telegram Bot API

---

## Como funciona

O usuário inicia o bot no Telegram com o comando:

```text
/start
