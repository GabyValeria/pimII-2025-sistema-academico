import pandas as pd
import os
from typing import Optional, Dict, Tuple, List
from pandas.errors import ParserError

# -----------------------------------------------------------------
# --- CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---
# -----------------------------------------------------------------

DIRETORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))

CAMINHO_BASE_DADOS = os.path.normpath(os.path.join(DIRETORIO_SCRIPT, '..', 'backend_c', 'dados'))

ARQUIVOS_CSV = {
    'aluno': 'alunos.csv',
    'professor': 'professores.csv',
    'admin': 'admin.csv',
    'turmas': 'turmas.csv',
    'matriculas': 'matriculas.csv',
    'atividades': 'atividades.csv',
    'notas': 'notas.csv'
}

DADOS_ACADEMICOS: Dict[str, pd.DataFrame] = {}
USUARIOS_CREDENCIAS: Dict[str, Dict[str, Tuple[str, str, str, str]]] = {}
DADOS_CARREGADOS = False

# -----------------------------------------------------------------
# --- CRIPTOGRAFIA/DESCRIPTOGRAFIA ---
# -----------------------------------------------------------------

CHAVE_CRIPTOGRAFIA = 5

def _criptografar_string(texto: str) -> str:
    """Criptografa uma string usando um deslocamento simples (Cifra de César)."""
    resultado = ""
    for char in texto:
        resultado += chr(ord(char) + CHAVE_CRIPTOGRAFIA)
    return resultado

def _descriptografar_string(texto: str) -> str:
    """Descriptografa uma string usando um deslocamento simples (Cifra de César)."""
    resultado = ""
    for char in texto:
        resultado += chr(ord(char) - CHAVE_CRIPTOGRAFIA)
    return resultado

# -----------------------------------------------------------------
# --- FUNÇÕES DE CARREGAMENTO E AUTENTICAÇÃO ---
# -----------------------------------------------------------------

def _carregar_df_csv(nome_chave: str, nome_arquivo: str) -> Optional[pd.DataFrame]:
    """Tenta carregar um DataFrame de um CSV, tratando caminhos e erros."""
    # Tenta carregar o arquivo a partir do diretório do script (caso de execução direta)
    caminho_completo_script = os.path.join(DIRETORIO_SCRIPT, nome_arquivo)
    
    # Tenta carregar o arquivo a partir do CAMINHO_BASE_DADOS (caso de execução no sistema)
    caminho_completo_base = os.path.join(CAMINHO_BASE_DADOS, nome_arquivo)
    
    caminho_final = None
    if os.path.exists(caminho_completo_script):
        caminho_final = caminho_completo_script
    elif os.path.exists(caminho_completo_base):
        caminho_final = caminho_completo_base
    else:
        # Tenta carregar o arquivo no diretório pai ou atual (Fallback)
        if os.path.exists(os.path.join(DIRETORIO_SCRIPT, '..', nome_arquivo)):
            caminho_final = os.path.join(DIRETORIO_SCRIPT, '..', nome_arquivo)
        elif os.path.exists(os.path.join(DIRETORIO_SCRIPT, nome_arquivo)):
            caminho_final = os.path.join(DIRETORIO_SCRIPT, nome_arquivo)
        else:
            print(f"AVISO: Arquivo CSV não encontrado para {nome_chave} nos caminhos esperados.")
            return pd.DataFrame() 

    try:
        # Tenta carregar, forçando a codificação UTF-8 ou Latin-1
        # IMPORTANTE: dtype=str garante que IDs numéricos não quebrem comparações com strings
        try:
            df = pd.read_csv(caminho_final, encoding='utf-8', dtype=str)
        except UnicodeDecodeError:
            df = pd.read_csv(caminho_final, encoding='latin-1', dtype=str)
            
        # Limpa espaços em branco nos nomes das colunas (ex: " ID " vira "ID")
        df.columns = df.columns.str.strip()
        
        # Limpa espaços em branco em TODOS os valores de texto da tabela
        # Isso resolve problemas onde "1 " (com espaço) não bate com "1"
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        return df

    except ParserError as e:
        print(f"ERRO: Falha ao analisar o CSV '{nome_arquivo}'. Verifique a formatação: {e}")
    except Exception as e:
        print(f"ERRO: Falha inesperada ao carregar '{nome_arquivo}': {e}")
        
    return pd.DataFrame()


