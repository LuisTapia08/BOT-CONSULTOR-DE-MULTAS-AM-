import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from src.modules.runner.main import executar_automacao


BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot_em_execucao = asyncio.Lock()


def apagar_arquivo_local(caminho):
    try:
        if caminho and os.path.exists(caminho):
            os.remove(caminho)
            print(f"Arquivo apagado do PC: {caminho}")
    except Exception as erro:
        print(f"Não consegui apagar o arquivo {caminho}: {erro}")


def obter_legenda_pdf(caminho):
    nome_arquivo = os.path.basename(caminho).lower()

    if "boleto" in nome_arquivo:
        return "Boleto/Pix da multa"

    if "notificacao_autuacao" in nome_arquivo:
        return "Notificação de Autuação"

    if "certidao" in nome_arquivo:
        return "Certidão negativa de multas"

    return "Documento gerado"


def obter_legenda_imagem(caminho):
    nome_arquivo = os.path.basename(caminho).lower()

    if "erro" in nome_arquivo:
        return "Print do erro encontrado"

    if "sem_multa" in nome_arquivo:
        return "O veículo em questão não possui multas"

    if "nip" in nome_arquivo:
        return "Informações da multa NIP"

    return "Informações da multa"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Consultar multas", callback_data="consulta_multa")],
        [InlineKeyboardButton("Certidão negativa de multas", callback_data="certidao_negativa")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Olá! Escolha uma opção:",
        reply_markup=reply_markup
    )


async def escolher_opcao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    opcao = query.data
    context.user_data["opcao"] = opcao

    if opcao == "consulta_multa":
        texto = "Você escolheu: Consultar multas.\n\nDigite o RENAVAM:"
    else:
        texto = "Você escolheu: Certidão negativa de multas.\n\nDigite o RENAVAM:"

    await query.edit_message_text(texto)


async def enviar_arquivos(update: Update, arquivos, legenda_imagem_principal=None):
    if not arquivos:
        return

    legenda_principal_usada = False

    for item in arquivos:
        caminho = item.get("caminho")
        tipo = item.get("tipo")

        if not caminho:
            continue

        if not os.path.exists(caminho):
            print(f"Arquivo não encontrado para envio: {caminho}")
            await update.message.reply_text(
                f"Arquivo gerado, mas não encontrado no PC: {caminho}"
            )
            continue

        try:
            if tipo == "pdf":
                legenda = obter_legenda_pdf(caminho)

                with open(caminho, "rb") as documento:
                    await update.message.reply_document(
                        document=documento,
                        caption=legenda
                    )

                apagar_arquivo_local(caminho)

            elif tipo == "imagem":
                if legenda_imagem_principal and not legenda_principal_usada:
                    legenda = legenda_imagem_principal
                    legenda_principal_usada = True
                else:
                    legenda = obter_legenda_imagem(caminho)

                with open(caminho, "rb") as imagem:
                    await update.message.reply_photo(
                        photo=imagem,
                        caption=legenda
                    )

                apagar_arquivo_local(caminho)

            else:
                print(f"Tipo de arquivo desconhecido: {tipo}")

        except Exception as erro:
            print(f"Erro ao enviar ou apagar arquivo: {erro}")
            await update.message.reply_text(
                "Ocorreu um erro ao enviar um dos arquivos."
            )


async def receber_renavam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opcao = context.user_data.get("opcao")

    if not opcao:
        await update.message.reply_text(
            "Primeiro escolha uma opção usando /start."
        )
        return

    renavam = update.message.text.strip()

    if not renavam.isdigit():
        await update.message.reply_text(
            "RENAVAM inválido. Digite apenas números."
        )
        return

    if bot_em_execucao.locked():
        await update.message.reply_text(
            "Já existe uma consulta em andamento. Aguarde terminar."
        )
        return

    await update.message.reply_text(
        f"Recebi o RENAVAM {renavam}.\nIniciando automação no computador local..."
    )

    async with bot_em_execucao:
        resultado = await asyncio.to_thread(
            executar_automacao,
            opcao,
            renavam
        )

    print("Resultado da automação:", resultado)
    print("Arquivos para envio:", resultado.get("arquivos", []))

    arquivos = resultado.get("arquivos", [])
    possui_imagem = any(
        item.get("tipo") == "imagem"
        for item in arquivos
    )

    if possui_imagem:
        await enviar_arquivos(
            update,
            arquivos,
            legenda_imagem_principal=resultado["mensagem"]
        )
    else:
        await update.message.reply_text(resultado["mensagem"])
        await enviar_arquivos(update, arquivos)

    context.user_data.clear()

    await update.message.reply_text(
        "Para fazer outra consulta, envie /start."
    )


def iniciar_bot():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN não encontrado no arquivo .env")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(escolher_opcao))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_renavam))

    print("Bot do Telegram iniciado.")
    print("Envie /start no Telegram para começar.")

    app.run_polling()
