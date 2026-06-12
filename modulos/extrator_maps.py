from typing import Dict, Any, Generator
from playwright.sync_api import Page, Locator
import time
import random

class ExtratorMaps:
    def __init__(self):
        """
        Módulo focado exclusivamente na extração do Google Maps.
        A navegação recebe uma aba (Page) injetada pelo Orquestrador.
        """
        pass

    def navegar_e_extrair(self, page: Page, termo_busca: str) -> Generator[Dict[str, Any], None, None]:
        """
        Acessa o Maps, busca o termo, e gera (yield) um dicionário bruto
        por cada local encontrado na barra lateral (feed).
        """
        print(f"Iniciando busca no Google Maps por: {termo_busca}")
        url = f"https://www.google.com/maps/search/{termo_busca.replace(' ', '+')}"
        
        page.goto(url)
        time.sleep(random.uniform(3.0, 5.0)) # Tempo para carregar a página
        
        # O Google Maps usa um elemento com role="feed" para a lista de resultados
        # Precisamos fazer scroll nele para carregar os itens
        
        feed_selector = "div[role='feed']"
        try:
            page.wait_for_selector(feed_selector, timeout=10000)
        except Exception:
            print("Não foi possível encontrar a lista de resultados. Talvez o Maps mudou a interface.")
            return

        locais_processados = set()
        
        # Loop de scroll infinito (controlado pelo orquestrador através do yield)
        while True:
            # Pega todos os itens visíveis no momento (role='article' ou 'a' com links para locais)
            # A classe principal de itens geralmente tem href começando com /maps/place/
            itens: list[Locator] = page.locator("a[href*='/maps/place/']").all()
            
            novos_itens_encontrados = False
            
            for item in itens:
                link = item.get_attribute("href")
                if link in locais_processados:
                    continue
                
                locais_processados.add(link)
                novos_itens_encontrados = True
                
                # Scroll até o elemento para garantir que ele carregou e imitar humano
                try:
                    item.scroll_into_view_if_needed()
                    time.sleep(random.uniform(0.5, 1.5))
                except:
                    continue
                
                # Clica no item para abrir o painel lateral com detalhes (Telefone, Site)
                try:
                    item.click()
                    time.sleep(random.uniform(2.0, 4.0)) # Tempo para abrir o painel esquerdo
                    
                    # Extrair nome (geralmente h1)
                    # O primeiro h1 pode ser "Resultados", então pegamos a classe do título da empresa
                    nome_locator = page.locator("h1.fontHeadlineLarge").first
                    if nome_locator.count() == 0:
                        nome_locator = page.locator("h1").last
                    nome = nome_locator.inner_text() if nome_locator.count() > 0 else "Sem Nome"
                    
                    # Extrair telefone (botão com data-item-id='phone:tel:')
                    # Usa regex seletor ou botão contendo ícone de telefone
                    telefone_locator = page.locator("button[data-tooltip='Copiar número de telefone']").first
                    telefone = telefone_locator.inner_text() if telefone_locator.count() > 0 else ""
                    
                    # Extrair site (botão contendo link externo)
                    site_locator = page.locator("a[data-tooltip='Abrir website']").first
                    site = site_locator.get_attribute("href") if site_locator.count() > 0 else ""
                    
                    dados_brutos = {
                        "nome": nome,
                        "telefone": telefone,
                        "site": site
                    }
                    
                    yield dados_brutos
                    
                except Exception as e:
                    print(f"Erro ao clicar/extrair item: {e}")
                    continue
            
            # Fazer scroll da barra lateral principal para carregar mais itens
            try:
                page.evaluate("document.querySelector('div[role=\"feed\"]').scrollBy(0, 1000)")
                time.sleep(random.uniform(2.0, 4.0))
            except:
                pass
                
            # Se não achou itens novos na iteração, e a mensagem "Fim da lista" apareceu, quebra
            if not novos_itens_encontrados:
                # Checar se tem mensagem de fim
                if page.locator("text=Você chegou ao final da lista").count() > 0:
                    break
                # Ou tenta scrollar um pouco mais pra ver se destrava
