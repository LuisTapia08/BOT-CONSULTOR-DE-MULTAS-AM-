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

- Python 3.14
- Playwright
- python-telegram-bot
- python-dotenv
- PyAutoGUI
- OpenCV
- Telegram Bot API

## Requisitos

- Windows com sessão gráfica ativa
- Python 3.14 instalado e disponível no terminal
- Google Chromium instalado pelo Playwright
- Token de bot do Telegram

> A automação usa navegador visível e recursos de tela. Por isso, ela deve rodar em um computador com área de trabalho desbloqueada.

## Instalação do ambiente

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Se o comando `python` não existir, confirme se o Python 3.14 está no PATH e abra um novo terminal. O terminal precisa enxergar `python --version` antes da criação da `.venv`.

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
TELEGRAM_TOKEN=seu_token_do_telegram
```

O arquivo `.env` não deve ser versionado.

## Executando

Com o ambiente virtual ativado:

```powershell
python main.py
```

No Telegram, inicie o bot com:

```text
/start
```

## Dependências

As dependências diretas ficam em `requirements.in`.

O arquivo `requirements.txt` é o arquivo travado, com dependências diretas e transitivas usadas para instalar o ambiente de forma reproduzível.

Para atualizar o arquivo travado:

```powershell
python -m pip install pip-tools
pip-compile requirements.in -o requirements.txt
```

Depois de atualizar dependências do Playwright, reinstale o navegador:

```powershell
python -m playwright install chromium
```

## Observações operacionais

- A pasta `output/` guarda arquivos temporários gerados durante a execução.
- A pasta `.venv/` guarda o ambiente virtual local e não deve ser versionada.
- A pasta `assets/` contém imagens usadas pela automação visual.
- Se a interface do portal mudar, seletores e imagens de automação podem precisar de atualização.
