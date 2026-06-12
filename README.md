# Relatório Geral do Sistema de Scraping (ETL)

Este documento detalha o funcionamento, a arquitetura e como personalizar o sistema de extração de leads desenvolvido.

## 1. Arquitetura Modular (Pipeline ETL)

O sistema foi construído seguindo uma lógica de **Pipeline ETL** (Extract, Transform, Load), separando a inteligência da execução.

*   **O Cérebro (`orquestrador.py`)**: Coordena o fluxo, gerencia os limites diários e decide a ordem das operações.
*   **Os Órgãos (`modulos/`)**: Scripts especializados que executam tarefas específicas de forma determinística.

---

## 2. Componentes do Sistema

### 🧠 Orquestrador ([orquestrador.py](orquestrador.py))
É o ponto de entrada do robô. Ele:
- Carrega as configurações do arquivo `.env`.
- Inicializa os módulos de extração, filtragem e planilhas.
- Controla o loop principal de busca.
- Garante que a meta de leads (`MAX_LEADS`) seja respeitada.

### 📍 Extrator Maps ([extrator_maps.py](modulos/extrator_maps.py))
Responsável apenas pela navegação no Google Maps.
- Faz o scroll infinito da lista de resultados.
- Coleta dados básicos visíveis (nome, site, telefone visível, endereço).
- **Não** toma decisões sobre a qualidade do lead.

### 🔍 Filtro de Dados ([filtro_dados.py](modulos/filtro_dados.py))
É a "peneira" inteligente do sistema.
- Verifica se o lead já tem WhatsApp no Google Maps.
- Caso não tenha, **visita o site da empresa** para buscar números de WhatsApp ou e-mails (Gmail) escondidos.
- Descarta leads que não possuem meios de contato válidos.

### 📊 Planilhas ([planilhas.py](modulos/planilhas.py))
Gerencia a persistência dos dados.
- Conecta-se à API do Google Sheets.
- Lê os números já existentes para evitar duplicatas.
- Salva os novos leads validados na planilha.

---

## 3. Como Personalizar o Robô

A maioria das configurações pode ser alterada sem mexer no código principal, através do arquivo **`.env`**.

### ⚙️ Alterando o Máximo de Leads
No arquivo [`.env`](.env), localize a linha:
```env
MAX_LEADS=5
```
Basta alterar o número para a quantidade desejada. O robô irá parar assim que atingir essa meta de leads **válidos** salvos na planilha.

### 🔎 Alterando o Termo e Local de Busca
No arquivo [`.env`](.env), localize a linha:
```env
TERMO_BUSCA="barbearias em brasilia df"
```
Para mudar o que o robô busca ou a cidade, altere o texto entre aspas. Exemplos:
- `TERMO_BUSCA="odontologia em São Paulo SP"`
- `TERMO_BUSCA="oficinas mecânicas em Curitiba"`

### 💻 Alterações no Código (Avançado)
Se você precisar alterar comportamentos mais profundos:

- **Ver o navegador rodando**: No [orquestrador.py](orquestrador.py) (linha 32), mude `headless=True` para `headless=False`.
- **Regras de Filtro**: No [filtro_dados.py](modulos/filtro_dados.py), você pode ajustar os termos de busca de e-mail ou WhatsApp dentro dos sites.

---

## 4. Fluxo de Funcionamento (Passo a Passo)

1.  **Início**: O Orquestrador lê o arquivo `.env`.
2.  **Verificação**: O módulo de Planilhas baixa todos os telefones que já estão na sua Google Sheets.
3.  **Busca**: O Playwright abre o Google Maps e pesquisa pelo `TERMO_BUSCA`.
4.  **Extração**: O robô rola a lista e "clica" nos estabelecimentos.
5.  **Triagem**: 
    - Se o lead tem WhatsApp no Maps, ele passa.
    - Se não tem, o robô abre o site da empresa em uma nova aba e "escaneia" o site atrás de um WhatsApp.
6.  **Gravação**: Se o lead for válido e não for duplicado, ele é escrito na planilha em tempo real.
7.  **Finalização**: O processo se repete até atingir o `MAX_LEADS`.

---

## 5. Arquivos de Suporte

- **`requirements.txt`**: Contém as bibliotecas necessárias.
- **`credentials.json`**: Chave de acesso à API do Google.
- **`.tmp/`**: Pasta onde o robô guarda dados temporários da sessão do navegador.

> [!TIP]
> Sempre que alterar o `.env`, você precisará reiniciar o robô para que as novas configurações entrem em vigor.
