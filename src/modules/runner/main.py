import os
from datetime import datetime
from playwright.sync_api import sync_playwright

from src.modules.open_site.main import abrir_site
from src.modules.consulta_multa.main import consultar_multas
from src.modules.certidao_negativa.main import emitir_certidao_negativa


def criar_pasta_output():
    os.makedirs("output", exist_ok=True)


def executar_automacao(tipo: str, renavam: str):
    criar_pasta_output()

    with sync_playwright() as playwright:
        browser, context, page = abrir_site(playwright)

        try:
            if tipo == "consulta_multa":
                resultado_consulta = consultar_multas(page, renavam)

                arquivos = []

                if resultado_consulta.get("print"):
                    arquivos.append({
                        "caminho": resultado_consulta["print"],
                        "tipo": "imagem"
                    })

                if resultado_consulta.get("pdf"):
                    arquivos.append({
                        "caminho": resultado_consulta["pdf"],
                        "tipo": "pdf"
                    })

                return {
                    "ok": True,
                    "mensagem": resultado_consulta["mensagem"],
                    "arquivos": arquivos
                }

            elif tipo == "certidao_negativa":
                arquivo_pdf = emitir_certidao_negativa(page, renavam)

                arquivos = []

                if arquivo_pdf:
                    arquivos.append({
                        "caminho": arquivo_pdf,
                        "tipo": "pdf"
                    })

                return {
                    "ok": True,
                    "mensagem": "Certidão negativa emitida com sucesso.",
                    "arquivos": arquivos
                }

            else:
                return {
                    "ok": False,
                    "mensagem": "Tipo de automação inválido.",
                    "arquivos": []
                }

        except Exception as erro:
            nome_erro = f"output/erro_{renavam}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            arquivos = []

            try:
                page.screenshot(path=nome_erro, full_page=True)
                arquivos.append({
                    "caminho": nome_erro,
                    "tipo": "imagem"
                })
            except Exception:
                pass

            return {
                "ok": False,
                "mensagem": f"Erro durante a automação: {erro}",
                "arquivos": arquivos
            }

        finally:
            context.close()
            browser.close()