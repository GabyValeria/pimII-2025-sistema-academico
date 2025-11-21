import customtkinter as ctk
from data_manager import get_dados_academicos, preparar_dados_para_ia
from ai_module import gerar_relatorio_ia
import pandas as pd
from fpdf import FPDF
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, Dict, Any, Tuple 

# --- Configurações Iniciais do CTk ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Cores
PRIMARY_BLUE = "#1F77B4" 
LIGHT_GRAY_BG = "#F5F5F5"
CARD_BG = "#FFFFFF" 
ERROR_RED = "#DC143C"
SUCCESS_GREEN = "#28a745"
DARK_GRAY = "#333333"

# =================================================================
# --- CLASSE 1: App (Janela Principal) ---
# =================================================================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Acadêmico com Apoio de IA")
        self.geometry("1000x650")
        self.configure(fg_color=LIGHT_GRAY_BG)
        
        self.dados_academicos: Dict[str, pd.DataFrame] = {}
        self.id_usuario: Optional[str] = None
        self.nivel_acesso: Optional[str] = None
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.login_frame = LoginFrame(self, self.callback_login_sucesso)
        self.login_frame.grid(row=0, column=0, sticky="nsew")

    def callback_login_sucesso(self, id_usuario, nivel, dados):
        """Callback chamado após a autenticação bem-sucedida."""
        self.id_usuario = id_usuario
        self.nivel_acesso = nivel
        self.dados_academicos = dados
        
        if hasattr(self, 'login_frame'):
            self.login_frame.destroy()
            
        self.main_frame = MainFrame(self, self.id_usuario, self.nivel_acesso, self.dados_academicos, self.logout)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Exibe a tela inicial apropriada
        if nivel == 'aluno':
            self.main_frame.exibir_dashboard_aluno()
        elif nivel == 'admin':
            self.main_frame.exibir_dashboard_admin()
        elif nivel == 'professor': 
            self.main_frame.exibir_dashboard_professor()
        else:
             # Fallback
            self.main_frame.exibir_dashboard_professor()


    def logout(self):
        """Destrói o frame principal e volta para a tela de login."""
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()
            
        self.id_usuario = None
        self.nivel_acesso = None
        self.dados_academicos = {}
        
        self.login_frame = LoginFrame(self, self.callback_login_sucesso)
        self.login_frame.grid(row=0, column=0, sticky="nsew")

# =================================================================
# --- CLASSE 2: LoginFrame ---
# =================================================================

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, callback_sucesso):
        super().__init__(master, fg_color=LIGHT_GRAY_BG)
        self.callback_sucesso = callback_sucesso
        self.master_app = master

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Card de Login
        self.login_card = ctk.CTkFrame(self, width=700, height=450, corner_radius=15, fg_color=CARD_BG)
        self.login_card.grid(row=0, column=0, sticky="") 
        
        self.auth_panel = ctk.CTkFrame(self.login_card, fg_color="transparent")
        self.auth_panel.grid(row=0, column=0, sticky="nsew", padx=50, pady=50)
        self.auth_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.auth_panel, text="SISTEMA DE ACESSO", font=ctk.CTkFont(size=20, weight="bold"), text_color=PRIMARY_BLUE).grid(row=0, column=0, pady=(0, 20))

        self.acesso_var = ctk.StringVar(value="aluno")
        self.seg_button = ctk.CTkSegmentedButton(self.auth_panel, variable=self.acesso_var, values=["aluno", "professor", "admin"], width=250, height=30)
        self.seg_button.grid(row=1, column=0, pady=10)

        self.login_entry = ctk.CTkEntry(self.auth_panel, placeholder_text="Login", width=250, height=40)
        self.login_entry.grid(row=2, column=0, pady=10)
        
        self.senha_entry = ctk.CTkEntry(self.auth_panel, placeholder_text="Senha", show="*", width=250, height=40)
        self.senha_entry.grid(row=3, column=0, pady=10)

        self.login_button = ctk.CTkButton(self.auth_panel, text="ENTRAR", command=self.tentar_login, width=250, height=40, fg_color=PRIMARY_BLUE)
        self.login_button.grid(row=4, column=0, pady=(20, 10))

        self.exit_button = ctk.CTkButton(self.auth_panel, text="SAIR", command=self.master_app.destroy, width=250, height=40, fg_color=ERROR_RED, hover_color="#B20C2D")
        self.exit_button.grid(row=5, column=0, pady=(10, 10))
        
        self.info_label = ctk.CTkLabel(self.auth_panel, text="", text_color=ERROR_RED)
        self.info_label.grid(row=6, column=0, pady=5)
        
    def tentar_login(self):
        login = self.login_entry.get().strip()
        senha = self.senha_entry.get().strip()
        tipo_selecionado = self.acesso_var.get()

        if not login or not senha:
            self.info_label.configure(
                text="⚠️ Preencha todos os campos antes de continuar.",
                text_color=ERROR_RED
            )
            return

        from data_manager import autenticar_usuario, DADOS_ACADEMICOS, USUARIOS_CREDENCIAS

        self.info_label.configure(text="Verificando credenciais...", text_color=DARK_GRAY)
        self.master_app.update_idletasks()

        try:
            resultado_auth = autenticar_usuario(login, senha)

            if resultado_auth is None:
                # Diagnóstico detalhado
                if not DADOS_ACADEMICOS:
                    msg = "⚠️ Nenhum dado foi carregado. Verifique os arquivos CSV."
                elif not any(USUARIOS_CREDENCIAS.values()):
                    msg = "⚠️ Nenhum usuário encontrado nos dados carregados."
                else:
                    msg = "❌ Login ou senha incorretos."
                self.info_label.configure(text=msg, text_color=ERROR_RED)
                return

            # Desempacota o retorno
            tipo_usuario, id_usuario, nome_usuario = resultado_auth
            dados = get_dados_academicos()

            # Verifica o nível de acesso (o tipo_usuario retornado DEVE ser o singular ('aluno', 'professor', 'admin'))
            if tipo_usuario != tipo_selecionado:
                self.info_label.configure(
                    text=f"⚠️ Nível de acesso incorreto: este usuário pertence a '{tipo_usuario}'.",
                    text_color=ERROR_RED
                )
                return

            # Verifica se os dados foram carregados corretamente (usando as chaves singulares)
            if not dados or any(df.empty for key, df in dados.items() if key in ['aluno', 'professor', 'turmas']):
                self.info_label.configure(
                    text="⚠️ Login válido, mas dados acadêmicos não foram carregados.",
                    text_color=ERROR_RED
                )
                return

            # Sucesso
            self.info_label.configure(
                text=f"✅ Bem-vindo, {nome_usuario} ({tipo_usuario})!",
                text_color=SUCCESS_GREEN
            )
            self.callback_sucesso(id_usuario, tipo_usuario, dados)

        except Exception as e:
            self.info_label.configure(
                text=f"❌ Erro inesperado no login: {str(e)}",
                text_color=ERROR_RED
            )

# =================================================================
# --- CLASSE 3: MainFrame (Lógica Central) ---
# =================================================================

