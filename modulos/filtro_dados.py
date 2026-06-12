import re
from typing import Dict, Any, Optional, Tuple
from playwright.sync_api import BrowserContext

class FiltroDados:
    def __init__(self):
        """
        Regras de negócios estritas. Age como bloqueio absoluto (Gatekeeper).
        """
        pass

    def classificar_telefone(self, telefone_bruto: str) -> Optional[str]:
        """
        Analisa o telefone e retorna o número limpo caso seja um celular válido.
        Caso contrário (seja fixo ou inválido), retorna None.
        Um celular precisa ter 11 dígitos e o 3º dígito sendo '9'.
        """
        if not telefone_bruto:
            return None
            
        numeros = re.sub(r'\D', '', telefone_bruto)
        
        # Ignora se for 0800, 4004 (nesta versão simplificada, focamos no padrão BR regional)
        # Ex celular: 11987654321 (11 digitos)
        if len(numeros) == 11 and numeros[2] == '9':
            return numeros
            
        return None

    def vasculhar_site(self, url: str, context: BrowserContext) -> Tuple[Optional[str], Optional[str]]:
        """
        Abre uma nova aba no contexto atual e visita o site procurando por @gmail.com e celulares.
        Retorna: (gmail_encontrado, celular_encontrado)
        """
        if not url:
            return None, None
            
        print(f"[Pesquisa Profunda] Inspecionando site em busca de Contatos: {url}")
        
        page = context.new_page()
        gmail = None
        celular = None
        
        try:
            # Timeout curto de 10s
            page.goto(url, timeout=10000, wait_until="domcontentloaded")
            body_text = page.locator("body").inner_text()
            html_content = page.content()
            
            # 1. Buscar Gmail
            match_email = re.search(r'[a-zA-Z0-9_.+-]+@gmail\.com', body_text, re.IGNORECASE)
            if match_email:
                gmail = match_email.group(0)
                
            # 2. Buscar Celular (Regex para padrão BR no texto ou links wa.me)
            # Tenta achar link do whatsapp primeiro
            match_wa = re.search(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=)[+]*(\d{10,13})', html_content)
            if match_wa:
                nums = match_wa.group(1)
                # Pega os ultimos 11 digitos assumindo que é Brasil (ignora o 55 se houver)
                if len(nums) >= 11:
                    celular_candidato = nums[-11:]
                    if celular_candidato[2] == '9':
                        celular = celular_candidato
            
            # Se não achou link do zap, procura no texto
            if not celular:
                # Procura padrões (XX) 9XXXX-XXXX ou similares
                match_tel = re.search(r'\(?\d{2}\)?\s*9\d{4}[-\s]*\d{4}', body_text)
                if match_tel:
                    numeros = re.sub(r'\D', '', match_tel.group(0))
                    if len(numeros) == 11 and numeros[2] == '9':
                        celular = numeros
                        
        except Exception as e:
            pass
        finally:
            page.close()
            
        return gmail, celular

    def triagem(self, dados_brutos: Dict[str, Any], context: BrowserContext) -> Optional[Dict[str, Any]]:
        """
        Fluxo de validação: Identifica se tem celular no Maps ou no Site.
        Se não tiver celular em nenhum dos dois -> Morre aqui.
        """
        telefone_maps = dados_brutos.get("telefone", "")
        site_url = dados_brutos.get("site", "")
        
        # 1. Analisa o que veio do Maps
        whatsapp_maps = self.classificar_telefone(telefone_maps)
        
        whatsapp_final = whatsapp_maps
        gmail_final = None
        
        # 2. Se tem site, vamos vasculhar (mesmo se já achou celular no maps, pra achar o gmail)
        if site_url:
            gmail_site, celular_site = self.vasculhar_site(site_url, context)
            gmail_final = gmail_site
            
            # Se o Maps não tinha celular, e o Site tem Celular -> Sucesso! Achamos o Zap.
            if not whatsapp_final and celular_site:
                whatsapp_final = celular_site
                
        # 3. Regra Mestra: Tem que ter WhatsApp!
        if not whatsapp_final:
            return None
            
        return {
            "nome": dados_brutos.get("nome", "Sem Nome"),
            "whatsapp": whatsapp_final,
            "gmail": gmail_final or "",
            "site": site_url
        }
