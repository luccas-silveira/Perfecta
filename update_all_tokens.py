# update_all_tokens.py
import requests
import json
import time
import os

# --- GLOBAL CONFIGURATIONS ---
# Client ID and Secret for refreshing the MAIN AGENCY token.
# These must correspond to the OAuth application that initially generated the token
# and refresh_token stored in gohighlevel_token.json.
REFRESH_CLIENT_ID = "683f5f030ea95a5033da7641-mbgzv4b8"
REFRESH_CLIENT_SECRET = "4b997d36-4315-459a-8e39-37d338d9cc24"

API_BASE_URL = "https://services.leadconnectorhq.com"
TOKEN_ENDPOINT_PATH = "/oauth/token"  # For refreshing agency token
LOCATION_TOKEN_ENDPOINT_PATH = "/oauth/locationToken"  # For getting location-specific tokens
API_VERSION = "2021-07-28"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENCY_TOKEN_FILE_PATH = os.path.join(BASE_DIR, "gohighlevel_token.json")
LOCATIONS_DATA_FILE = os.path.join(BASE_DIR, "installed_locations_data.json")

# --- 1. AGENCY TOKEN REFRESH LOGIC ---
def refresh_agency_token():
    """
    Lê o refresh_token do AGENCY_TOKEN_FILE_PATH, solicita um novo access_token
    e atualiza o arquivo JSON com os novos dados do token.
    Retorna True em sucesso, False em falha.
    """
    print(">>> [AGENCY TOKEN] Iniciando processo de atualização do Access Token da Agência...")

    # Basic check for placeholder credentials
    if REFRESH_CLIENT_ID.startswith("SEU_") or REFRESH_CLIENT_ID == "67eedd8b4a187d3c029d7839-mapli59s": # Example of a known different/placeholder ID
        print("!!! [AGENCY TOKEN] ATENÇÃO: Verifique REFRESH_CLIENT_ID e REFRESH_CLIENT_SECRET.")
        # return False # Potentially stop if known placeholders are used

    try:
        if not os.path.exists(AGENCY_TOKEN_FILE_PATH):
            print(f"!!! [AGENCY TOKEN] ERRO: Arquivo '{os.path.basename(AGENCY_TOKEN_FILE_PATH)}' não encontrado.")
            return False
        with open(AGENCY_TOKEN_FILE_PATH, 'r', encoding='utf-8') as f:
            token_data_antigo = json.load(f)
    except json.JSONDecodeError:
        print(f"!!! [AGENCY TOKEN] ERRO: JSON inválido em '{os.path.basename(AGENCY_TOKEN_FILE_PATH)}'.")
        return False
    except Exception as e:
        print(f"!!! [AGENCY TOKEN] ERRO ao ler arquivo: {e}")
        return False

    refresh_token_atual = token_data_antigo.get('refresh_token')
    user_type_salvo = token_data_antigo.get('userType')
    company_id_salvo = token_data_antigo.get('companyId') # Important for preserving

    if not refresh_token_atual:
        print("!!! [AGENCY TOKEN] ERRO: 'refresh_token' não encontrado no arquivo JSON.")
        return False
    if not user_type_salvo:
        print("!!! [AGENCY TOKEN] ERRO: 'userType' não encontrado no arquivo JSON (necessário para refresh).")
        return False

    payload_refresh = {
        'grant_type': 'refresh_token',
        'client_id': REFRESH_CLIENT_ID,
        'client_secret': REFRESH_CLIENT_SECRET,
        'refresh_token': refresh_token_atual,
        'user_type': user_type_salvo
    }
    headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}
    refresh_url = f"{API_BASE_URL}{TOKEN_ENDPOINT_PATH}"

    print(f">>> [AGENCY TOKEN] Solicitando refresh para User Type: {user_type_salvo}...")
    response_obj = None
    try:
        response_obj = requests.post(refresh_url, data=payload_refresh, headers=headers, timeout=30)
        response_obj.raise_for_status()
        novo_token_data = response_obj.json()
        print(">>> [AGENCY TOKEN] Novo conjunto de tokens da agência recebido com SUCESSO.")

        timestamp_atual = int(time.time())
        novo_token_data['refreshed_at_unix_timestamp'] = timestamp_atual
        novo_token_data['refreshed_at_readable'] = time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(timestamp_atual))

        if 'userType' not in novo_token_data and user_type_salvo:
            novo_token_data['userType'] = user_type_salvo
        if 'companyId' not in novo_token_data and company_id_salvo: # Preserve companyId if not in refresh response
            novo_token_data['companyId'] = company_id_salvo
        # Ensure companyId exists if the new token provides one, crucial for location token fetching
        if not novo_token_data.get('companyId'):
             print("!!! [AGENCY TOKEN] ALERTA: 'companyId' não está presente nos dados do token atualizado. Isso pode ser necessário para buscar tokens de localização.")


        with open(AGENCY_TOKEN_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(novo_token_data, f, indent=4, ensure_ascii=False)
        print(f">>> [AGENCY TOKEN] Arquivo '{os.path.basename(AGENCY_TOKEN_FILE_PATH)}' atualizado.")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"!!! [AGENCY TOKEN] ERRO HTTP: {http_err}")
        if response_obj is not None:
            print(f"!!! Status: {response_obj.status_code}, Resposta: {response_obj.text}")
            if response_obj.status_code in [400, 401] and "invalid_grant" in response_obj.text:
                 print("!!! Causa provável: 'refresh_token' inválido/expirado ou client_id/secret incorretos.")
    except Exception as e:
        print(f"!!! [AGENCY TOKEN] ERRO inesperado no refresh: {e}")
    return False

