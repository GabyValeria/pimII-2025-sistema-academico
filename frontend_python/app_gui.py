import customtkinter as ctk
from data_manager import autenticar_usuario 
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
        self.title("Sistema Acadêmico Colaborativo (SGA)")
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
        else: # Professor (default)
            self.main_frame.exibir_dados('turmas_prof')

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
        self.seg_button = ctk.CTkSegmentedButton(self.auth_panel, variable=self.acesso_var, values=["aluno", "professor", "admin"])
        self.seg_button.grid(row=1, column=0, pady=10)

        self.login_entry = ctk.CTkEntry(self.auth_panel, placeholder_text="Login", width=250, height=40)
        self.login_entry.grid(row=2, column=0, pady=10)
        
        self.senha_entry = ctk.CTkEntry(self.auth_panel, placeholder_text="Senha", show="*", width=250, height=40)
        self.senha_entry.grid(row=3, column=0, pady=10)

        self.login_button = ctk.CTkButton(self.auth_panel, text="ENTRAR", command=self.tentar_login, width=250, height=40, fg_color=PRIMARY_BLUE)
        self.login_button.grid(row=4, column=0, pady=(20, 10))
        
        self.info_label = ctk.CTkLabel(self.auth_panel, text="", text_color=ERROR_RED)
        self.info_label.grid(row=5, column=0, pady=5)
        
        # Credenciais de Exemplo (para facilitar o teste)
        self.login_entry.insert(0, "alice") 
        self.senha_entry.insert(0, "123456")
        
    def tentar_login(self):
        login = self.login_entry.get()
        senha = self.senha_entry.get()
        tipo = self.acesso_var.get()
        
        self.info_label.configure(text="Verificando...", text_color=DARK_GRAY)
        self.master_app.update_idletasks()
        
        id_usuario, dados = autenticar_usuario(login, senha, tipo)
        
        if id_usuario is not None and dados:
            # Verifica se pelo menos o DF de alunos/professores/turmas foi carregado
            if tipo == 'admin' or not any(df.empty for df in [dados.get('alunos'), dados.get('professores'), dados.get('turmas')]): 
                self.info_label.configure(text="✅ Login bem-sucedido!", text_color=SUCCESS_GREEN)
                self.callback_sucesso(id_usuario, tipo, dados)
                return
        
        self.info_label.configure(text="❌ Login ou senha incorretos ou dados não carregados.", text_color=ERROR_RED)


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
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=f"SGA - {nome_display}", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        button_font = ctk.CTkFont(size=14, weight="bold")
        
        # Botões de Navegação
        if nivel_acesso == 'aluno':
            ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.exibir_dashboard_aluno, fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=1, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Minhas Matrículas", command=lambda: self.exibir_dados('matriculas_aluno'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=2, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Meu Desempenho", command=self.exibir_notas_aluno_com_grafico, fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=3, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Relatório IA (PDF)", command=self.gerar_relatorio_ia_pdf, fg_color=ERROR_RED, font=button_font).grid(row=4, column=0, padx=20, pady=10)
        elif nivel_acesso == 'professor':
            ctk.CTkButton(self.sidebar_frame, text="Minhas Turmas", command=lambda: self.exibir_dados('turmas_prof'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=1, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Análise Turma (IA)", command=lambda: self.analisar_dados_ia('professor'), fg_color=ERROR_RED, font=button_font).grid(row=2, column=0, padx=20, pady=10)
        elif nivel_acesso == 'admin':
            ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.exibir_dashboard_admin, fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=1, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Alunos", command=lambda: self.exibir_dados('alunos'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=2, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Professores", command=lambda: self.exibir_dados('professores'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=3, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Turmas", command=lambda: self.exibir_dados('turmas'), fg_color=LIGHT_GRAY_BG, text_color=DARK_GRAY, font=button_font).grid(row=4, column=0, padx=20, pady=10)
            ctk.CTkButton(self.sidebar_frame, text="Análise Geral (IA)", command=lambda: self.analisar_dados_ia('admin'), fg_color=ERROR_RED, font=button_font).grid(row=5, column=0, padx=20, pady=10)


        ctk.CTkButton(self.sidebar_frame, text="Logout", command=self.callback_logout, fg_color=ERROR_RED, font=button_font).grid(row=8, column=0, padx=20, pady=(10, 20))

        # --- Main Content ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=CARD_BG)
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_content_frame.grid_rowconfigure(1, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        self.current_display_label = ctk.CTkLabel(self.main_content_frame, text="Bem-vindo ao SGA!", font=ctk.CTkFont(size=16, weight="bold"), text_color=DARK_GRAY)
        self.current_display_label.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        # Container principal com scroll
        self.content_container = ctk.CTkScrollableFrame(self.main_content_frame, label_text="Visualização de Dados", fg_color=LIGHT_GRAY_BG, label_text_color=DARK_GRAY)
        self.content_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
    
    # ==========================================================
    # --- FUNÇÕES DE LIMPEZA E UI ---
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
    
    def _exibir_tabela_formatada(self, df: pd.DataFrame, title: str, parent_frame: ctk.CTkFrame):
        """Exibe um DataFrame como uma tabela formatada."""
        
        table_frame = ctk.CTkFrame(parent_frame, fg_color=CARD_BG, corner_radius=10)
        table_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
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
        self.current_display_label.configure(text=f"Visualizando: {tipo.replace('_', ' ').upper()}")
        dfs = self.dados

        if tipo in ['alunos', 'professores', 'turmas'] and tipo in dfs:
            self._exibir_tabela_formatada(dfs[tipo], f"Lista de {tipo.capitalize()}", self.content_container)
        
        elif tipo == 'matriculas_aluno' and 'matriculas' in dfs:
            minhas_matriculas = dfs['matriculas'][dfs['matriculas']['id_aluno'].astype(str) == str(self.id_usuario)]
            turmas_info = dfs.get('turmas', pd.DataFrame())
            
            turmas_info['id'] = turmas_info['id'].astype(str) 
            
            df_display = pd.merge(minhas_matriculas, turmas_info, left_on='id_turma', right_on='id', how='left', suffixes=('_mat', '_turma'))
            
            nome_turma_col = 'nome' if 'nome' in df_display.columns else 'nome_turma'
            codigo_col = 'codigo' if 'codigo' in df_display.columns else 'id_turma' # Usa id_turma como fallback
            semestre_col = 'semestre' if 'semestre' in df_display.columns else 'semestre_turma'

            df_final = df_display[[codigo_col, nome_turma_col, semestre_col]].rename(columns={codigo_col: 'Código', nome_turma_col: 'Turma', semestre_col: 'Semestre'})
            
            self._exibir_tabela_formatada(df_final, "Minhas Matrículas", self.content_container)
        
        elif tipo == 'turmas_prof' and 'turmas' in dfs:
            minhas_turmas = dfs['turmas'][dfs['turmas']['id_professor_responsavel'].astype(str) == str(self.id_usuario)]
            self._exibir_tabela_formatada(minhas_turmas, f"Minhas Turmas (Prof. {self.id_usuario})", self.content_container)
            
        else:
            self.current_display_label.configure(text=f"Dados de {tipo} Indisponíveis.")

    def exibir_dashboard_admin(self):
        self._limpar_container()
        self.current_display_label.configure(text="📊 Dashboard Administrativo")

        df_alunos = self.dados.get('alunos', pd.DataFrame())
        df_turmas = self.dados.get('turmas', pd.DataFrame())
        df_professores = self.dados.get('professores', pd.DataFrame())

        kpi_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        kpi_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        kpi_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="kpi_group")

        card1 = self._criar_kpi_card_custom(kpi_frame, "Total de Alunos", str(len(df_alunos)), PRIMARY_BLUE)
        card2 = self._criar_kpi_card_custom(kpi_frame, "Total de Professores", str(len(df_professores)), SUCCESS_GREEN)
        card3 = self._criar_kpi_card_custom(kpi_frame, "Total de Turmas", str(len(df_turmas)), ERROR_RED)

        card1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        card2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        card3.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Adiciona uma mensagem de fallback se os dados estiverem vazios
        if df_alunos.empty and df_turmas.empty and df_professores.empty:
            ctk.CTkLabel(self.content_container, text="Atenção: Nenhuma informação carregada. Verifique os CSVs.", text_color=ERROR_RED).grid(row=1, column=0, padx=10, pady=10)


    def exibir_dashboard_aluno(self):
        self._limpar_container()
        
        df_alunos = self.dados.get('alunos', pd.DataFrame())
        nome_aluno = self.id_usuario # Fallback
        
        if not df_alunos.empty:
            aluno_info = df_alunos[df_alunos['id'].astype(str) == str(self.id_usuario)]
            if not aluno_info.empty:
                 nome_col = next((col for col in aluno_info.columns if col.lower() == 'nome'), None)
                 
                 if nome_col:
                    nome_aluno = aluno_info.iloc[0].get(nome_col, self.id_usuario)
                 else:
                    nome_aluno = self.id_usuario 
        
        self.current_display_label.configure(text=f"🏠 Dashboard do Aluno: {nome_aluno}")
        
        medias, _ = self._calcular_medias()
        
        kpi_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        kpi_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        kpi_frame.grid_columnconfigure((0, 1), weight=1, uniform="kpi_group")

        if medias:
            media_geral = sum(medias.values()) / len(medias)
            status = "Aprovado" if media_geral >= 6.0 else "Atenção"
            
            card1 = self._criar_kpi_card_custom(kpi_frame, "Média Geral Ponderada", f"{media_geral:.2f}", PRIMARY_BLUE)
            card2 = self._criar_kpi_card_custom(kpi_frame, "Status Atual", status, SUCCESS_GREEN if status == "Aprovado" else ERROR_RED)
            card1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            card2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            self._gerar_grafico_desempenho_aluno(kpi_frame, medias, 1)
        else:
            ctk.CTkLabel(kpi_frame, text="Nenhum dado de nota encontrado para o cálculo da média.", text_color=DARK_GRAY).grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    def _gerar_grafico_desempenho_aluno(self, parent_frame, medias, row):
        """Gera um gráfico de desempenho por disciplina para o aluno."""
        fig, ax = plt.subplots(figsize=(8, 4))
        disciplinas = list(medias.keys())
        valores = list(medias.values())
        
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

    def _calcular_medias(self) -> Tuple[Dict[str, float], str]:
        """Calcula a média ponderada do aluno e retorna o detalhe para IA."""
        dfs = self.dados
        if any(key not in dfs or dfs[key].empty for key in ['matriculas', 'turmas', 'atividades', 'notas']):
             return {}, "Dados incompletos para cálculo de média."

        aluno_id_conv = str(self.id_usuario)
        minhas_matriculas = dfs['matriculas'][dfs['matriculas']['id_aluno'].astype(str) == aluno_id_conv]
        medias = {}
        relatorio_detalhado = ""
        
        for id_turma in minhas_matriculas['id_turma'].unique():
            turma_data = dfs['turmas'][dfs['turmas']['id'].astype(str) == str(id_turma)]
            if turma_data.empty: continue
            
            turma = turma_data.iloc[0]
            atividades_turma = dfs['atividades'][dfs['atividades']['id_turma'].astype(str) == str(id_turma)]
            notas_aluno = dfs['notas'][dfs['notas']['id_aluno'].astype(str) == aluno_id_conv]
            
            # Mescla atividades e notas
            df_notas_completo = pd.merge(
                atividades_turma, 
                notas_aluno, 
                left_on='id', 
                right_on='id_atividade', 
                how='left', 
                suffixes=('_ativ', '_nota')
            )
            
            # 1. Identificar coluna de Nota
            nota_col = None
            if 'nota_nota' in df_notas_completo.columns:
                nota_col = 'nota_nota' 
            elif 'nota' in df_notas_completo.columns:
                nota_col = 'nota' 
            
            if not nota_col:
                 print(f"❌ ERRO: Coluna de nota não encontrada no DataFrame mesclado para turma {id_turma}.")
                 continue
                 
            # 2. Converte Nota e Peso
            df_notas_completo['nota_valor'] = pd.to_numeric(df_notas_completo[nota_col], errors='coerce') 
            
            peso_col = 'peso_ativ' if 'peso_ativ' in df_notas_completo.columns else 'peso'
            df_notas_completo['peso'] = pd.to_numeric(df_notas_completo.get(peso_col), errors='coerce') 

            df_calculo = df_notas_completo.dropna(subset=['nota_valor', 'peso'])
            
            soma_ponderada = (df_calculo['peso'] * df_calculo['nota_valor']).sum()
            soma_pesos_lancados = df_calculo['peso'].sum()
            media = (soma_ponderada / soma_pesos_lancados) if soma_pesos_lancados > 0 else 0.0
            
            turma_nome = f"{turma.get('codigo', 'Desconhecido')}"
            medias[turma_nome] = media
            
            relatorio_detalhado += f"**Disciplina: {turma_nome}**: Média: {media:.2f}\n"

        return medias, relatorio_detalhado

    def exibir_notas_aluno_com_grafico(self):
        """Exibe o gráfico de desempenho e a tabela de médias."""
        self._limpar_container()
        self.exibir_dashboard_aluno() 
        
        medias, _ = self._calcular_medias()
        
        if medias:
            df_medias = pd.DataFrame(list(medias.items()), columns=['Disciplina', 'Média Final'])
            df_medias['Média Final'] = df_medias['Média Final'].apply(lambda x: f"{x:.2f}")
            
            self.content_container_table = ctk.CTkScrollableFrame(self.main_content_frame, label_text="Resumo das Médias", fg_color=LIGHT_GRAY_BG, label_text_color=DARK_GRAY)
            self.content_container_table.grid(row=2, column=0, padx=10, pady=10, sticky="nsew") 
            self.main_content_frame.grid_rowconfigure(2, weight=1) 
            
            self._exibir_tabela_formatada(df_medias, "Resumo das Médias por Disciplina", self.content_container_table)
        
    # ==========================================================
    # --- FUNÇÕES DE IA E PDF ---
    # ==========================================================
    
    def _preparar_dados_para_ia(self, tipo_analise: str) -> str:
        """Prepara e formata os dados para serem enviados ao módulo de IA."""
        dfs = self.dados
        data_string = ""
        
        # 1. Obter Nome do Usuário
        nome_display = self.id_usuario
        if tipo_analise == 'aluno':
            df_target = dfs.get('alunos', pd.DataFrame())
        elif tipo_analise == 'professor':
             df_target = dfs.get('professores', pd.DataFrame())
        else: # admin
             df_target = pd.DataFrame() 

        if not df_target.empty:
            user_info = df_target[df_target['id'].astype(str) == str(self.id_usuario)]
            if not user_info.empty:
                 nome_col = next((col for col in user_info.columns if col.lower() == 'nome'), None)
                 if nome_col:
                    nome_display = user_info.iloc[0].get(nome_col, self.id_usuario)

        # 2. Gerar Dados
        if tipo_analise == 'aluno':
            _, data_string = self._calcular_medias()
            self.last_ia_report_name = f"Relatório Aluno {nome_display}"
            self.last_ia_report_type = "aluno"
            
        elif tipo_analise == 'admin' or tipo_analise == 'professor':
            # Simplesmente passa o head dos dados carregados
            for key, df in dfs.items():
                 # Limita a 5 linhas para evitar sobrecarga no prompt da IA
                 data_string += f"\n--- {key.upper()} ({len(df)} Registros) ---\n"
                 data_string += df.head(5).to_string() + "\n"
            
            self.last_ia_report_name = f"Relatório {tipo_analise.capitalize()} ({nome_display})"
            self.last_ia_report_type = tipo_analise
        
        return data_string

    def analisar_dados_ia(self, tipo_analise: str):
        """Chama a IA, exibe o resultado e armazena para geração de PDF."""
        self._limpar_container()
        self.current_display_label.configure(text=f"🧠 Análise de Dados via IA - {tipo_analise.upper()}")

        status_label = ctk.CTkLabel(self.content_container, text="Aguarde, a IA está gerando o relatório...", text_color=PRIMARY_BLUE)
        status_label.grid(row=0, column=0, padx=20, pady=20, sticky="n")
        self.update_idletasks()
        
        raw_data = self._preparar_dados_para_ia(tipo_analise)

        if not raw_data:
            status_label.configure(text="❌ Erro: Dados insuficientes para análise de IA.", text_color=ERROR_RED)
            return

        try:
            # CORREÇÃO CRÍTICA: Chamada com a ordem correta dos argumentos: (nome_usuario, dados_para_ia, tipo_usuario)
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
            
            save_pdf_btn = ctk.CTkButton(self.content_container, text="SALVAR RELATÓRIO COMO PDF", command=lambda: self._salvar_como_pdf(relatorio_ia_texto), 
                                         fg_color=SUCCESS_GREEN, font=ctk.CTkFont(size=14, weight="bold"))
            save_pdf_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        except Exception as e:
            status_label.configure(text=f"❌ Erro ao processar IA: Verifique se ai_module.py existe. Detalhe: {e}", text_color=ERROR_RED)

    def gerar_relatorio_ia_pdf(self):
         """Função de conveniência para Alunos."""
         self.analisar_dados_ia('aluno') 

    def _salvar_como_pdf(self, report_text: str):
        """Salva o relatório em um arquivo PDF."""
        try:
            filename = f"{self.last_ia_report_name.replace(' ', '_')}_{self.id_usuario}_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf"
            pdf = FPDF()
            pdf.add_page()
            
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, self.last_ia_report_name, 0, 1, "C")
            
            pdf.set_font("Arial", "", 10)
            
            # Formatação simples para o PDF
            formatted_text = report_text.replace('**', '').replace('\n\n', '\n').encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, formatted_text)
            
            pdf.output(filename, "F")
            
            print(f"✅ Relatório PDF salvo com sucesso em: {os.path.abspath(filename)}")
            
        except Exception as e:
            print(f"❌ ERRO ao gerar o PDF: {e}")
            
# ==========================================================
# --- Inicialização da Aplicação ---
# ==========================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()