def carregar_dados_academicos():
    """Carrega todos os dados do CSV para as variáveis globais."""
    global DADOS_ACADEMICOS, USUARIOS_CREDENCIAS, DADOS_CARREGADOS

    if DADOS_CARREGADOS:
        return

    DADOS_ACADEMICOS = {}
    USUARIOS_CREDENCIAS = {}

    # Carregar todos os dados
    for chave, arquivo in ARQUIVOS_CSV.items():
        df = _carregar_df_csv(chave, arquivo)
        if df is not None:
            DADOS_ACADEMICOS[chave] = df

    # Depois de carregar, construir as credenciais
    _carregar_credenciais_e_nomes()
    DADOS_CARREGADOS = True
    print("INFO: Dados Acadêmicos e Credenciais carregados.")

def _carregar_credenciais_e_nomes():
    """Carrega e popula o dicionário USUARIOS_CREDENCIAS, assumindo que senhas no CSV JÁ ESTÃO CRIPTOGRAFADAS."""
    global USUARIOS_CREDENCIAS
    dados = DADOS_ACADEMICOS

    mapa_tipos = {
        'aluno': 'aluno',
        'professor': 'professor',
        'admin': 'admin'
    }

    for chave_dados, tipo_usuario in mapa_tipos.items():
        df_usuario = dados.get(chave_dados)
        USUARIOS_CREDENCIAS[tipo_usuario] = {}
        
        if df_usuario is not None and not df_usuario.empty and 'Login' in df_usuario.columns and 'Senha' in df_usuario.columns:
            for _, row in df_usuario.iterrows():
                login = str(row.get('Login', '')).strip().lower()
                # A senha no CSV é tratada como já criptografada
                senha_armazenada = str(row.get('Senha', '')).strip() 
                
                if login and senha_armazenada:
                    # Não criptografa novamente; armazena a string do CSV
                    senha_criptografada = senha_armazenada 
                    id_usuario = str(row.get('ID', '')).strip()
                    nome_usuario = str(row.get('Nome', f"{tipo_usuario.capitalize()} {id_usuario}")).strip()
                    
                    # Armazena (tipo, id_usuario, nome_usuario, senha_criptografada)
                    USUARIOS_CREDENCIAS[tipo_usuario][login] = (tipo_usuario, id_usuario, nome_usuario, senha_criptografada)


def autenticar_usuario(login: str, senha: str) -> Optional[Tuple[str, str, str]]:
    """
    Verifica as credenciais. Retorna (tipo, id_usuario, nome_usuario) em caso de sucesso.
    Compara a senha de entrada plana com a senha armazenada (DESCRIPTOGRAFADA).
    """
    if not DADOS_CARREGADOS:
        carregar_dados_academicos()
    
    login = login.strip().lower()
    senha_plana_input = senha.strip() 

    for tipo_usuario, credenciais_map in USUARIOS_CREDENCIAS.items():
        if login in credenciais_map:
            tipo, id_usuario, nome_usuario, senha_criptografada_armazenada = credenciais_map[login]
            
            # Descriptografa a senha armazenada para comparar com a senha plana de entrada
            senha_descriptografada_armazenada = _descriptografar_string(senha_criptografada_armazenada) 
            
            # Compara a senha plana de entrada com a senha descriptografada armazenada
            if senha_plana_input == senha_descriptografada_armazenada: 
                return (tipo, id_usuario, nome_usuario)
                
    return None


def get_dados_academicos() -> Dict[str, pd.DataFrame]:
    """Retorna os dados acadêmicos carregados."""
    carregar_dados_academicos()
    return DADOS_ACADEMICOS

# -----------------------------------------------------------------
# --- FUNÇÕES DE PRÉ-PROCESSAMENTO PARA IA ---
# -----------------------------------------------------------------

