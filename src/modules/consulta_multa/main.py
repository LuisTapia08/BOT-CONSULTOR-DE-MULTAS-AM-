import os
import re
import time
import shutil
import pyautogui
from pathlib import Path
from datetime import datetime

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT = BASE_DIR / "output"
ASSETS = BASE_DIR / "assets"


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


def existe_multa_nip(page):
    try:
        celula_nip = page.get_by_role("cell", name=re.compile(r"^NIP$", re.I))
        return celula_nip.count() > 0
    except Exception:
        return False


def localizar_mensagem_sem_multas(page):
    mensagem_sem_multas = re.compile(
        r"não\s+h[áa]\s+notifica[cç][õo]es\s+a\s+serem\s+emitidas",
        re.I
    )

    seletores = [
        page.get_by_text(mensagem_sem_multas),
        page.locator("text=/não\\s+h[áa]\\s+notifica[cç][õo]es\\s+a\\s+serem\\s+emitidas/i"),
    ]

    for seletor in seletores:
        try:
            if seletor.count() > 0 and seletor.first.is_visible():
                return seletor.first
        except Exception:
            pass

    return None


def aguardar_resultado_consulta(page, timeout=30000):
    fim = time.time() + timeout / 1000
    tabela = page.get_by_role("table")

    while time.time() < fim:
        try:
            if tabela.count() > 0 and tabela.first.is_visible():
                return "tabela", tabela.first
        except Exception:
            pass

        mensagem_sem_multas = localizar_mensagem_sem_multas(page)

        if mensagem_sem_multas is not None:
            return "sem_multas", mensagem_sem_multas

        time.sleep(0.5)

    tabela.wait_for(state="visible", timeout=1000)
    return "tabela", tabela.first


def arquivo_esta_pronto(arquivo):
    try:
        tamanho_1 = arquivo.stat().st_size
        time.sleep(1)
        tamanho_2 = arquivo.stat().st_size

        return tamanho_1 == tamanho_2 and tamanho_2 > 0
    except Exception:
        return False


def mover_pdf_baixado_recente(nome_pdf_destino, inicio_download, timeout=60):
    pasta_downloads = Path.home() / "Downloads"
    destino = Path(nome_pdf_destino)

    fim = time.time() + timeout

    extensoes_temporarias = [
        ".crdownload",
        ".tmp",
        ".download",
        ".part"
    ]

    while time.time() < fim:
        arquivos_recentes = []

        if pasta_downloads.exists():
            for arquivo in pasta_downloads.glob("*"):
                try:
                    if not arquivo.is_file():
                        continue

                    nome_minusculo = arquivo.name.lower()
                    extensao = arquivo.suffix.lower()

                    if extensao in extensoes_temporarias:
                        continue

                    if nome_minusculo.endswith(".crdownload"):
                        continue

                    if "unconfirmed" in nome_minusculo:
                        continue

                    if arquivo.stat().st_mtime >= inicio_download - 2:
                        arquivos_recentes.append(arquivo)

                except Exception:
                    pass

        if arquivos_recentes:
            arquivo_mais_recente = max(
                arquivos_recentes,
                key=lambda arq: arq.stat().st_mtime
            )

            if not arquivo_esta_pronto(arquivo_mais_recente):
                time.sleep(1)
                continue

            try:
                destino.parent.mkdir(parents=True, exist_ok=True)

                if destino.exists():
                    destino.unlink()

                shutil.move(str(arquivo_mais_recente), str(destino))

                print(f"Arquivo baixado movido para: {destino}")
                return True

            except PermissionError:
                time.sleep(1)

            except Exception as erro:
                print(f"Erro ao mover arquivo baixado: {erro}")
                return False

        time.sleep(1)

    return False


def clicar_boleto_com_pyautogui():
    imagem_botao = ASSETS / "pagar_multa.png"

    if not imagem_botao.exists():
        print(f"Imagem do botão não encontrada: {imagem_botao}")
        return False

    print(f"Procurando botão pela imagem: {imagem_botao}")

    confidences = [0.9, 0.85, 0.8, 0.75, 0.7]

    for confidence in confidences:
        fim = time.time() + 12

        while time.time() < fim:
            try:
                posicao = pyautogui.locateCenterOnScreen(
                    str(imagem_botao),
                    confidence=confidence
                )

                if posicao:
                    print(f"Botão encontrado em {posicao} com confidence {confidence}")
                    pyautogui.moveTo(posicao.x, posicao.y, duration=0.2)
                    pyautogui.click()
                    return True

            except pyautogui.ImageNotFoundException:
                pass

            except Exception as erro:
                print(f"Erro procurando imagem do botão: {erro}")

            time.sleep(0.5)

    print("Não consegui encontrar o botão Pagar com boleto/pix pela imagem.")
    return False


