import requests
import json
import os # Para checagem de placeholders

# --- Configurações Essenciais (VOCÊ PRECISA PREENCHER/VERIFICAR ABAIXO) ---

# 1. Arquivo JSON onde o token da sua AGÊNCIA está salvo
AGENCY_TOKEN_FILE_PATH = "gohighlevel_token.json"

# 2. ID da sua Agência/Empresa principal (Company ID da Agência)
AGENCY_COMPANY_ID = "FevLf4DJoE5QlF3MDviM"  # << SUBSTITUA AQUI PELO ID CORRETO DA SUA AGÊNCIA

# 3. ID da Localização Alvo (A Location ID específica que você quer processar)
TARGET_LOCATION_ID = "vH3FikNOO9r4YkbIIiub" # << SUBSTITUA AQUI PELO ID DA LOCATION DESEJADA

# 4. Arquivo JSON onde o token da localização alvo será salvo
LOCATION_TOKEN_OUTPUT_FILE = "location_token.json" # Nome do arquivo de saída para o token da location

# --- Configurações da API (geralmente não precisam ser alteradas) ---
API_BASE_URL = "https://services.leadconnectorhq.com"
LOCATION_TOKEN_ENDPOINT = "/oauth/locationToken"
API_VERSION = "2021-07-28"

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
            return None
        print(">>> Token da agência carregado com sucesso.")
        return access_token
    except FileNotFoundError:
        print(f"!!! ERRO: Arquivo de token da agência '{filepath}' não encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"!!! ERRO: O arquivo '{filepath}' não contém um JSON válido.")
        return None
    except Exception as e:
        print(f"!!! ERRO inesperado ao ler o arquivo de token da agência: {e}")
        return None

def obter_token_para_location_fixa(agency_company_id, fixed_location_id, agency_token):
    """
    Tenta obter um token específico para a fixed_location_id fornecida.
    Retorna o dicionário do token ou um dicionário de erro.
    """
    print(f"\n--- Processando Location ID Fixa: {fixed_location_id} ---")
    
    if not fixed_location_id or fixed_location_id == "SEU_LOCATION_ID_ESPECIFICO_AQUI":
        error_msg = "!!! ERRO: 'TARGET_LOCATION_ID' não foi definida ou ainda é um placeholder. Por favor, configure-a no script."
        print(error_msg)
        return {"error": error_msg, "locationId_processed": fixed_location_id}

    url = f"{API_BASE_URL}{LOCATION_TOKEN_ENDPOINT}"
    payload = {
        "companyId": agency_company_id,
        "locationId": fixed_location_id
    }
    headers = {
        "Authorization": f"Bearer {agency_token}",
        "Version": API_VERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    print(f"    -> Solicitando token para Location ID: {fixed_location_id}...")
    response_obj = None
    try:
        response_obj = requests.post(url, data=payload, headers=headers)
        response_obj.raise_for_status() # Lança uma exceção para códigos de erro HTTP (4xx ou 5xx)
        location_token_data = response_obj.json()
        print(f"    <- Token específico para Location ID {fixed_location_id} obtido com SUCESSO.")
        return location_token_data # Retorna os dados do token
    except requests.exceptions.HTTPError as http_err:
        error_message = f"ERRO HTTP ao obter token: {http_err}"
        print(f"    !!! {error_message}")
        error_payload_dict = {"error": error_message, "status_code": None, "details": None, "locationId_processed": fixed_location_id}
        if response_obj is not None:
            error_payload_dict["status_code"] = response_obj.status_code
            try:
                error_payload_dict["details"] = response_obj.json()
            except json.JSONDecodeError:
                error_payload_dict["details"] = response_obj.text[:300] + ("..." if len(response_obj.text) > 300 else "")
            print(f"       Status: {response_obj.status_code}, Resposta: {error_payload_dict['details']}")
        return error_payload_dict
    except requests.exceptions.RequestException as req_err:
        error_message = f"ERRO de Requisição ao obter token (ex: problema de conexão): {req_err}"
        print(f"    !!! {error_message}")
        return {"error": error_message, "locationId_processed": fixed_location_id}
    except json.JSONDecodeError:
        error_message = "ERRO ao tentar decodificar a resposta JSON da API."
        print(f"    !!! {error_message}")
        details = None
        if response_obj is not None:
             details = response_obj.text[:300] + ("..." if len(response_obj.text) > 300 else "")
             print(f"       Conteúdo recebido (que não é JSON válido): {details}")
        return {"error": error_message, "raw_response": details, "locationId_processed": fixed_location_id}
    except Exception as e:
        error_message = f"ERRO inesperado ao obter token para {fixed_location_id}: {e}"
        print(f"    !!! {error_message}")
        return {"error": error_message, "locationId_processed": fixed_location_id}

def salvar_token_da_location(filepath, token_data):
    """
    Salva os dados do token da localização (ou erro) no arquivo JSON especificado.
    """
    print(f"\n>>> Salvando dados do token da localização em: '{filepath}'...")
    try:
        with open(filepath, 'w', encoding='utf-8') as f_out:
            json.dump(token_data, f_out, indent=4, ensure_ascii=False)
        print(">>> Dados do token da localização salvos com sucesso!")
    except IOError as io_err:
        print(f"!!! ERRO AO SALVAR ARQUIVO JSON '{filepath}': {io_err}")
    except Exception as e_save:
        print(f"!!! ERRO INESPERADO AO SALVAR ARQUIVO JSON '{filepath}': {e_save}")

# --- Ponto de entrada do script ---
if __name__ == "__main__":
    print("--- Iniciando script: Obter token específico para uma LOCATION FIXA ---")

    # Verificar se os IDs da Agência e da Location foram preenchidos
    valid_config = True
    if AGENCY_COMPANY_ID == "SEU_AGENCY_COMPANY_ID_AQUI" or not AGENCY_COMPANY_ID:
        print("-" * 70)
        print("!!! ATENÇÃO URGENTE !!!")
        print("!!! Por favor, edite o script e defina a variável 'AGENCY_COMPANY_ID'")
        print("!!! com o ID correto da sua agência/empresa principal no topo do arquivo.")
        print("-" * 70)
        valid_config = False
    
    if TARGET_LOCATION_ID == "SEU_LOCATION_ID_ESPECIFICO_AQUI" or not TARGET_LOCATION_ID:
        print("-" * 70)
        print("!!! ATENÇÃO URGENTE !!!")
        print("!!! Por favor, edite o script e defina a variável 'TARGET_LOCATION_ID'")
        print("!!! com o ID correto da localização alvo no topo do arquivo.")
        print("-" * 70)
        valid_config = False

    if valid_config:
        # 1. Carregar o token da agência
        agency_token = carregar_token_da_agencia(AGENCY_TOKEN_FILE_PATH)

        if agency_token:
            # 2. Obter token para a location fixa especificada
            location_token_info = obter_token_para_location_fixa(
                AGENCY_COMPANY_ID, 
                TARGET_LOCATION_ID, 
                agency_token
            )
            
            # 3. Salvar o token/erro da location no arquivo de saída especificado
            # A função obter_token_para_location_fixa sempre retorna um dicionário (token ou erro)
            salvar_token_da_location(LOCATION_TOKEN_OUTPUT_FILE, location_token_info)
        else:
            print("!!! Não foi possível carregar o token da agência. Processo interrompido.")
    else:
        print("!!! Configurações essenciais não foram preenchidas. Verifique as mensagens acima.")

    print("\n--- Script finalizado ---")