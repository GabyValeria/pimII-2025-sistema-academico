import pandas as pd
import os
from typing import Optional, Dict, Any, Tuple 

CAMINHO_BASE_DADOS = 'dados'

# Lista de arquivos CSV esperados
ARQUIVOS_CSV = {
    'alunos': 'alunos.csv',
    'professores': 'professores.csv',
    'turmas': 'turmas.csv',
    'matriculas': 'matriculas.csv',
    'atividades': 'atividades.csv',
    'notas': 'notas.csv'
}

DADOS_ACADEMICOS: Dict[str, pd.DataFrame] = {}
USUARIOS_CREDENCIAS: Dict[str, Any] = {
    'admin': [{'id': 'admin', 'login': 'admin', 'senha': '123'}] 
}


def carregar_dados_do_csv():
    """Carrega DataFrames, usando separador ';', normaliza colunas e extrai credenciais."""
    global DADOS_ACADEMICOS
    global USUARIOS_CREDENCIAS
    
    print(f"DEBUG: Diretório de trabalho (CWD): {os.getcwd()}")
    print(f"DEBUG: Tentando carregar CSVs de: {os.path.abspath(CAMINHO_BASE_DADOS)}")
    
    # 1. Tenta carregar cada CSV
    for key, filename in ARQUIVOS_CSV.items():
        caminho_completo = os.path.join(CAMINHO_BASE_DADOS, filename)
        
        if not os.path.exists(caminho_completo):
            print(f"⚠️ AVISO: Arquivo não encontrado em: {caminho_completo}. DataFrame de '{key}' vazio.")
            DADOS_ACADEMICOS[key] = pd.DataFrame()
            continue

        try:
            # --- TRATAMENTO PADRÃO PARA TODOS OS CSVS ---
            # Usa leitura padrão com separador ';' e encoding 'latin-1' (padrão no Brasil)
            df = pd.read_csv(caminho_completo, sep=';', encoding='latin-1', header=0)
            
            # Checa se o DataFrame está vazio após a leitura
            if df.empty:
                 raise ValueError(f"DataFrame {filename} está vazio mesmo após a leitura.")
            
            # Normaliza nomes de colunas
            df.columns = df.columns.str.lower().str.strip() 

            DADOS_ACADEMICOS[key] = df
                
        except Exception as e:
            print(f"❌ ERRO GRAVE no carregamento de {filename}: {e}. DataFrame de '{key}' vazio.")
            DADOS_ACADEMICOS[key] = pd.DataFrame()

    # 2. Extrair Credenciais (Alunos e Professores)
    required_cols = ['id', 'login', 'senha']
    
    for user_type in ['aluno', 'professor']:
        df_target = DADOS_ACADEMICOS.get(f'{user_type}s', pd.DataFrame()) 
        
        # O DF de Professores e Alunos deve ter as colunas 'id', 'login', e 'senha' para que o login funcione.
        if not df_target.empty and all(col in df_target.columns for col in required_cols):
            # Converte ID, login e senha para string para comparação segura
            df_target['id'] = df_target['id'].astype(str)
            df_target['login'] = df_target['login'].astype(str)
            df_target['senha'] = df_target['senha'].astype(str)
            
            # Filtra apenas as colunas de credenciais e converte para o formato esperado
            USUARIOS_CREDENCIAS[user_type] = df_target[required_cols].to_dict(orient='records')
            if len(USUARIOS_CREDENCIAS[user_type]) > 0:
                 print(f"DEBUG: Credenciais de {user_type.capitalize()} carregadas: {len(USUARIOS_CREDENCIAS[user_type])} usuários.")
        else:
            USUARIOS_CREDENCIAS[user_type] = []
            if df_target.empty:
                print(f"⚠️ AVISO: Credenciais de {user_type.capitalize()} não carregadas (DF Vazio).")
            else:
                print(f"⚠️ AVISO: Credenciais de {user_type.capitalize()} não carregadas. Colunas esperadas: {required_cols}.")


# Chama a função de carregamento no início do módulo
carregar_dados_do_csv()

# =================================================================
# --- FUNÇÃO DE AUTENTICAÇÃO ---
# =================================================================

def autenticar_usuario(login: str, senha: str, tipo: str) -> Tuple[Optional[str], Dict[str, Any]]:
    """Verifica as credenciais do usuário."""
    
    if tipo not in USUARIOS_CREDENCIAS:
        return None, {}

    for usuario in USUARIOS_CREDENCIAS[tipo]:
        # Comparação segura como String
        if str(usuario.get('login')) == login and str(usuario.get('senha')) == senha:
            user_id = str(usuario.get('id', login))
            return user_id, DADOS_ACADEMICOS

    return None, {}