def gerar_boleto_nip(page, renavam):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    nome_print = OUTPUT / f"print_multa_nip_{renavam}_{timestamp}.png"
    nome_pdf = OUTPUT / f"boleto_multa_{renavam}_{timestamp}.pdf"

    print("Multa NIP encontrada. Abrindo detalhes...")

    try:
        celula_nip = page.get_by_role("cell", name=re.compile(r"^NIP$", re.I)).first
        celula_nip.wait_for(state="visible", timeout=10000)
        celula_nip.click()
    except Exception:
        print("Não consegui clicar diretamente na célula NIP. Tentando clicar na primeira linha.")
        page.locator("table tbody tr").first.click()

    page.wait_for_timeout(2000)

    page.screenshot(path=str(nome_print), full_page=True)
    print(f"Print da multa NIP salvo em: {nome_print}")

    try:
        page.bring_to_front()
    except Exception:
        pass

    inicio_download = time.time()

    clicou = clicar_boleto_com_pyautogui()

    if not clicou:
        return {
            "status": "erro_boleto",
            "mensagem": "Multa NIP encontrada, mas não consegui clicar no botão Pagar com boleto/pix pela imagem.",
            "print": str(nome_print),
            "pdf": None
        }

    print("Clique no botão realizado. Aguardando download do boleto...")

    baixou = mover_pdf_baixado_recente(str(nome_pdf), inicio_download, timeout=60)

    if baixou:
        print(f"Boleto encontrado e movido para: {nome_pdf}")

        return {
            "status": "boleto",
            "mensagem": "Multa NIP encontrada. Boleto/Pix baixado com sucesso.",
            "print": str(nome_print),
            "pdf": str(nome_pdf)
        }

    return {
        "status": "erro_boleto",
        "mensagem": "Multa NIP encontrada, cliquei no botão, mas não consegui localizar o PDF do boleto baixado.",
        "print": str(nome_print),
        "pdf": None
    }


def consultar_multas(page, renavam):
    print("\nIniciando consulta de multas...")

    OUTPUT.mkdir(parents=True, exist_ok=True)

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

    tipo_resultado, tabela = aguardar_resultado_consulta(page)

    if tipo_resultado == "sem_multas":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_print = OUTPUT / f"print_sem_multa_{renavam}_{timestamp}.png"
        page.screenshot(path=str(nome_print), full_page=True)

        print(f"Consulta sem multas. Print salvo em: {nome_print}")

        return {
            "status": "sem_multas",
            "mensagem": "O veículo em questão não possui multas.",
            "print": str(nome_print),
            "pdf": None
        }

    if existe_multa_nip(page):
        return gerar_boleto_nip(page, renavam)

    try:
        page.locator("table tbody tr").first.click()
    except Exception:
        tabela.click()

    page.wait_for_timeout(1500)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    nome_print = OUTPUT / f"print_multa_{renavam}_{timestamp}.png"
    page.screenshot(path=str(nome_print), full_page=True)

    print(f"Print da multa salvo em: {nome_print}")

    botao_imprimir_na = localizar_botao_imprimir_na(page)

    if botao_imprimir_na is None:
        return {
            "status": "sem_na",
            "mensagem": "Consulta finalizada, mas o botão 'Imprimir NA' não foi encontrado.",
            "print": str(nome_print),
            "pdf": None
        }

    nome_pdf = OUTPUT / f"notificacao_autuacao_{renavam}_{timestamp}.pdf"

    inicio_download = time.time()

    try:
        with page.expect_download(timeout=20000) as download_info:
            botao_imprimir_na.click()

        download = download_info.value
        download.save_as(str(nome_pdf))

        print(f"PDF da NA salvo corretamente em: {nome_pdf}")

        return {
            "status": "na",
            "mensagem": "Multa encontrada em prazo de defesa. Notificação de Autuação baixada com sucesso.",
            "print": str(nome_print),
            "pdf": str(nome_pdf)
        }

    except PlaywrightTimeoutError:
        print("Playwright não capturou o download diretamente.")
        print("Tentando localizar o PDF baixado na pasta Downloads...")

    except Exception as erro:
        print(f"Erro ao baixar NA diretamente: {erro}")
        print("Tentando localizar o PDF baixado na pasta Downloads...")

    baixou = mover_pdf_baixado_recente(str(nome_pdf), inicio_download, timeout=40)

    if baixou:
        print(f"PDF encontrado na pasta Downloads e renomeado para: {nome_pdf}")

        return {
            "status": "na",
            "mensagem": "Multa encontrada em prazo de defesa. Notificação de Autuação baixada com sucesso.",
            "print": str(nome_print),
            "pdf": str(nome_pdf)
        }

    return {
        "status": "erro_pdf",
        "mensagem": "A NA foi solicitada, mas não consegui localizar o PDF baixado.",
        "print": str(nome_print),
        "pdf": None
    }
