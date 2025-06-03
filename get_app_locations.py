import requests
import json
import os # Para verificações de placeholders e manipulação de caminhos

# --- Configurações Essenciais (VOCÊ PRECISA PREENCHER/VERIFICAR ESTES VALORES) ---

# ID da sua Agência/Empresa principal. Este é o Company ID da agência
# que possui o aplicativo ou está autorizada a fazer esta consulta.
# Exemplo: "FevLf4DJoE5QlF3MDviM" (Verifique o 'companyId' no seu gohighlevel_token.json ou na sua conta)
AGENCY_COMPANY_ID = "FevLf4DJoE5QlF3MDviM"  # <<< SUBSTITUA AQUI PELO ID CORRETO DA SUA AGÊNCIA

# ID do seu Aplicativo (Marketplace App ID)
# Exemplo: "tDtDnQdgm2LXpyiqYvZ6" (Este é o ID do aplicativo que você quer verificar)
APP_ID = "683f5f030ea95a5033da7641"                        # <<< SUBSTITUA AQUI PELO ID DO SEU APLICATIVO

# Arquivo JSON onde o token de acesso da sua AGÊNCIA está salvo.
# Este arquivo deve conter um campo "access_token" válido.
AGENCY_TOKEN_FILE_PATH = "gohighlevel_token.json"

# Nome do arquivo JSON onde a lista de localizações com o app instalado será salva.
# Este arquivo será criado ou sobrescrito.
OUTPUT_LOCATIONS_FILE = "installed_locations_data.json"
# ------------------------------------------------------------------------------------

# Configurações da API (geralmente não precisam ser alteradas)
API_ENDPOINT_URL = "https://services.leadconnectorhq.com/oauth/installedLocations"
API_VERSION = "2021-07-28" # Conforme a documentação e seu exemplo

def carregar_token_da_agencia(filepath):
    """
    Carrega o access_token da agência do arquivo JSON especificado.
    Retorna o access_token como string, ou None se houver erro.
    """
    print(f">>> Carregando token da agência de: '{filepath}'...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
        access_token = token_data.get('access_token')

        if not access_token:
            print(f"!!! ERRO: Chave 'access_token' não encontrada no arquivo '{filepath}'.")
            print("!!! Certifique-se de que o arquivo contém um token de acesso válido da agência.")
            return None
        
        print(">>> Token da agência carregado com sucesso.")
        return access_token
    except FileNotFoundError:
        print(f"!!! ERRO: Arquivo de token da agência '{filepath}' não encontrado.")
        print("!!! Execute primeiro o script para obter/atualizar o token da agência.")
        return None
    except json.JSONDecodeError:
        print(f"!!! ERRO: O arquivo '{filepath}' não contém um JSON válido.")
        return None
    except Exception as e:
        print(f"!!! ERRO inesperado ao ler o arquivo de token da agência: {e}")
        return None

def obter_e_salvar_localizacoes_instaladas(agency_token, company_id, app_id, output_filepath):
    """
    Busca as localizações onde o aplicativo especificado está instalado,
    usando o token da agência, e salva a lista em um arquivo JSON.
    """
    print(f"\n>>> Buscando localizações onde o App ID '{app_id}' está instalado para a Company ID '{company_id}'...")

    headers = {
        "Authorization": f"Bearer {agency_token}", # Essencial para autenticação
        "Version": API_VERSION,
        "Accept": "application/json"
    }
    
    querystring = {
        "isInstalled": "true", # Conforme solicitado, para buscar apenas onde está instalado
        "companyId": company_id,
        "appId": app_id
    }

    print(f">>> Enviando requisição GET para: {API_ENDPOINT_URL}")
    print(f"    Com parâmetros: {querystring}")
    
    response = None # Inicializa para o caso de erro antes da atribuição
    try:
        response = requests.get(API_ENDPOINT_URL, headers=headers, params=querystring)
        response.raise_for_status()  # Levanta um erro HTTP para respostas 4xx/5xx

        locations_data = response.json()
        print(">>> Resposta da API recebida com SUCESSO!")

        # A resposta da API, conforme a documentação, já deve ser uma lista de localizações
        # ou um objeto contendo uma lista. Ex: {"locations": [...]}
        # Vamos verificar e extrair a lista de 'locations' se necessário.
        if isinstance(locations_data, dict) and 'locations' in locations_data:
            data_to_save = locations_data['locations']
            print(f">>> Encontradas {len(data_to_save)} localizações onde o app está instalado.")
        elif isinstance(locations_data, list):
            data_to_save = locations_data
            print(f">>> Encontradas {len(data_to_save)} localizações onde o app está instalado (resposta direta da lista).")
        else:
            print("!!! AVISO: A resposta da API não foi uma lista de localizações ou um dicionário com a chave 'locations' como esperado.")
            print(f"!!! Conteúdo recebido: {json.dumps(locations_data, indent=2)}")
            data_to_save = locations_data # Salvar o que foi recebido mesmo assim

        # Salvar os dados no arquivo JSON
        with open(output_filepath, 'w', encoding='utf-8') as f_out:
            json.dump(data_to_save, f_out, indent=4, ensure_ascii=False)
        print(f">>> Dados das localizações instaladas salvos em: '{output_filepath}'")

    except requests.exceptions.HTTPError as http_err:
        print(f"!!! ERRO HTTP ao buscar localizações: {http_err}")
        if response is not None:
            print(f"!!! Código de Status da Resposta: {response.status_code}")
            print("!!! Resposta da API (pode conter mais detalhes do erro):")
            try:
                print(json.dumps(response.json(), indent=2))
            except json.JSONDecodeError:
                print(response.text)
    except requests.exceptions.RequestException as req_err:
        print(f"!!! ERRO DE REQUISIÇÃO (ex: problema de conexão): {req_err}")
    except json.JSONDecodeError:
        print("!!! ERRO ao tentar decodificar a resposta JSON da API.")
        if response is not None:
            print("!!! Conteúdo recebido (que não é JSON válido):")
            print(response.text)
    except Exception as e:
        print(f"!!! Ocorreu um erro inesperado: {e}")

# --- Ponto de entrada do script ---
if __name__ == "__main__":
    print("--- Iniciando script: Obter Localizações com App Instalado ---")

    # Verificação crucial: Confira se você alterou os placeholders!
    if AGENCY_COMPANY_ID == "SEU_AGENCY_COMPANY_ID_AQUI" or APP_ID == "SEU_APP_ID_AQUI":
        print("-" * 70)
        print("!!! ATENÇÃO URGENTE !!!")
        print("!!! Você PRECISA substituir os valores de placeholder para")
        print("!!! 'AGENCY_COMPANY_ID' e 'APP_ID' com suas informações reais")
        print("!!! no início do script.")
        print("-" * 70)
    else:
        # 1. Carregar o token da agência
        token_da_agencia = carregar_token_da_agencia(AGENCY_TOKEN_FILE_PATH)

        if token_da_agencia:
            # 2. Obter e salvar as localizações
            obter_e_salvar_localizacoes_instaladas(
                token_da_agencia,
                AGENCY_COMPANY_ID,
                APP_ID,
                OUTPUT_LOCATIONS_FILE
            )
        else:
            print("!!! Processo interrompido devido à falha ao carregar o token da agência.")

    print("\n--- Script finalizado ---")