import requests
import json
import time # Para adicionar timestamps de quando o token foi atualizado

client_id = "683f5f030ea95a5033da7641-mbgzv4b8"
client_secret = "4b997d36-4315-459a-8e39-37d338d9cc24"
authorization_code = "3d0e95517576a2c4f279ca9396011c8d531a7b58" # Este é o 'code'
user_type = "Company"  # Ou "Location"

# Configurações da API (geralmente não precisam ser alteradas)
token_url = "https://services.leadconnectorhq.com/oauth/token"
token_file_path = "gohighlevel_token.json"  # Nome do arquivo onde o token será salvo

# Função principal para obter e salvar o token
def obter_e_salvar_token_gohighlevel():

    # Solicita o access token ao Gohighlevel e o salva em um arquivo JSON.

    print(">>> Iniciando o processo para obter o Access Token do Gohighlevel...")

    # Verificação crucial: Confira se você alterou os placeholders!
    if client_id == "SEU_CLIENT_ID_AQUI" or \
       client_secret == "SEU_CLIENT_SECRET_AQUI" or \
       authorization_code == "CODIGO_DE_AUTORIZACAO_RECEBIDO_AQUI" or \
        print("-" * 70):
        print("!!! ATENÇÃO URGENTE !!!")
        print("!!! Você PRECISA substituir os valores de placeholder como 'SEU_CLIENT_ID_AQUI',")
        print("!!! 'SEU_CLIENT_SECRET_AQUI', 'CODIGO_DE_AUTORIZACAO_RECEBIDO_AQUI', e 'SUA_REDIRECT_URI_AQUI'")
        print("!!! com suas informações reais no início do script.")
        print("!!! O 'authorization_code' é um código temporário que você recebe após o")
        print("!!! processo de autorização do usuário na plataforma Gohighlevel.")
        print("-" * 70)
        return # Interrompe a execução da função se as credenciais não foram alteradas

    # Dados que serão enviados na requisição para obter o token
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code', # Tipo de concessão para obter o token inicial
        'code': authorization_code,         # O código de autorização que você recebe
        'user_type': user_type
    }

    # Cabeçalhos da requisição
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Accept': "application/json"
    }

    print(f">>> Enviando requisição para o endpoint: {token_url}")
    try:
        # Fazendo a requisição POST
        response = requests.post(token_url, data=payload, headers=headers)

        # Verifica se a requisição teve algum erro HTTP (como 400, 401, 500, etc.)
        response.raise_for_status()

        # Se a requisição foi bem-sucedida, converte a resposta JSON para um dicionário Python
        token_data = response.json()
        print(">>> Resposta da API recebida com SUCESSO!")

        # Salvando os dados do token em um arquivo JSON
        with open(token_file_path, 'w') as f:
            json.dump(token_data, f, indent=4) # indent=4 para formatar o JSON de forma legível
        print(f">>> Token e informações relacionadas foram salvos em: {token_file_path}")

        # Mostrar alguns detalhes do token obtido (opcional)
        print("\n--- Detalhes do Token Obtido ---")
        print(f"  Access Token (início): {token_data.get('access_token', 'N/A')[:20]}...") # Mostra apenas os primeiros 20 caracteres
        print(f"  Refresh Token (início): {token_data.get('refresh_token', 'N/A')[:20] if token_data.get('refresh_token') else 'N/A'}...")
        print(f"  Expira em (segundos): {token_data.get('expires_in', 'N/A')}")
        print(f"  Tipo de Usuário: {token_data.get('userType', 'N/A')}")
        print(f"  ID da Conta (Empresa/Agência): {token_data.get('companyId') or token_data.get('locationId') or token_data.get('agencyId') or 'N/A'}")
        print("--- Fim dos Detalhes ---\n")

    except requests.exceptions.HTTPError as http_err:
        print(f"!!! ERRO HTTP ao tentar obter o token: {http_err}")
        print(f"!!! Código de Status da Resposta: {response.status_code}")
        print("!!! Resposta da API (pode conter mais detalhes do erro):")
        print(response.text) # Mostra a resposta completa da API em caso de erro
    except requests.exceptions.RequestException as req_err:
        print(f"!!! ERRO DE REQUISIÇÃO (ex: problema de conexão): {req_err}")
    except json.JSONDecodeError:
        print("!!! ERRO ao tentar decodificar a resposta JSON da API.")
        print("!!! Conteúdo recebido (que não é JSON válido):")
        print(response.text)
    except Exception as e:
        print(f"!!! Ocorreu um erro inesperado e não tratado: {e}")

# ---------------------------------------------------------------------------
# Ponto de entrada do script: quando você executa "python nome_do_arquivo.py"
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("--- Iniciando script para obter token do Gohighlevel ---")

    # Antes de rodar, você precisa ter a biblioteca 'requests' instalada.
    # Se não tiver, abra o terminal e digite: pip install requests
    # OU, se usar Python 3: pip3 install requests

    # Chama a função principal
    obter_e_salvar_token_gohighlevel()

    print("--- Script finalizado ---")