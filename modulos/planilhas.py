import gspread
from typing import List, Dict, Any

class PlanilhasGoogle:
    def __init__(self, spreadsheet_name: str = "Leads Barbearias", credentials_path: str = "credentials.json"):
        """
        Inicializa a conexão com o Google Sheets.
        Requer um arquivo credentials.json com as chaves da conta de serviço.
        """
        self.credentials_path = credentials_path
        self.spreadsheet_name = spreadsheet_name
        self.client = None
        self.sheet = None
        
        try:
            # Tenta autenticar. Se o arquivo não existir ou for inválido, avisa o usuário.
            self.client = gspread.service_account(filename=self.credentials_path)
            # Tenta abrir a planilha pelo nome
            self.sheet = self.client.open(self.spreadsheet_name).sheet1
            print(f"Conectado à planilha: {self.spreadsheet_name}")
        except FileNotFoundError:
            print("AVISO: Arquivo credentials.json não encontrado. A integração com Sheets não funcionará de verdade.")
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"AVISO: Planilha '{self.spreadsheet_name}' não encontrada. Crie e compartilhe com o e-mail do bot.")
        except Exception as e:
            print(f"AVISO: Erro ao conectar com Google Sheets: {e}")

    def obter_telefones_existentes(self) -> List[str]:
        """
        Lê a planilha e retorna uma lista de telefones da Coluna B (WhatsApp)
        para garantir a anti-duplicação.
        """
        if not self.sheet:
            return []
            
        print("Lendo telefones existentes no Google Sheets para anti-duplicação...")
        try:
            # Supondo que a coluna B (index 2) seja o WhatsApp
            telefones = self.sheet.col_values(2)
            # Remove o cabeçalho se existir
            if telefones and telefones[0].lower() in ['whatsapp', 'telefone']:
                telefones.pop(0)
            return telefones
        except Exception as e:
            print(f"Erro ao ler telefones: {e}")
            return []

    def salvar_lead(self, lead_data: Dict[str, Any]) -> bool:
        """
        Salva uma nova linha no Google Sheets com os dados validados.
        """
        if not self.sheet:
            nome_seguro = lead_data['nome'].encode('ascii', 'ignore').decode()
            print(f"[DRY RUN] Inserindo dados locais -> {nome_seguro}")
            return True
            
        print(f"Salvando lead na planilha: {lead_data['nome']}")
        try:
            linha = [
                lead_data.get('nome', ''),
                lead_data.get('whatsapp', ''),
                lead_data.get('gmail', '') or '',
                lead_data.get('site', '') or ''
            ]
            self.sheet.append_row(linha)
            return True
        except Exception as e:
            print(f"Erro ao salvar lead na planilha: {e}")
            return False