# --- 2. LOCATION TOKEN FETCHING LOGIC ---
def _load_agency_token_for_location_fetching():
    """Carrega o token da agência (access_token e companyId) do arquivo."""
    print(f">>> [LOCATION TOKENS] Carregando token da agência de: '{os.path.basename(AGENCY_TOKEN_FILE_PATH)}'...")
    try:
        if not os.path.exists(AGENCY_TOKEN_FILE_PATH):
            print(f"!!! [LOCATION TOKENS] ERRO: Arquivo de token da agência '{os.path.basename(AGENCY_TOKEN_FILE_PATH)}' não encontrado.")
            return None
        with open(AGENCY_TOKEN_FILE_PATH, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
        
        access_token = token_data.get('access_token')
        company_id = token_data.get('companyId')

        if not access_token:
            print(f"!!! [LOCATION TOKENS] ERRO: 'access_token' não encontrado no arquivo de token da agência.")
            return None
        if not company_id: # companyId is required in the payload for location tokens
            print(f"!!! [LOCATION TOKENS] ERRO: 'companyId' não encontrado no arquivo de token da agência. Este ID é necessário para buscar tokens de localização.")
            return None # Strict check: companyId must be present.
            
        print(">>> [LOCATION TOKENS] Token da agência e Company ID carregados com sucesso.")
        return {"access_token": access_token, "companyId": company_id}
    except Exception as e:
        print(f"!!! [LOCATION TOKENS] ERRO ao carregar token da agência: {e}")
        return None

def _load_locations_data():
    """Carrega a lista de dados de localizações do arquivo JSON."""
    print(f">>> [LOCATION TOKENS] Carregando dados das localizações de: '{os.path.basename(LOCATIONS_DATA_FILE)}'...")
    try:
        if not os.path.exists(LOCATIONS_DATA_FILE):
            print(f"!!! [LOCATION TOKENS] ERRO: Arquivo '{os.path.basename(LOCATIONS_DATA_FILE)}' não encontrado.")
            return None
        with open(LOCATIONS_DATA_FILE, 'r', encoding='utf-8') as f:
            locations_data = json.load(f)
        
        if isinstance(locations_data, dict) and 'locations' in locations_data and isinstance(locations_data['locations'], list):
            # Handles if the file was saved as {"locations": [...]} by get_app_locations.py
            # The get-location-tokens.py script expects a direct list.
            # Let's ensure this function returns the list itself.
            locations_data = locations_data['locations']

        if not isinstance(locations_data, list):
            print(f"!!! [LOCATION TOKENS] ERRO: Conteúdo de '{os.path.basename(LOCATIONS_DATA_FILE)}' não é uma lista JSON como esperado.")
            return None
            
        print(f">>> [LOCATION TOKENS] {len(locations_data)} localização(ões) carregada(s).")
        return locations_data
    except Exception as e:
        print(f"!!! [LOCATION TOKENS] ERRO ao carregar dados de localizações: {e}")
        return None

def _fetch_and_attach_location_tokens(agency_company_id, locations_data_list, agency_access_token):
    """Itera sobre localizações, obtém token e anexa à lista."""
    if not locations_data_list:
        print("!!! [LOCATION TOKENS] Nenhuma localização para processar.")
        return

    print(f"\n>>> [LOCATION TOKENS] Iniciando obtenção de tokens específicos para {len(locations_data_list)} localização(ões)...")
    location_token_url = f"{API_BASE_URL}{LOCATION_TOKEN_ENDPOINT_PATH}"
    
    for loc_info in locations_data_list:
        location_id = loc_info.get("_id") or loc_info.get("id") # Handle both _id and id for location id

        if not location_id:
            print(f"!!! [LOCATION TOKENS] Aviso: Item de localização sem ID válido. Pulando. Item: {loc_info}")
            loc_info["location_specific_token_fetch_status"] = {"error": "Missing ID in location data"}
            continue

        print(f"\n--- [LOCATION TOKENS] Processando Location ID: {location_id} ---")
        
        payload = {"companyId": agency_company_id, "locationId": location_id}
        headers = {
            "Authorization": f"Bearer {agency_access_token}",
            "Version": API_VERSION,
            "Content-Type": "application/x-www-form-urlencoded", # As per get-location-tokens.py
            "Accept": "application/json"
        }

        response_obj = None
        try:
            response_obj = requests.post(location_token_url, data=payload, headers=headers, timeout=20)
            response_obj.raise_for_status()
            location_token_data = response_obj.json()
            print(f"    <- [LOCATION TOKENS] Token para Location ID {location_id} obtido com SUCESSO.")
            loc_info["location_specific_token_data"] = location_token_data
        except requests.exceptions.HTTPError as http_err:
            error_message = f"ERRO HTTP: {http_err}"
            print(f"    !!! [LOCATION TOKENS] {error_message}")
            error_details_to_save = {"error": error_message, "status_code": None, "details": None}
            if response_obj is not None:
                error_details_to_save["status_code"] = response_obj.status_code
                try: error_details_to_save["details"] = response_obj.json()
                except json.JSONDecodeError: error_details_to_save["details"] = response_obj.text[:300] + "..."
            loc_info["location_specific_token_data"] = error_details_to_save
        except Exception as e:
            error_message = f"ERRO inesperado: {e}"
            print(f"    !!! [LOCATION TOKENS] {error_message}")
            loc_info["location_specific_token_data"] = {"error": error_message}

def _save_updated_locations_data(data_to_save):
    """Salva a lista de dados de localizações atualizada."""
    print(f"\n>>> [LOCATION TOKENS] Salvando dados atualizados em: '{os.path.basename(LOCATIONS_DATA_FILE)}'...")
    try:
        # The original get-location-tokens.py saves the list directly.
        # If get_app_locations.py saved it as {"locations": [...]}, this script would
        # have loaded just the list. So, we save the list directly.
        with open(LOCATIONS_DATA_FILE, 'w', encoding='utf-8') as f_out:
            json.dump(data_to_save, f_out, indent=4, ensure_ascii=False)
        print(">>> [LOCATION TOKENS] Dados de localização atualizados salvos com sucesso!")
        return True
    except Exception as e:
        print(f"!!! [LOCATION TOKENS] ERRO AO SALVAR ARQUIVO JSON: {e}")
        return False

def manage_location_tokens():
    """Orquestra o processo de obtenção de tokens de localização."""
    print("\n--- [LOCATION TOKENS] Iniciando Gerenciamento de Tokens de Localização ---")
    
    agency_auth_data = _load_agency_token_for_location_fetching()
    if not agency_auth_data:
        print("!!! [LOCATION TOKENS] Falha ao carregar dados de autenticação da agência. Abortando.")
        return False

    agency_access_token = agency_auth_data['access_token']
    agency_company_id_for_locations = agency_auth_data['companyId'] # Use companyId from agency token file
    
    print(f">>> [LOCATION TOKENS] Usando Company ID da Agência: {agency_company_id_for_locations} para buscar tokens de localização.")

    lista_de_localizacoes = _load_locations_data()
    if lista_de_localizacoes is None: # Check for None specifically, as empty list is valid
        print("!!! [LOCATION TOKENS] Falha ao carregar dados de localizações. Abortando.")
        return False
    if not lista_de_localizacoes: # Empty list
        print(">>> [LOCATION TOKENS] Lista de localizações está vazia. Nada a processar.")
        return True # Considered success as there's nothing to do.

    _fetch_and_attach_location_tokens(agency_company_id_for_locations, lista_de_localizacoes, agency_access_token)
    
    if _save_updated_locations_data(lista_de_localizacoes):
        print("--- [LOCATION TOKENS] Gerenciamento de Tokens de Localização concluído com SUCESSO ---")
        return True
    else:
        print("--- [LOCATION TOKENS] Gerenciamento de Tokens de Localização concluído com FALHA AO SALVAR ---")
        return False

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print(f"--- Iniciando Script Combinado: {os.path.basename(__file__)} ---")
    start_time = time.time()

    agency_token_ok = refresh_agency_token()

    if agency_token_ok:
        print("\n>>> Token da agência atualizado/verificado com sucesso.")
        location_tokens_ok = manage_location_tokens()
        if location_tokens_ok:
            print("\n--- Script Combinado FINALIZADO COM SUCESSO ---")
        else:
            print("\n--- Script Combinado FINALIZADO COM FALHA na etapa de tokens de localização ---")
            exit(1)
    else:
        print("\n!!! Falha ao atualizar o token da agência. Processo interrompido.")
        print("--- Script Combinado FINALIZADO COM FALHA ---")
        exit(1)
    
    end_time = time.time()
    print(f"Tempo total de execução: {end_time - start_time:.2f} segundos.")