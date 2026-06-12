import os
from dotenv import load_dotenv
from modulos.extrator_maps import ExtratorMaps
from modulos.filtro_dados import FiltroDados
from modulos.planilhas import PlanilhasGoogle
from playwright.sync_api import sync_playwright

# Carrega as variáveis do arquivo .env
load_dotenv()

# Lê de variável de ambiente ou assume 50 por padrão
MAX_LEADS_DIARIOS = int(os.getenv("MAX_LEADS", 50))

def main():
    print("Iniciando Orquestrador - Bot de Barbearias")
    
    # Inicializa "Órgãos" Determinísticos
    sheets = PlanilhasGoogle()
    maps = ExtratorMaps()
    filtros = FiltroDados()
    
    # Reconhecimento: Memoriza telefones para não repetir
    telefones_existentes = sheets.obter_telefones_existentes()
    
    contador = 0
    # Lê de variável de ambiente ou assume 'Barbearias em São Paulo' por padrão
    termo_busca = os.getenv("TERMO_BUSCA", "Barbearias em São Paulo")
    
    print(f"Iniciando Navegador Playwright...")
    with sync_playwright() as p:
        # Abre o navegador (coloque headless=False para ver ele rodando)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="pt-BR")
        page = context.new_page()
        
        # Caçada: Inicia extração
        # O extrator maps é um Generator (yield) que vai rolar a página infinitamente
        for dados_brutos in maps.navegar_e_extrair(page, termo_busca):
            if contador >= MAX_LEADS_DIARIOS:
                print(f"Meta atingida ({MAX_LEADS_DIARIOS}). Encerrando bot gentilmente.")
                break
                
            # Triagem: Passa pela regra do WhatsApp/Gmail
            # Passamos o 'context' para que o filtro possa abrir uma nova aba
            lead_validado = filtros.triagem(dados_brutos, context)
            
            if not lead_validado:
                nome_seguro = dados_brutos.get('nome', '').encode('ascii', 'ignore').decode()
                print(f"[-] Descartado (Sem WhatsApp no Maps/Site): {nome_seguro}")
                continue
                
            # Anti-Duplicação
            if lead_validado["whatsapp"] in telefones_existentes:
                nome_seguro = lead_validado['nome'].encode('ascii', 'ignore').decode()
                print(f"[-] Duplicado (Já existe no Sheets): {nome_seguro}")
                continue
                
            # Registro: Grava no Sheets
            sucesso = sheets.salvar_lead(lead_validado)
            if sucesso:
                # Atualiza cache para evitar dup em tempo de execução
                telefones_existentes.append(lead_validado["whatsapp"])
                contador += 1
                nome_seguro = lead_validado['nome'].encode('ascii', 'ignore').decode()
                whatsapp = lead_validado['whatsapp']
                gmail = lead_validado.get('gmail', 'N/A') or 'N/A'
                site = lead_validado.get('site', 'N/A') or 'N/A'
                print(f"[+] SUCESSO ({contador}/{MAX_LEADS_DIARIOS}): {nome_seguro} | ZAP: {whatsapp} | GMAIL: {gmail} | SITE: {site}")
        
        # Finaliza navegador
        print("Fechando navegador.")
        browser.close()

if __name__ == "__main__":
    main()
