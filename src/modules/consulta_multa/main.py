import os
import re
import time
import shutil
from pathlib import Path
from datetime import datetime

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


def localizar_botao_imprimir_na(page):
    seletores = [
        page.get_by_role("button", name=re.compile(r"imprimir\s*na", re.I)),
        page.get_by_role("link", name=re.compile(r"imprimir\s*na", re.I)),
        page.get_by_text(re.compile(r"imprimir\s*na", re.I)),
        page.locator("button").filter(has_text=re.compile(r"imprimir\s*na", re.I)),
        page.locator("a").filter(has_text=re.compile(r"imprimir\s*na", re.I)),
    ]

    for seletor in seletores:
        try:
            if seletor.count() > 0:
                seletor.first.wait_for(state="visible", timeout=5000)
                return seletor.first
        except Exception:
            pass

    return None


def mover_pdf_baixado_recente(nome_pdf_destino, inicio_download, timeout=40):
    """
    Procura o PDF mais recente na pasta Downloads e move para output/
    com o nome correto.
    """
    pasta_downloads = Path.home() / "Downloads"
    destino = Path(nome_pdf_destino)

    fim = time.time() + timeout

    while time.time() < fim:
        pdfs = []

        if pasta_downloads.exists():
            for arquivo in pasta_downloads.glob("*.pdf"):
                try:
                    if arquivo.stat().st_mtime >= inicio_download - 2:
                        pdfs.append(arquivo)
                except Exception:
                    pass

        if pdfs:
            pdf_mais_recente = max(pdfs, key=lambda arq: arq.stat().st_mtime)

            try:
                destino.parent.mkdir(parents=True, exist_ok=True)

                if destino.exists():
                    destino.unlink()

                shutil.move(str(pdf_mais_recente), str(destino))
                return True

            except PermissionError:
                time.sleep(1)

            except Exception as erro:
                print(f"Erro ao mover PDF baixado: {erro}")
                return False

        time.sleep(1)

    return False


def consultar_multas(page, renavam):
    print("\nIniciando consulta de multas...")

    os.makedirs("output", exist_ok=True)

    page.locator("div").filter(
        has_text="Consulta e Pagamento de Multas"
    ).nth(5).click()

    page.get_by_role("button", name="Renavam").click()

    campo_renavam = page.get_by_role(
        "textbox",
        name="Insira um Renavam, Ex.:"
    )

    campo_renavam.click()
    campo_renavam.fill(renavam)
    campo_renavam.press("Enter")

    page.get_by_role("button", name="Continuar").click()

    tabela = page.get_by_role("table")
    tabela.wait_for(state="visible", timeout=30000)

    try:
        page.locator("table tbody tr").first.click()
    except Exception:
        tabela.click()

    page.wait_for_timeout(1500)

    nome_print = f"output/print_multa_{renavam}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    page.screenshot(path=nome_print, full_page=True)

    print(f"Print da multa salvo em: {nome_print}")

    botao_imprimir_na = localizar_botao_imprimir_na(page)

    if botao_imprimir_na is None:
        return {
            "status": "sem_na",
            "mensagem": "Consulta finalizada, mas o botão 'Imprimir NA' não foi encontrado.",
            "print": nome_print,
            "pdf": None
        }

    nome_pdf = f"output/notificacao_autuacao_{renavam}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    inicio_download = time.time()

    try:
        with page.expect_download(timeout=20000) as download_info:
            botao_imprimir_na.click()

        download = download_info.value
        download.save_as(nome_pdf)

        print(f"PDF da NA salvo corretamente em: {nome_pdf}")

        return {
            "status": "na",
            "mensagem": "Multa encontrada em prazo de defesa. Notificação de Autuação baixada com sucesso.",
            "print": nome_print,
            "pdf": nome_pdf
        }

    except PlaywrightTimeoutError:
        print("Playwright não capturou o download diretamente.")
        print("Tentando localizar o PDF baixado na pasta Downloads...")

    baixou = mover_pdf_baixado_recente(nome_pdf, inicio_download, timeout=40)

    if baixou:
        print(f"PDF encontrado na pasta Downloads e renomeado para: {nome_pdf}")

        return {
            "status": "na",
            "mensagem": "Multa encontrada em prazo de defesa. Notificação de Autuação baixada com sucesso.",
            "print": nome_print,
            "pdf": nome_pdf
        }

    return {
        "status": "erro_pdf",
        "mensagem": "A NA foi solicitada, mas não consegui localizar o PDF baixado.",
        "print": nome_print,
        "pdf": None
    }