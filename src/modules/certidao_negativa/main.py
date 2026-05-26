import os
from datetime import datetime


def emitir_certidao_negativa(page, renavam):
    print("\nIniciando emissão da certidão negativa...")

    page.locator("div").filter(
        has_text="Certidão Negativa de Multas"
    ).nth(5).click()

    page.get_by_role("button", name="Renavam").click()

    campo_renavam = page.get_by_role(
        "textbox",
        name="Insira um Renavam, Ex.:"
    )

    campo_renavam.click()
    campo_renavam.fill(renavam)

    page.get_by_role("button", name="Continuar").click()

    os.makedirs("output", exist_ok=True)

    nome_arquivo = f"output/certidao_negativa_{renavam}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    with page.expect_download() as download_info:
        page.get_by_role("button", name="Imprimir").click()

    download = download_info.value
    download.save_as(nome_arquivo)

    print(f"Certidão negativa baixada como: {nome_arquivo}")

    return nome_arquivo