def preparar_dados_para_ia(id_usuario: str, tipo_usuario: str) -> str:
    """
    Prepara e formata os dados para serem enviados ao módulo de IA.
    Ajustado para usar os novos cabeçalhos de CSV e a nova estrutura de notas.
    """
    dados = get_dados_academicos()
    id_usuario = str(id_usuario).strip()
    saida_formatada: List[str] = []

    if tipo_usuario == 'aluno':
        # 1. Obter DataFrames
        df_notas = dados.get('notas')
        df_atividades = dados.get('atividades')
        df_turmas = dados.get('turmas')
        df_alunos = dados.get('aluno')

        if df_notas is None or df_atividades is None or df_turmas is None or df_alunos is None:
             return "ERRO: Dados insuficientes (Notas, Atividades, Turmas ou Alunos ausentes) para análise de aluno."
        
        # Obter o nome do aluno
        nome_aluno_row = df_alunos[df_alunos['ID'].astype(str) == id_usuario]
        nome_aluno = nome_aluno_row.iloc[0]['Nome'] if not nome_aluno_row.empty else f"Aluno ID {id_usuario}"

        saida_formatada.append(f"RELATORIO_NOTAS_ALUNO: {nome_aluno}")
        
        # Filtra notas do aluno (usando o novo cabeçalho 'ID_Aluno' em notas.csv)
        df_notas['ID_Aluno'] = df_notas['ID_Aluno'].astype(str).str.strip()
        df_notas_aluno = df_notas[df_notas['ID_Aluno'] == id_usuario].copy()
        
        if df_notas_aluno.empty:
            saida_formatada.append("RELATORIO_NOTAS: Aluno não possui notas registradas.")
        else:
            # Mescla notas com atividades (para obter ID_Turma, Nome_Atividade e Peso)
            # Renomeia 'ID' de atividades para 'ID_Atividade_fk' para evitar conflito
            df_merge = pd.merge(
                df_notas_aluno,
                df_atividades[['ID', 'ID_Turma', 'Nome_Atividade', 'Peso']].rename(columns={'ID': 'ID_Atividade_fk'}),
                left_on='ID_Atividade',
                right_on='ID_Atividade_fk',
                how='left',
            )
            
            # Mescla com turmas (para obter Nome da Disciplina)
            # AJUSTE: Renomeia 'Nome' de turmas para 'Nome_Disciplina'
            df_merge = pd.merge(
                df_merge,
                df_turmas[['ID', 'Nome']].rename(columns={'ID': 'ID_Turma', 'Nome': 'Nome_Disciplina'}),
                left_on='ID_Turma',
                right_on='ID_Turma',
                how='left',
            )
            
            # Garante que as colunas são numéricas
            df_merge['Nota'] = pd.to_numeric(df_merge['Nota'], errors='coerce').fillna(0)
            df_merge['Peso'] = pd.to_numeric(df_merge['Peso'], errors='coerce').fillna(0)

            # Calcula a nota ponderada: Nota * (Peso/100)
            df_merge['Nota_Ponderada'] = df_merge['Nota'] * (df_merge['Peso'] / 100.0)
            
            # Calcula média ponderada por disciplina (a soma das notas ponderadas é a média final)
            medias_por_disciplina = df_merge.groupby('Nome_Disciplina')['Nota_Ponderada'].sum().reset_index()
            
            for _, row in medias_por_disciplina.iterrows():
                disciplina = str(row['Nome_Disciplina']).strip()
                media = row['Nota_Ponderada']
                saida_formatada.append(f"{disciplina}: {media:.2f}")

    elif tipo_usuario == 'professor':
        # 1. Certifica-se de que todos os DataFrames necessários estão carregados
        df_turmas = dados.get('turmas')
        df_professores = dados.get('professor')
        df_notas = dados.get('notas') 
        df_atividades = dados.get('atividades') 
        
        if df_turmas is None or df_professores is None or df_notas is None or df_atividades is None:
             return "ERRO: Dados insuficientes (Turmas, Professores, Notas ou Atividades ausentes) para análise de professor."

        # Obter o nome do professor
        nome_prof_row = df_professores[df_professores['ID'].astype(str) == id_usuario]
        nome_professor = nome_prof_row.iloc[0]['Nome'] if not nome_prof_row.empty else f"Professor ID {id_usuario}"
        
        saida_formatada.append(f"RELATORIO_PROFESSOR: {nome_professor}")
        
        # Garante que a coluna ID_Professor_Responsavel existe e a filtra
        if 'ID_Professor_Responsavel' in df_turmas.columns:
            
            # Garante que a coluna de ID do professor em turmas é string para comparação
            df_turmas['ID_Professor_Responsavel'] = df_turmas['ID_Professor_Responsavel'].astype(str).str.strip()
            
            # 2. Filtra turmas sob responsabilidade do professor
            turmas_do_prof = df_turmas[df_turmas['ID_Professor_Responsavel'] == id_usuario].copy()
            saida_formatada.append(f"Total_Turmas: {len(turmas_do_prof)}")
            
            if not turmas_do_prof.empty:
                
                # --- Lógica de Cálculo de Média e Desvio Padrão ---
                
                # 3. Obter IDs das turmas do professor
                ids_turmas_do_prof = turmas_do_prof['ID'].unique()
                
                # 4. Filtrar atividades associadas a essas turmas
                df_atividades['ID_Turma'] = df_atividades['ID_Turma'].astype(str).str.strip()
                df_atividades_do_prof = df_atividades[df_atividades['ID_Turma'].isin(ids_turmas_do_prof)].copy()
                
                media_turma = 0.0
                desvio_padrao = 0.0
                
                if not df_atividades_do_prof.empty:
                    
                    # 5. Filtrar notas que pertencem a estas atividades
                    # Renomeia ID para evitar conflito no merge
                    df_atividades_do_prof.rename(columns={'ID': 'ID_Atividade_Prof'}, inplace=True)
                    
                    df_notas['ID_Atividade'] = df_notas['ID_Atividade'].astype(str).str.strip()
                    df_notas_do_prof = pd.merge(
                        df_notas,
                        df_atividades_do_prof[['ID_Atividade_Prof']],
                        left_on='ID_Atividade',
                        right_on='ID_Atividade_Prof',
                        how='inner' # Pega apenas as notas de atividades do professor
                    )
                    
                    # 6. Calcular Média e Desvio Padrão (convertendo para numérico com segurança)
                    df_notas_do_prof['Nota'] = pd.to_numeric(df_notas_do_prof['Nota'], errors='coerce')
                    
                    # Calcula a média de todas as notas do professor
                    if not df_notas_do_prof['Nota'].empty:
                        media_turma = df_notas_do_prof['Nota'].mean()
                        desvio_padrao = df_notas_do_prof['Nota'].std() if df_notas_do_prof['Nota'].std() is not None else 0.0
                
                # 7. Adicionar ao relatório com os nomes de chave ESPERADOS pelo ai_module.py
                saida_formatada.append(f"Media_Turma: {media_turma:.2f}")
                saida_formatada.append(f"Desvio_Padrao: {desvio_padrao:.2f}")

                # 8. Adicionar lista de turmas para contexto
                for _, row in turmas_do_prof.iterrows():
                    disciplina = str(row.get('Nome', 'N/A')).strip() 
                    codigo = str(row.get('Codigo', 'N/A')).strip()
                    saida_formatada.append(f"Turma: {disciplina} ({codigo})")
            else:
                saida_formatada.append("INFO: Professor não possui turmas sob sua responsabilidade.")
                # Adiciona 0.00 para evitar que o ai_module.py retorne a mensagem de erro padrão
                saida_formatada.append("Media_Turma: 0.00") 
                saida_formatada.append("Desvio_Padrao: 0.00")
        else:
            saida_formatada.append("ERRO: Coluna 'ID_Professor_Responsavel' não encontrada em turmas.csv.")
            saida_formatada.append("Media_Turma: 0.00") 
            saida_formatada.append("Desvio_Padrao: 0.00")

    elif tipo_usuario == 'admin' or tipo_usuario == 'administrador':
        df_alunos = dados.get('aluno')
        df_professores = dados.get('professor')
        df_turmas = dados.get('turmas')
        
        if df_alunos is None or df_professores is None or df_turmas is None:
             return "ERRO: Dados insuficientes (Alunos, Professores ou Turmas ausentes) para análise administrativa."
        
        saida_formatada.append("RELATORIO_ADMINISTRADOR:")
        # Agora podemos calcular os totais com segurança, pois os DFs existem
        total_alunos = df_alunos.shape[0]
        total_professores = df_professores.shape[0]
        total_turmas = df_turmas.shape[0]
        
        saida_formatada.append(f"Total_Alunos: {total_alunos}")
        saida_formatada.append(f"Total_Professores: {total_professores}")
        saida_formatada.append(f"Total_Turmas: {total_turmas}")

        # Simulação de métrica administrativa
        taxa_evasao_simulada = 0.05
        if total_alunos > 100:
             taxa_evasao_simulada = 0.12 # Exemplo: aumenta a evasão em sistemas maiores
        
        saida_formatada.append(f"Taxa_Evasao_Ultimo_Semestre: {taxa_evasao_simulada}")        

    return "\n".join(saida_formatada)


def get_colunas_csv(tipo: str) -> Optional[List[str]]:
    """Retorna o cabeçalho do CSV para um tipo de dado específico."""
    carregar_dados_academicos()
    df = DADOS_ACADEMICOS.get(tipo)
    if df is not None:
        return list(df.columns)
    return None