class MainFrame(ctk.CTkFrame):
    def __init__(self, master, id_usuario, nivel_acesso, dados, callback_logout):
        super().__init__(master, fg_color=LIGHT_GRAY_BG)
        self.id_usuario = id_usuario
        self.nivel_acesso = nivel_acesso
        self.dados = dados
        self.callback_logout = callback_logout
        self.grafico_canvas = None 
        self.content_container_table = None 

        # Variáveis de Estado para IA/PDF
        self.last_ia_report_name = ""
        self.last_ia_report_data = ""
        self.last_ia_report_type = ""
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color=PRIMARY_BLUE) 
        self.sidebar_frame.grid(row=0, column=0, sticky="nswe")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        # Nome do Usuário na Sidebar
        nome_display = id_usuario.upper()
        df_display = self.dados.get(nivel_acesso, pd.DataFrame()) # Busca no df de aluno/professor/admin
        
        # A coluna de Nome é 'Nome' em alunos/admin/professores.
        if not df_display.empty and 'ID' in df_display.columns and 'Nome' in df_display.columns:
            user_info = df_display[df_display['ID'].astype(str) == str(self.id_usuario)]
            if not user_info.empty:
                nome_display = user_info.iloc[0]['Nome']
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=f"Sistema Acadêmico\n {nome_display}", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        button_font = ctk.CTkFont(size=14, weight="bold")
        
        # Botões de Navegação (Aluno)
        if nivel_acesso == 'aluno':
            ctk.CTkButton(self.sidebar_frame, text="Início", command=self.exibir_dashboard_aluno, fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=1, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Minhas Matrículas", command=lambda: self.exibir_dados('matriculas_aluno'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=2, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Meu Desempenho", command=self.exibir_notas_aluno_com_grafico, fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=3, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Relatório IA (PDF)", command=self.gerar_relatorio_ia_pdf, fg_color=ERROR_RED, font=button_font).grid(row=4, column=0, padx=20, pady=10)
        
        # Botões de Navegação (Professor)
        elif nivel_acesso == 'professor':
            ctk.CTkButton(self.sidebar_frame, text="Início", command=self.exibir_dashboard_professor, fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=1, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Minhas Turmas", command=lambda: self.exibir_dados('turmas_prof'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=2, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Meus Alunos", command=lambda: self.exibir_dados_prof_detalhado('alunos'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=3, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Minhas Atividades", command=lambda: self.exibir_dados_prof_detalhado('atividades'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=4, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Análise Turma (IA)", command=lambda: self.analisar_dados_ia('professor'), fg_color=ERROR_RED, font=button_font).grid(row=5, column=0, padx=20, pady=10)

        # Botões de Navegação (Admin)
        elif nivel_acesso == 'admin':
            ctk.CTkButton(self.sidebar_frame, text="Início", command=self.exibir_dashboard_admin, fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=1, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Alunos", command=lambda: self.exibir_dados('aluno_data'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=2, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Professores", command=lambda: self.exibir_dados('professor_data'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=3, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Turmas", command=lambda: self.exibir_dados('turmas'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=4, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Análise Geral (IA)", command=lambda: self.analisar_dados_ia('admin'), fg_color=ERROR_RED, font=button_font).grid(row=5, column=0, padx=20, pady=10)


        ctk.CTkButton(self.sidebar_frame, text="Sair", command=self.callback_logout, fg_color=ERROR_RED, font=button_font).grid(row=8, column=0, padx=20, pady=(10, 20)) 

        # --- Main Content ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=CARD_BG)
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_content_frame.grid_rowconfigure(1, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        self.current_display_label = ctk.CTkLabel(self.main_content_frame, text="Bem-vindo ao Sistema Acadêmico!", font=ctk.CTkFont(size=16, weight="bold"), text_color=DARK_GRAY)
        self.current_display_label.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        # Container principal com scroll
        self.content_container = ctk.CTkScrollableFrame(self.main_content_frame, label_text="Visualização de Dados", fg_color=LIGHT_GRAY_BG, label_text_color=DARK_GRAY)
        self.content_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
    
    # ==========================================================
    # --- FUNÇÕES AUXILIARES DE UI ---
    # ==========================================================
    
    def _limpar_container(self):
        """Limpa todos os widgets do content_container e destrói o gráfico."""
        for widget in self.content_container.winfo_children():
            widget.destroy()
        
        if self.content_container_table:
            self.content_container_table.destroy()
            self.content_container_table = None
            self.main_content_frame.grid_rowconfigure(2, weight=0) 

        if self.grafico_canvas:
            self.grafico_canvas.get_tk_widget().destroy()
            self.grafico_canvas = None

    def _criar_kpi_card_custom(self, frame, label_text, value_text, color=PRIMARY_BLUE):
        """Cria um cartão de KPI."""
        card = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=10, height=80)
        label = ctk.CTkLabel(card, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color="#606060")
        value = ctk.CTkLabel(card, text=value_text, font=ctk.CTkFont(size=24, weight="bold"), text_color=color)
        
        card.grid_columnconfigure(0, weight=1)
        label.grid(row=0, column=0, padx=15, pady=(10, 0), sticky="w")
        value.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")
        return card

    # ==========================================================
    # --- FUNÇÕES DE DASHBOARD/TABELAS ---
    # ==========================================================

    def _encontrar_coluna(self, df: pd.DataFrame, possiveis_nomes: list) -> str:
        """Retorna o nome real da coluna no DataFrame procurando por variações."""
        cols_lower = {c.lower(): c for c in df.columns}
        for nome in possiveis_nomes:
            if nome.lower() in cols_lower:
                return cols_lower[nome.lower()]
        return None
    
    def _exibir_tabela_formatada(self, df: pd.DataFrame, title: str, parent_frame: ctk.CTkFrame):
        """Exibe um DataFrame como uma tabela formatada."""
        
        # Limpa o frame de destino (se for o content_container, será limpo antes)
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        table_frame = ctk.CTkFrame(parent_frame, fg_color=CARD_BG, corner_radius=10)
        table_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        parent_frame.grid_columnconfigure(0, weight=1) # Faz a tabela se expandir
        parent_frame.grid_rowconfigure(0, weight=1)

        # Título
        ctk.CTkLabel(table_frame, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=PRIMARY_BLUE).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        if df.empty:
            ctk.CTkLabel(table_frame, text="Nenhum dado para exibir.", text_color=DARK_GRAY).grid(row=1, column=0, padx=15, pady=10, sticky="w")
            return

        max_cols = min(len(df.columns), 8) 
        for j in range(max_cols):
            table_frame.grid_columnconfigure(j, weight=1)

        # Cabeçalho
        for j, col_name in enumerate(df.columns[:max_cols]):
            header = ctk.CTkLabel(table_frame, text=col_name.upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color=DARK_GRAY, fg_color=LIGHT_GRAY_BG, corner_radius=5)
            header.grid(row=1, column=j, padx=2, pady=2, sticky="ew")

        # Dados
        for i, row in df.iterrows():
            for j, value in enumerate(row.iloc[:max_cols]):
                bg_color = CARD_BG if i % 2 == 0 else LIGHT_GRAY_BG
                cell = ctk.CTkLabel(table_frame, text=str(value), font=ctk.CTkFont(size=12), text_color=DARK_GRAY, fg_color=bg_color, corner_radius=0)
                cell.grid(row=i + 2, column=j, padx=2, pady=1, sticky="ew")

    def exibir_dados(self, tipo):
        """Função unificada para exibir diferentes tipos de dados em tabela."""
        self._limpar_container()
        dfs = self.dados
        
        # --- LÓGICA DE TURMAS (Professor filtra, Admin vê todas) ---
        if tipo.startswith('turmas') and 'turmas' in dfs:
            df_turmas_orig = dfs['turmas'].copy()
            id_prof_col = 'ID_Professor_Responsavel'
            
            df_display = df_turmas_orig
            display_name = "Lista de Turmas"
            
            # FILTRO PARA PROFESSOR (acesso 'professor' ou tipo 'turmas_prof')
            if self.nivel_acesso == 'professor' or tipo == 'turmas_prof':
                self.current_display_label.configure(text="Visualizando: MINHAS TURMAS")
                
                if id_prof_col in df_turmas_orig.columns:
                    # Garante que a coluna ID seja string para comparação 
                    df_turmas_orig[id_prof_col] = df_turmas_orig[id_prof_col].astype(str)
                    
                    # Aplica o filtro para mostrar APENAS as turmas do professor logado
                    df_display = df_turmas_orig[df_turmas_orig[id_prof_col].str.strip() == str(self.id_usuario)]
                    display_name = f"Minhas Turmas (Prof. {self.id_usuario})"
                else:
                    self._exibir_tabela_formatada(pd.DataFrame(), "ERRO: Coluna de ID de Professor ('ID_Professor_Responsavel') não encontrada em Turmas.", self.content_container)
                    return 
            
            # PARA ADMIN (tipo 'turmas')
            elif self.nivel_acesso == 'admin' and tipo == 'turmas':
                 self.current_display_label.configure(text="Visualizando: TODAS AS TURMAS (ADMIN)")
                 display_name = "Todas as Turmas"
                 df_display = df_turmas_orig
            else:
                self.current_display_label.configure(text="Visualizando: ACESSO NÃO AUTORIZADO / DADOS INDISPONÍVEIS")
                return

            self._exibir_tabela_formatada(df_display, display_name, self.content_container)
            return

        # --- LÓGICA DE MATRÍCULAS DO ALUNO ---
        elif tipo == 'matriculas_aluno' and 'matriculas' in dfs and 'turmas' in dfs:
            self.current_display_label.configure(text="Visualizando: MINHAS MATRÍCULAS")
            id_aluno_col = 'ID_Aluno'
            
            if id_aluno_col not in dfs['matriculas'].columns:
                ctk.CTkLabel(self.content_container, text="Erro: Coluna 'ID_Aluno' não encontrada na tabela de matrículas.", text_color=ERROR_RED).grid(row=0, column=0, padx=10, pady=10)
                return

            minhas_matriculas = dfs['matriculas'][dfs['matriculas'][id_aluno_col].astype(str) == str(self.id_usuario)]
            turmas_info = dfs.get('turmas', pd.DataFrame())
            
            # Garante que as colunas de merge sejam strings
            turmas_info['ID'] = turmas_info['ID'].astype(str) 
            minhas_matriculas['ID_Turma'] = minhas_matriculas['ID_Turma'].astype(str) 
            
            # Merge usando as chaves corrigidas
            df_display = pd.merge(minhas_matriculas, turmas_info, left_on='ID_Turma', right_on='ID', how='left', suffixes=('_mat', '_turma'))
            
            # NOVO CABEÇALHO: 'Nome' (para nome da disciplina)
            nome_col_turma = next((col for col in ['Nome', 'Nome_Disciplina_turma'] if col in df_display.columns), None) 
            semestre_col = next((col for col in ['Semestre', 'Semestre_turma'] if col in df_display.columns), None)

            if not nome_col_turma or not semestre_col:
                ctk.CTkLabel(self.content_container, text="Aviso: Coluna de nome da disciplina ('Nome') ou 'Semestre' não foi encontrada na tabela de Turmas.", text_color=ERROR_RED).grid(row=0, column=0, padx=10, pady=10)
                return
            
            # Prepara o DataFrame final
            cols_to_show = [c for c in [nome_col_turma, semestre_col] if c in df_display.columns]
            df_final = df_display[cols_to_show].copy() 
            df_final = df_final.rename(columns={nome_col_turma: 'Disciplina', semestre_col: 'Semestre'})
            
            self._exibir_tabela_formatada(df_final, "Minhas Matrículas", self.content_container)

        # --- LÓGICA DE DADOS GERAIS (Admin e Professor/Aluno: 'aluno_data', 'professor_data') ---
        else: 
            data_key = tipo.replace('_data', '').replace('s', '')
            display_name = tipo.replace('_data', '').capitalize()
            
            # Ajusta data_key caso o tipo seja 'aluno_data' ou 'professor_data' (tipos usados pelo Admin)
            if tipo.startswith('professor_data'): 
                data_key = 'professor'
            elif tipo.startswith('aluno_data'):
                 data_key = 'aluno'
            elif tipo.startswith('admin_data'):
                 data_key = 'admin'
            
            if data_key in ['aluno', 'professor', 'admin'] and data_key in dfs:
                self.current_display_label.configure(text=f"Visualizando: {display_name.upper()}")
                self._exibir_tabela_formatada(dfs[data_key], f"Lista de {display_name.capitalize()}", self.content_container)
            
            else:
                 self.current_display_label.configure(text=f"Dados de {tipo} Indisponíveis.")

    def _calcular_medias(self) -> Tuple[Dict[str, float], str]:
        """Calcula a média ponderada do aluno de forma robusta."""
        dfs = self.dados
        
        # Verifica se as tabelas necessárias existem
        required = ['matriculas', 'turmas', 'atividades', 'notas']
        if any(k not in dfs for k in required):
             return {}, "ERRO: Dados incompletos (tabelas faltando no CSV)."

        aluno_id_str = str(self.id_usuario).strip()
        
        # 1. Encontrar nomes corretos das colunas na tabela de Matrículas
        col_id_aluno_mat = self._encontrar_coluna(dfs['matriculas'], ['ID_Aluno', 'Aluno_ID', 'RA'])
        col_id_turma_mat = self._encontrar_coluna(dfs['matriculas'], ['ID_Turma', 'Turma_ID'])
        
        if not col_id_aluno_mat or not col_id_turma_mat:
             return {}, "ERRO: Colunas de ID de Aluno ou Turma não encontradas no arquivo matriculas.csv."

        # 2. Filtrar matrículas do aluno logado
        minhas_matriculas = dfs['matriculas'][dfs['matriculas'][col_id_aluno_mat].astype(str) == aluno_id_str]
        
        if minhas_matriculas.empty:
            return {}, "AVISO: Nenhuma matrícula encontrada para este aluno."

        medias = {}
        relatorio_detalhado = ""

        # 3. Iterar sobre cada turma que o aluno está matriculado
        for id_turma in minhas_matriculas[col_id_turma_mat].unique():
            id_turma_str = str(id_turma)
            
            # Busca nome da Turma para exibir no relatório
            turma_row = dfs['turmas'][dfs['turmas']['ID'].astype(str) == id_turma_str]
            nome_turma = f"Turma {id_turma_str}"
            if not turma_row.empty:
                col_nome = self._encontrar_coluna(dfs['turmas'], ['Nome', 'Disciplina', 'Materia'])
                if col_nome:
                    nome_turma = turma_row.iloc[0][col_nome]

            # 4. Filtrar ATIVIDADES desta turma específica
            df_atividades = dfs['atividades']
            col_id_turma_ativ = self._encontrar_coluna(df_atividades, ['ID_Turma', 'Turma_ID'])
            
            if not col_id_turma_ativ: continue
            
            # Pega todas as atividades cadastradas para essa turma
            atividades_turma = df_atividades[df_atividades[col_id_turma_ativ].astype(str) == id_turma_str]
            
            if atividades_turma.empty:
                continue

            # Identifica colunas de ID e Peso na tabela de Atividades
            col_id_ativ = self._encontrar_coluna(atividades_turma, ['ID', 'Codigo'])
            col_peso = self._encontrar_coluna(atividades_turma, ['Peso', 'Ponderacao'])
            
            # Identifica colunas na tabela de Notas
            df_notas = dfs['notas']
            col_id_aluno_nota = self._encontrar_coluna(df_notas, ['ID_Aluno', 'Aluno_ID'])
            col_id_ativ_nota = self._encontrar_coluna(df_notas, ['ID_Atividade', 'Atividade_ID'])
            col_nota_valor = self._encontrar_coluna(df_notas, ['Nota', 'Valor', 'Score'])
            
            if not all([col_id_aluno_nota, col_id_ativ_nota, col_nota_valor, col_id_ativ, col_peso]):
                continue

            # 5. Filtrar NOTAS apenas deste aluno
            notas_do_aluno = df_notas[df_notas[col_id_aluno_nota].astype(str) == aluno_id_str]

            # 6. Cruzar (Merge) as Notas do Aluno com as Atividades da Turma
            # Aqui cruzamos ID_Atividade (da nota) com ID (da atividade)
            df_calculo = pd.merge(
                notas_do_aluno,
                atividades_turma,
                left_on=col_id_ativ_nota,
                right_on=col_id_ativ,
                how='inner',
                suffixes=('_nota', '_ativ')
            )

            if df_calculo.empty:
                medias[nome_turma] = 0.0
                relatorio_detalhado += f"{nome_turma}: 0.0 (Sem notas lançadas)\n"
                continue
            
            # Resolve nomes de colunas após o merge (caso haja duplicidade)
            c_nota = col_nota_valor if col_nota_valor in df_calculo.columns else f"{col_nota_valor}_nota"
            c_peso = col_peso if col_peso in df_calculo.columns else f"{col_peso}_ativ"

            # Converte para números (para evitar erro de cálculo com texto)
            df_calculo['val_nota'] = pd.to_numeric(df_calculo[c_nota], errors='coerce').fillna(0)
            df_calculo['val_peso'] = pd.to_numeric(df_calculo[c_peso], errors='coerce').fillna(0)

            # 7. Cálculo Matemático da Média Ponderada
            soma_pond = (df_calculo['val_nota'] * df_calculo['val_peso']).sum()
            soma_pesos = df_calculo['val_peso'].sum()
            
            media_final = (soma_pond / soma_pesos) if soma_pesos > 0 else 0.0
            
            medias[nome_turma] = media_final
            relatorio_detalhado += f"{nome_turma}: {media_final:.2f}\n"

        return medias, relatorio_detalhado

    def _calcular_medias_turmas_professor(self) -> Dict[str, float]:
        """Calcula a média geral de cada turma do professor."""
        dfs = self.dados
        if 'turmas' not in dfs or 'atividades' not in dfs or 'notas' not in dfs:
            return {}

        prof_id_str = str(self.id_usuario).strip()
        
        # Identifica colunas essenciais em Turmas
        df_turmas = dfs['turmas']
        col_id_prof = self._encontrar_coluna(df_turmas, ['ID_Professor_Responsavel', 'ID_Professor', 'Professor_ID'])
        col_id_turma = self._encontrar_coluna(df_turmas, ['ID', 'Codigo'])
        col_nome_turma = self._encontrar_coluna(df_turmas, ['Nome', 'Disciplina'])
        
        if not col_id_prof: return {}

        # Filtra turmas do professor
        minhas_turmas = df_turmas[df_turmas[col_id_prof].astype(str) == prof_id_str]
        if minhas_turmas.empty: return {}

        medias_por_turma = {}

        for _, row in minhas_turmas.iterrows():
            turma_id = str(row[col_id_turma])
            turma_nome = row[col_nome_turma] if col_nome_turma else f"Turma {turma_id}"
            
            # Filtra atividades da turma
            df_atividades = dfs['atividades']
            col_turma_fk = self._encontrar_coluna(df_atividades, ['ID_Turma', 'Turma_ID'])
            if not col_turma_fk: continue
            
            atividades_turma = df_atividades[df_atividades[col_turma_fk].astype(str) == turma_id]
            
            if atividades_turma.empty:
                medias_por_turma[turma_nome] = 0.0
                continue
                
            # Merge Notas + Atividades
            df_notas = dfs['notas']
            col_ativ_id = self._encontrar_coluna(df_atividades, ['ID', 'Codigo'])
            col_ativ_peso = self._encontrar_coluna(df_atividades, ['Peso', 'Ponderacao'])
            col_nota_fk = self._encontrar_coluna(df_notas, ['ID_Atividade', 'Atividade_ID'])
            col_nota_valor = self._encontrar_coluna(df_notas, ['Nota', 'Valor'])
            
            if not all([col_ativ_id, col_ativ_peso, col_nota_fk, col_nota_valor]):
                continue
                
            df_merge = pd.merge(
                df_notas,
                atividades_turma,
                left_on=col_nota_fk,
                right_on=col_ativ_id,
                how='inner',
                suffixes=('_nota', '_ativ')
            )
            
            if df_merge.empty:
                medias_por_turma[turma_nome] = 0.0
                continue
                
            # Resolve nomes após merge
            c_nota = col_nota_valor if col_nota_valor in df_merge.columns else f"{col_nota_valor}_nota"
            c_peso = col_ativ_peso if col_ativ_peso in df_merge.columns else f"{col_ativ_peso}_ativ"
            
            # Converte e calcula
            df_merge['n'] = pd.to_numeric(df_merge[c_nota], errors='coerce').fillna(0)
            df_merge['p'] = pd.to_numeric(df_merge[c_peso], errors='coerce').fillna(0)
            
            # Média simples de todos os registros (média da turma)
            # Idealmente: calcula média de cada aluno, depois média da turma.
            # Simplificação funcional: (Soma de todas as notas ponderadas) / (Soma de todos os pesos lançados)
            soma_notas = (df_merge['n'] * df_merge['p']).sum()
            soma_pesos = df_merge['p'].sum()
            
            media_turma = (soma_notas / soma_pesos) if soma_pesos > 0 else 0.0
            medias_por_turma[turma_nome] = media_turma

        return medias_por_turma

    # Gráfico de Desempenho das Turmas
    def _gerar_grafico_desempenho_professor(self, parent_frame, medias, row):
        """Gera um gráfico de desempenho por turma para o professor."""
        
        # Limpa o gráfico anterior se existir
        if self.grafico_canvas:
            self.grafico_canvas.get_tk_widget().destroy()
        
        if not medias:
            ctk.CTkLabel(parent_frame, text="Não há médias disponíveis para gerar o gráfico.", text_color=DARK_GRAY).grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="n")
            return
            
        fig, ax = plt.subplots(figsize=(8, 4))
        
        turmas = list(medias.keys())
        valores = list(medias.values())
        
        # Cores baseadas na média (Abaixo de 6.0 é Risco, 6.0-7.5 é Atenção, acima de 7.5 é Bom)
        colors = []
        for v in valores:
            if v < 6.0:
                colors.append(ERROR_RED) # Vermelho (Risco)
            elif v < 7.5:
                colors.append(PRIMARY_BLUE) # Azul (Atenção/Médio)
            else:
                colors.append(SUCCESS_GREEN) # Verde (Bom Desempenho)
                
        ax.bar(turmas, valores, color=colors)
        ax.axhline(6.0, color='red', linestyle=':', linewidth=1, label='Risco (6.0)')
        ax.axhline(7.5, color='green', linestyle=':', linewidth=1, label='Alto (7.5)')
        ax.set_title("Média de Desempenho por Turma (Professor)")
        ax.set_ylabel("Média da Turma")
        ax.set_ylim(0, 10)
        plt.xticks(rotation=25, ha="right", fontsize=8)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas_widget = canvas.get_tk_widget()
        # Coloca o gráfico na linha especificada
        canvas_widget.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.grafico_canvas = canvas 

    # Dashboard do Professor com Gráfico
    def exibir_dashboard_professor(self):
        self._limpar_container()
        
        # 1. Título
        nome_professor = self.id_usuario 
        df_professor = self.dados.get('professor', pd.DataFrame())
        
        if not df_professor.empty and 'ID' in df_professor.columns and 'Nome' in df_professor.columns:
            prof_info = df_professor[df_professor['ID'].astype(str) == str(self.id_usuario)]
            if not prof_info.empty:
                nome_professor = prof_info.iloc[0]['Nome']
        
        self.current_display_label.configure(text=f"🎓 Início do(a) Professor(a): {nome_professor}")

        # 2. KPIs
        df_turmas = self.dados.get('turmas', pd.DataFrame())
        df_matriculas = self.dados.get('matriculas', pd.DataFrame())
        
        num_turmas = 0
        num_alunos = 0
        turmas_prof_df = pd.DataFrame()

        if 'ID_Professor_Responsavel' in df_turmas.columns:
            df_turmas['ID_Professor_Responsavel'] = df_turmas['ID_Professor_Responsavel'].astype(str)
            turmas_prof_df = df_turmas[df_turmas['ID_Professor_Responsavel'] == str(self.id_usuario)].copy()
            num_turmas = len(turmas_prof_df)

        if not turmas_prof_df.empty and 'ID_Turma' in df_matriculas.columns:
            # Obtém IDs das turmas do professor
            ids_turmas_prof = turmas_prof_df['ID'].astype(str).tolist()
            # Filtra matrículas que correspondem às turmas do professor
            df_matriculas['ID_Turma'] = df_matriculas['ID_Turma'].astype(str)
            matriculas_prof = df_matriculas[df_matriculas['ID_Turma'].isin(ids_turmas_prof)]
            # Conta o número de alunos
            if 'ID_Aluno' in matriculas_prof.columns:
                num_alunos = matriculas_prof['ID_Aluno'].nunique()

        kpi_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        kpi_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        kpi_frame.grid_columnconfigure((0, 1), weight=1, uniform="kpi_group")

        card1 = self._criar_kpi_card_custom(kpi_frame, "Total de Turmas", str(num_turmas), PRIMARY_BLUE)
        card2 = self._criar_kpi_card_custom(kpi_frame, "Total de Alunos", str(num_alunos), SUCCESS_GREEN)
        
        card1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        card2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 3. Gráfico de Desempenho das Turmas
        medias_turmas = self._calcular_medias_turmas_professor()
        
        graph_frame = ctk.CTkFrame(self.content_container, fg_color=CARD_BG, corner_radius=10)
        graph_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        graph_frame.grid_columnconfigure(0, weight=1)
        graph_frame.grid_rowconfigure(1, weight=1) # Permite o gráfico se expandir
        
        ctk.CTkLabel(graph_frame, text="Média de Desempenho por Turma", font=ctk.CTkFont(size=14, weight="bold"), text_color=DARK_GRAY).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self._gerar_grafico_desempenho_professor(graph_frame, medias_turmas, 1)

        # 4. Lista de Turmas
        self.content_container.grid_rowconfigure(2, weight=1)
        
        # Cria um container específico para a tabela para melhor layout
        turmas_table_frame = ctk.CTkFrame(self.content_container, fg_color=LIGHT_GRAY_BG)
        turmas_table_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        turmas_table_frame.grid_columnconfigure(0, weight=1)
        turmas_table_frame.grid_rowconfigure(0, weight=1)

        # Remove a coluna de ID do professor antes de exibir
        self._exibir_tabela_formatada(turmas_prof_df.drop(columns=['ID_Professor_Responsavel'], errors='ignore'), 
                                     "Visão Geral das Turmas", 
                                     turmas_table_frame)


    # Abas de detalhe do Professor (Alunos / Atividades)
    def exibir_dados_prof_detalhado(self, tipo_dado: str):
        self._limpar_container()
        
        # 1. Título
        title = "Meus Alunos (Todas as Turmas)" if tipo_dado == 'alunos' else "Minhas Atividades (Todas as Turmas)"
        self.current_display_label.configure(text=f"Visualizando: {title.upper()}")
        
        # 2. Obter turmas do professor
        df_turmas = self.dados.get('turmas', pd.DataFrame())
        df_prof_turmas = df_turmas[df_turmas['ID_Professor_Responsavel'].astype(str) == str(self.id_usuario)]
        
        if df_prof_turmas.empty:
            ctk.CTkLabel(self.content_container, text="Aviso: Nenhuma turma encontrada para este professor.", text_color=DARK_GRAY).grid(row=0, column=0, padx=10, pady=10)
            return

        # 3. Preparar o TabView (Abas)
        tab_view = ctk.CTkTabview(self.content_container, fg_color=CARD_BG)
        tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        
        # 4. Preencher as Abas
        
        # DataFrame de todos os alunos/atividades do professor
        df_alunos = self.dados.get('aluno', pd.DataFrame())
        df_matriculas = self.dados.get('matriculas', pd.DataFrame())
        df_atividades = self.dados.get('atividades', pd.DataFrame())

        
        for _, turma in df_prof_turmas.iterrows():
            turma_id = str(turma['ID'])
            turma_nome = turma.get('Nome', f"Turma ID {turma_id}") 
            tab = tab_view.add(turma_nome)
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

            if tipo_dado == 'alunos':
                # Filtra matrículas da turma
                matriculas_turma = df_matriculas[df_matriculas['ID_Turma'].astype(str) == turma_id]
                ids_alunos = matriculas_turma['ID_Aluno'].unique()
                
                # Filtra alunos
                df_alunos_turma = df_alunos[df_alunos['ID'].astype(str).isin(ids_alunos)].copy()
                
                if not df_alunos_turma.empty:
                    # Colunas de Aluno
                    cols_to_show = ['ID', 'Nome', 'RA', 'Email']
                    df_display = df_alunos_turma[[c for c in cols_to_show if c in df_alunos_turma.columns]]
                    self._exibir_tabela_formatada(df_display, f"Alunos de {turma_nome}", tab)
                else:
                    ctk.CTkLabel(tab, text="Nenhum aluno matriculado nesta turma.", text_color=DARK_GRAY).grid(row=0, column=0, padx=10, pady=10)

            elif tipo_dado == 'atividades':
                # Filtra atividades da turma
                df_atividades_turma = df_atividades[df_atividades['ID_Turma'].astype(str) == turma_id].copy()
                
                if not df_atividades_turma.empty:
                    # Colunas de Atividades. NOVO CABEÇALHO: 'Nome_Atividade'
                    cols_to_show = ['ID', 'Nome_Atividade', 'Tipo', 'Peso', 'Data_Entrega']
                    df_display = df_atividades_turma[[c for c in cols_to_show if c in df_atividades_turma.columns]]
                    # Renomeia para exibição
                    df_display = df_display.rename(columns={'Nome_Atividade': 'Nome'})
                    
                    self._exibir_tabela_formatada(df_display, f"Atividades de {turma_nome}", tab)
                else:
                    ctk.CTkLabel(tab, text="Nenhuma atividade cadastrada para esta turma.", text_color=DARK_GRAY).grid(row=0, column=0, padx=10, pady=10)

        # Garante que a primeira aba seja selecionada
        if df_prof_turmas.shape[0] > 0:
            first_tab_name = df_prof_turmas.iloc[0].get('Nome', f"Turma ID {df_prof_turmas.iloc[0]['ID']}")
            tab_view.set(first_tab_name)

    def exibir_dashboard_admin(self):
        self._limpar_container()
        self.current_display_label.configure(text="📊 Painel do Administrador")

        df_alunos = self.dados.get('aluno', pd.DataFrame()) 
        df_turmas = self.dados.get('turmas', pd.DataFrame())
        df_professores = self.dados.get('professor', pd.DataFrame()) 

        # --- 1. KPIs (Cards Superiores) ---
        kpi_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        kpi_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        kpi_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="kpi_group")

        total_alunos = len(df_alunos) if not df_alunos.empty else 0
        total_profs = len(df_professores) if not df_professores.empty else 0
        total_turmas = len(df_turmas) if not df_turmas.empty else 0

        card1 = self._criar_kpi_card_custom(kpi_frame, "Total de Alunos", str(total_alunos), PRIMARY_BLUE)
        card2 = self._criar_kpi_card_custom(kpi_frame, "Total de Professores", str(total_profs), SUCCESS_GREEN)
        card3 = self._criar_kpi_card_custom(kpi_frame, "Total de Turmas", str(total_turmas), ERROR_RED)

        card1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        card2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        card3.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        if total_alunos == 0 and total_turmas == 0:
            ctk.CTkLabel(self.content_container, text="Atenção: Nenhuma informação carregada.", text_color=ERROR_RED).grid(row=1, column=0, padx=10, pady=10)
            return

        # --- 2. Gráfico de Distribuição ---
        dados_grafico = self._calcular_alunos_por_turma()
        
        if dados_grafico:
            graph_frame = ctk.CTkFrame(self.content_container, fg_color=CARD_BG, corner_radius=10)
            graph_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
            graph_frame.grid_columnconfigure(0, weight=1)
            
            self.content_container.grid_rowconfigure(1, weight=1) # Permite expandir
            
            self._gerar_grafico_admin(graph_frame, dados_grafico, 0)
        else:
            ctk.CTkLabel(self.content_container, text="Sem dados de matrículas para gerar gráfico.", text_color=DARK_GRAY).grid(row=1, column=0, padx=10, pady=10)

    def _preparar_tabela_notas_detalhada(self) -> pd.DataFrame:
        """Prepara um DataFrame com as notas detalhadas do aluno por atividade e disciplina."""
        dfs = self.dados
        required = ['matriculas', 'turmas', 'atividades', 'notas']
        
        # Verifica se as tabelas necessárias existem
        if any(k not in dfs for k in required) or dfs.get('notas', pd.DataFrame()).empty:
             return pd.DataFrame()

        aluno_id_str = str(self.id_usuario).strip()
        
        # 1. Filtrar notas do aluno logado
        col_id_aluno_nota = self._encontrar_coluna(dfs['notas'], ['ID_Aluno', 'Aluno_ID'])
        if not col_id_aluno_nota: return pd.DataFrame()
        df_notas_aluno = dfs['notas'][dfs['notas'][col_id_aluno_nota].astype(str).str.strip() == aluno_id_str].copy()
        
        if df_notas_aluno.empty:
            return pd.DataFrame()
        
        # 2. Merge Notas com Atividades (para obter o nome e peso da atividade)
        atividades_info = dfs.get('atividades', pd.DataFrame()).copy()
        col_ativ_id = self._encontrar_coluna(atividades_info, ['ID', 'Codigo'])
        col_nota_ativ = self._encontrar_coluna(df_notas_aluno, ['ID_Atividade', 'Atividade_ID'])
        
        if not col_ativ_id or not col_nota_ativ: return pd.DataFrame()
        
        atividades_info[col_ativ_id] = atividades_info[col_ativ_id].astype(str)
        df_notas_aluno[col_nota_ativ] = df_notas_aluno[col_nota_ativ].astype(str)

        df_merged = pd.merge(
            df_notas_aluno,
            atividades_info,
            left_on=col_nota_ativ,
            right_on=col_ativ_id,
            how='left',
            suffixes=('_nota', '_ativ')
        )
        
        # 3. Merge com Turmas (para obter o nome da disciplina/turma)
        turmas_info = dfs.get('turmas', pd.DataFrame()).copy()
        col_ativ_turma = self._encontrar_coluna(atividades_info, ['ID_Turma', 'Turma_ID']) 
        col_turma_nome = self._encontrar_coluna(turmas_info, ['Nome', 'Disciplina', 'Materia'])
        col_turma_id_ativ = col_ativ_turma if col_ativ_turma in df_merged.columns else f"{col_ativ_turma}_ativ"
        
        if col_turma_id_ativ and 'ID' in turmas_info.columns and col_turma_nome:
            turmas_info['ID'] = turmas_info['ID'].astype(str)
            df_merged[col_turma_id_ativ] = df_merged[col_turma_id_ativ].astype(str)

            df_merged = pd.merge(
                df_merged,
                turmas_info,
                left_on=col_turma_id_ativ,
                right_on='ID',
                how='left',
                suffixes=('', '_turma_info')
            )
        
        # 4. Preparar colunas finais para exibição
        col_nome_ativ = next((c for c in ['Nome_ativ', self._encontrar_coluna(atividades_info, ['Nome', 'Nome_Atividade'])] if c in df_merged.columns), None)
        col_nome_turma = next((c for c in [col_turma_nome, f"{col_turma_nome}_turma_info"] if c in df_merged.columns), None) 

        col_nota_valor = self._encontrar_coluna(df_merged, ['Nota_nota', 'Nota', 'Valor'])
        col_peso_valor = self._encontrar_coluna(df_merged, ['Peso_ativ', 'Peso', 'Ponderacao'])
        
        cols_to_show = {
            col_nome_turma: 'Disciplina',
            col_nome_ativ: 'Atividade',
            col_peso_valor: 'Peso',
            col_nota_valor: 'Nota'
        }
        
        df_final = df_merged[[c for c in cols_to_show.keys() if c in df_merged.columns]].copy()
        df_final = df_final.rename(columns={k: v for k, v in cols_to_show.items() if k in df_final.columns})

        return df_final[['Disciplina', 'Atividade', 'Peso', 'Nota']].fillna('-')        

    def exibir_dashboard_aluno(self):
        self._limpar_container()
        
        df_aluno = self.dados.get('aluno', pd.DataFrame())
        nome_aluno = self.id_usuario 
        
        # Busca pelo nome
        if not df_aluno.empty and 'ID' in df_aluno.columns and 'Nome' in df_aluno.columns:
            aluno_info = df_aluno[df_aluno['ID'].astype(str) == str(self.id_usuario)]
            if not aluno_info.empty:
                nome_col = next((col for col in aluno_info.columns if col.lower() == 'nome'), 'Nome')
                nome_aluno = aluno_info.iloc[0].get(nome_col, self.id_usuario)
        
        self.current_display_label.configure(text=f"🏠 Início do Aluno: {nome_aluno}")
        
        medias, relatorio_status = self._calcular_medias() 
        
        kpi_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        kpi_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew") 
        kpi_frame.grid_columnconfigure((0, 1), weight=1, uniform="kpi_group")
        
        kpi_frame.grid_rowconfigure(0, weight=0) 
        kpi_frame.grid_rowconfigure(1, weight=1) 

        if "ERRO" in relatorio_status:
            ctk.CTkLabel(kpi_frame, text=relatorio_status, text_color=ERROR_RED, wraplength=450, justify="left").grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nwe")
            return
            
        elif medias:
            media_geral = sum(medias.values()) / len(medias)
            status = "Aprovado" if media_geral >= 6.0 else "Atenção"
            
            card1 = self._criar_kpi_card_custom(kpi_frame, "Média Geral Ponderada", f"{media_geral:.2f}", PRIMARY_BLUE)
            card2 = self._criar_kpi_card_custom(kpi_frame, "Status Atual", status, SUCCESS_GREEN if status == "Aprovado" else ERROR_RED)
            card1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            card2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            self._gerar_grafico_desempenho_aluno(kpi_frame, medias, 1) 
        else:
            ctk.CTkLabel(kpi_frame, text="Nenhum dado de nota encontrado para o cálculo da média. Verifique a consistência dos dados de Matrículas e Notas.", text_color=DARK_GRAY).grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    def _gerar_grafico_desempenho_aluno(self, parent_frame, medias, row):
        """Gera um gráfico de desempenho por disciplina para o aluno."""
        if self.grafico_canvas:
            self.grafico_canvas.get_tk_widget().destroy()
        
        fig, ax = plt.subplots(figsize=(8, 4))
        
        disciplinas = list(medias.keys())[:10]
        valores = list(medias.values())[:10]
        
        ax.bar(disciplinas, valores, color=[SUCCESS_GREEN if v >= 7.0 else ERROR_RED if v < 6.0 else PRIMARY_BLUE for v in valores])
        ax.axhline(6.0, color='gray', linestyle='--', linewidth=1, label='Corte (6.0)')
        ax.set_title("Desempenho por Disciplina")
        ax.set_ylabel("Média")
        ax.set_ylim(0, 10)
        plt.xticks(rotation=15, ha="right")
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.grafico_canvas = canvas 

    def exibir_notas_aluno_com_grafico(self):
        """
        Exibe o dashboard de desempenho do aluno: KPIs, Gráfico e Tabela de notas detalhadas.
        Tudo dentro de um único CTkScrollableFrame (self.content_container).
        """
        self._limpar_container()
        self.current_display_label.configure(text="📈 Meu Desempenho Acadêmico")
        
        medias, relatorio_status = self._calcular_medias()

        # --- PARTE 1: KPI e Gráfico (Fica na row 0 do self.content_container) ---
        # Este é o primeiro bloco de conteúdo dentro do frame rolavel
        kpi_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        kpi_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew") # "ew" para expansão horizontal
        kpi_frame.grid_columnconfigure((0, 1), weight=1, uniform="kpi_group")
        kpi_frame.grid_rowconfigure(0, weight=0) # Linha dos KPIs
        kpi_frame.grid_rowconfigure(1, weight=1) # Linha do Gráfico

        if "ERRO" in relatorio_status:
            ctk.CTkLabel(kpi_frame, text=relatorio_status, text_color=ERROR_RED, wraplength=450, justify="left").grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nwe")
        elif medias:
            # Cards KPI (row 0 dentro do kpi_frame)
            media_geral = sum(medias.values()) / len(medias)
            status = "Aprovado" if media_geral >= 6.0 else "Atenção"
            card1 = self._criar_kpi_card_custom(kpi_frame, "Média Geral Ponderada", f"{media_geral:.2f}", PRIMARY_BLUE)
            card2 = self._criar_kpi_card_custom(kpi_frame, "Status Atual", status, SUCCESS_GREEN if status == "Aprovado" else ERROR_RED)
            card1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            card2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            # Gráfico de Desempenho (row 1 dentro do kpi_frame)
            self._gerar_grafico_desempenho_aluno(kpi_frame, medias, 1) 
        else:
            ctk.CTkLabel(kpi_frame, text="Nenhum dado de nota encontrado para o cálculo da média.", text_color=DARK_GRAY).grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        # --- PARTE 2: Tabela de Notas Detalhada (Fica na row 1 do self.content_container) ---
        
        # Este é o segundo bloco de conteúdo, imediatamente abaixo do gráfico no frame rolavel.
        table_container_frame = ctk.CTkFrame(self.content_container, fg_color=LIGHT_GRAY_BG)
        table_container_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        table_container_frame.grid_columnconfigure(0, weight=1)
        
        df_detalhado = self._preparar_tabela_notas_detalhada()
        
        if not df_detalhado.empty:
            # A função _exibir_tabela_formatada criará a tabela no table_container_frame
            self._exibir_tabela_formatada(df_detalhado, "Notas Detalhadas por Atividade", table_container_frame)
        else:
            ctk.CTkLabel(table_container_frame, text="Nenhuma nota detalhada encontrada.", text_color=DARK_GRAY).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            
        # Configura as linhas do container rolavel:
        self.content_container.grid_rowconfigure(0, weight=0) # O gráfico/KPI não se expande verticalmente
        self.content_container.grid_rowconfigure(1, weight=1) # A tabela pode se expandir (se houver espaço extra)

    def _calcular_alunos_por_turma(self) -> Dict[str, int]:
        """Calcula a quantidade de alunos por turma para o gráfico do Admin."""
        dfs = self.dados
        if 'matriculas' not in dfs or 'turmas' not in dfs:
            return {}
            
        # Identifica colunas e garante que existem
        col_turma_id_mat = self._encontrar_coluna(dfs['matriculas'], ['ID_Turma', 'Turma_ID'])
        col_turma_id = self._encontrar_coluna(dfs['turmas'], ['ID', 'Codigo'])
        col_turma_nome = self._encontrar_coluna(dfs['turmas'], ['Nome', 'Disciplina'])
        
        if not col_turma_id_mat or not col_turma_id:
            return {}
        
        # Força conversão para string para evitar erro (ex: 1 vs "1")
        df_mat = dfs['matriculas'].copy()
        df_mat[col_turma_id_mat] = df_mat[col_turma_id_mat].astype(str).str.strip()
        
        # Conta ocorrências de matrículas por ID de turma
        contagem = df_mat[col_turma_id_mat].value_counts()
        
        resultado = {}
        for id_turma, qtd in contagem.items():
            id_turma_str = str(id_turma)
            
            # Busca o nome da turma
            nome_turma = f"Turma {id_turma_str}"
            turma_row = dfs['turmas'][dfs['turmas'][col_turma_id].astype(str).str.strip() == id_turma_str]
            
            if not turma_row.empty and col_turma_nome:
                nome_turma = str(turma_row.iloc[0][col_turma_nome])
                
            resultado[nome_turma] = qtd
            
        return resultado

    def _gerar_grafico_admin(self, parent_frame, dados: Dict[str, int], row):
        """Gera o gráfico de barras para o Admin."""
        if self.grafico_canvas:
            self.grafico_canvas.get_tk_widget().destroy()
            
        if not dados:
            return          

        # Configuração do Gráfico
        fig, ax = plt.subplots(figsize=(8, 4))
        
        turmas = list(dados.keys())
        qtds = list(dados.values())
        
        # Cria barras
        bars = ax.bar(turmas, qtds, color=PRIMARY_BLUE)
        
        ax.set_title("Distribuição de Alunos por Turma")
        ax.set_ylabel("Qtd. Alunos")
        
        # Adiciona o valor em cima da barra (try/except para versões antigas do matplotlib)
        try:
            ax.bar_label(bars)
        except AttributeError:
            # Fallback para matplotlib antigo
            for rect in bars:
                height = rect.get_height()
                ax.annotate(f'{height}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom')
        
        plt.xticks(rotation=30, ha="right", fontsize=9)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=row, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.grafico_canvas = canvas    
        
    # ==========================================================
    # --- FUNÇÕES DE IA E PDF ---
    # ==========================================================
    
    def _preparar_dados_para_ia(self, tipo_analise: str) -> str:
        """Prepara e formata os dados para serem enviados ao módulo de IA."""
        
        # O data_manager.py agora faz todo o trabalho de mesclagem e formatação
        # Assume que o data_manager.py foi atualizado para usar os novos cabeçalhos
        data_string = preparar_dados_para_ia(self.id_usuario, tipo_analise)
        
        dfs = self.dados
        nome_display = self.id_usuario 
        
        if tipo_analise == 'aluno':
            df_aluno = dfs.get('aluno', pd.DataFrame()) 
            if not df_aluno.empty and 'ID' in df_aluno.columns:
                 user_info = df_aluno[df_aluno['ID'].astype(str) == str(self.id_usuario)]
                 if not user_info.empty:
                     # A coluna de nome é 'Nome'
                     nome_col = next((col for col in user_info.columns if col.lower() == 'nome'), None)
                     nome_display = user_info.iloc[0].get(nome_col, self.id_usuario) if nome_col else self.id_usuario
                     
            self.last_ia_report_name = f"Relatório de Desempenho do Aluno: {nome_display}"
            self.last_ia_report_type = "aluno"
            
        elif tipo_analise == 'admin' or tipo_analise == 'professor':
            df_user = dfs.get(tipo_analise, pd.DataFrame()) 
            if not df_user.empty and 'ID' in df_user.columns:
                 user_info = df_user[df_user['ID'].astype(str) == str(self.id_usuario)]
                 if not user_info.empty:
                     # A coluna de nome é 'Nome'
                     nome_col = next((col for col in user_info.columns if col.lower() == 'nome'), None)
                     nome_display = user_info.iloc[0].get(nome_col, self.id_usuario) if nome_col else self.id_usuario

            self.last_ia_report_name = f"Relatório Gerencial: {tipo_analise.capitalize()} ({nome_display})"
            self.last_ia_report_type = tipo_analise
        
        return data_string

    def analisar_dados_ia(self, tipo_analise: str):
        """Chama a IA, exibe o resultado e armazena para geração de PDF."""
        self._limpar_container()
        self.current_display_label.configure(text=f"🧠 Análise de Dados via IA - {tipo_analise.upper()}")

        status_label = ctk.CTkLabel(self.content_container, text="Aguarde, a IA está gerando o relatório...", text_color=PRIMARY_BLUE)
        status_label.grid(row=0, column=0, padx=20, pady=20, sticky="n")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.update_idletasks() 

        raw_data = self._preparar_dados_para_ia(tipo_analise)

        if not raw_data or raw_data.strip().startswith('AVISO:') or raw_data.strip().startswith('ERRO:'):
            status_label.configure(text=f"❌ Erro: Dados insuficientes para análise de IA. Detalhe: {raw_data.strip()}", text_color=ERROR_RED)
            return

        try:
            relatorio_ia_texto = gerar_relatorio_ia(
                nome_usuario=self.last_ia_report_name, 
                dados_para_ia=raw_data, 
                tipo_usuario=tipo_analise
            )
            self.last_ia_report_data = relatorio_ia_texto 
            
            status_label.destroy()
            
            report_box = ctk.CTkTextbox(self.content_container, height=400, fg_color=CARD_BG, text_color=DARK_GRAY)
            report_box.insert("0.0", relatorio_ia_texto)
            report_box.configure(state="disabled")
            report_box.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
            self.content_container.grid_rowconfigure(1, weight=1)
            self.ia_report_box = report_box # Atributo para limpeza

            
            save_pdf_btn = ctk.CTkButton(self.content_container, text="SALVAR RELATÓRIO COMO PDF", command=lambda: self._salvar_como_pdf(relatorio_ia_texto), 
                                         fg_color=SUCCESS_GREEN, font=ctk.CTkFont(size=14, weight="bold"))
            save_pdf_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        except Exception as e:
            status_label.configure(text=f"❌ Erro ao processar IA. Detalhe: {e}", text_color=ERROR_RED)

    def gerar_relatorio_ia_pdf(self):
        """Função de conveniência para Alunos."""
        self.analisar_dados_ia('aluno') 

    def _salvar_como_pdf(self, report_text: str):
        """Salva o relatório em um arquivo PDF."""
        try:
            base_name = "".join(c if c.isalnum() or c == '_' else '_' for c in self.last_ia_report_name.replace(' ', '_'))
            filename = f"{base_name}_{self.id_usuario}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, self.last_ia_report_name.encode('latin-1', 'replace').decode('latin-1'), 0, 1, "C")
            
            pdf.set_font("Arial", "", 10)
             
            # Ajusta para remover a formatação markdown (como ** e ###)
            formatted_text = report_text.replace('**', '').replace('###', '').replace('>', '').encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, formatted_text)
            
            pdf.output(filename, "F")
            
            print(f"✅ Relatório PDF salvo com sucesso em: {os.path.abspath(filename)}")
            
            ctk.CTkLabel(self.content_container, text=f"✅ PDF '{filename}' salvo com sucesso no diretório do script!", text_color=SUCCESS_GREEN).grid(row=3, column=0, padx=10, pady=5)
            
        except Exception as e:
            error_msg = f"❌ ERRO ao salvar PDF: {e}. Verifique as permissões de pasta e se 'fpdf' e 'pandas' estão instalados."
            print(error_msg)
            ctk.CTkLabel(self.content_container, text=error_msg, text_color=ERROR_RED).grid(row=3, column=0, padx=10, pady=5)
        
# ==========================================================
# --- Inicialização da Aplicação ---
# ==========================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()
