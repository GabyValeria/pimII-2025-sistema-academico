# -*- coding: utf-8 -*-

# --- Importação das Bibliotecas Necessárias ---
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd # Para manipulação de dados dos arquivos CSV
from matplotlib.figure import Figure # Para criar gráficos
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # Para integrar gráficos no Tkinter
from reportlab.pdfgen import canvas as pdf_canvas # Para gerar PDFs
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os
import datetime
import shutil # Para a funcionalidade de backup

# --- Configurações Visuais Globais ---
# Paleta de cores e fontes para manter a consistência visual
CORES = {
    "fundo_claro": "#f8f9fa", "fundo_componente": "#ffffff", "destaque": "#d18681",
    "suporte": "#acbfb7", "acento": "#8e6d86", "texto_escuro": "#212529", "texto_claro": "#ffffff",
    "sucesso": "#2a9d8f", "erro": "#e76f51"
}
FONT_TITULO = ("Segoe UI", 22, "bold")
FONT_SUBTITULO = ("Segoe UI", 16, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_BOTAO = ("Segoe UI", 12, "bold")
FONT_INDICADOR = ("Segoe UI", 28, "bold")

# --- Estrutura de Arquivos e Diretórios ---
DATA_DIR = "data"
ARQUIVOS_CSV = {
    "usuarios": os.path.join(DATA_DIR, "usuarios.csv"),
    "turmas": os.path.join(DATA_DIR, "turmas.csv"),
    "aulas": os.path.join(DATA_DIR, "aulas.csv"),
    "atividades": os.path.join(DATA_DIR, "atividades.csv"),
}
LOG_FILE = os.path.join(DATA_DIR, "logs.txt")

# --- Função Central de LOG ---
def registrar_log(mensagem):
    """
    Registra uma mensagem no arquivo de log com data e hora.
    Usada para auditoria de ações importantes no sistema.
    """
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] [FRONTEND] {mensagem}\n")
    except Exception as e:
        # Em caso de falha no log, imprime no console para não parar a aplicação
        print(f"ERRO CRITICO: Nao foi possivel escrever no arquivo de log: {e}")

# --- Classe Principal da Aplicação ---
class App(tk.Tk):
    """
    A classe principal que gerencia a janela e a troca entre as diferentes telas (frames).
    """
    def __init__(self):
        super().__init__()
        self.title("Sistema Acadêmico Colaborativo - PIM II")
        self.geometry("1280x720")
        self.minsize(1024, 700) # Define um tamanho mínimo para a janela
        self.configure(bg=CORES["fundo_claro"])
        
        # Configura o estilo visual dos componentes ttk (Notebook, Treeview, etc.)
        self.configurar_estilos()
        
        # Carrega os dados dos arquivos .csv para a memória
        self.dados = self.carregar_dados()
        if self.dados is None:
            # Se os dados não puderem ser carregados, a aplicação não inicia
            return

        self.usuario_logado = None # Armazena os dados do usuário após o login

        # Container principal onde as telas (Login, Admin, etc.) serão exibidas
        self._container = tk.Frame(self, bg=CORES["fundo_claro"])
        self._container.pack(fill="both", expand=True)
        
        self.mostrar_frame("LoginScreen") # Mostra a tela de login inicialmente
        registrar_log("SISTEMA INICIADO")
        
        # Garante que o log de finalização seja registrado ao fechar a janela
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configurar_estilos(self):
        """Define o estilo visual dos widgets ttk para toda a aplicação."""
        style = ttk.Style(self)
        style.theme_use('clam')
        # Estilo para as abas (Notebook)
        style.configure('TNotebook', background=CORES["fundo_claro"], borderwidth=0)
        style.configure('TNotebook.Tab', background=CORES["suporte"], foreground=CORES["texto_claro"], font=("Segoe UI", 12), padding=[15, 8], borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', CORES["destaque"])])
        # Estilo para as tabelas (Treeview)
        style.configure("Treeview.Heading", font=('Segoe UI', 11, 'bold'), background=CORES["suporte"], foreground=CORES["texto_escuro"])
        style.configure("Treeview", rowheight=30, font=('Segoe UI', 10), background=CORES["fundo_componente"])
        style.map("Treeview", background=[('selected', CORES["destaque"])])

    def carregar_dados(self, refresh=False):
        """
        Lê todos os arquivos .csv da pasta 'data' e os carrega em DataFrames do Pandas.
        O parâmetro 'refresh' força a releitura dos arquivos do disco.
        """
        if not refresh and hasattr(self, 'dados_brutos'):
            return self.dados_brutos
        
        if not os.path.isdir(DATA_DIR):
            messagebox.showerror("Erro Crítico", f"A pasta '{DATA_DIR}' não foi encontrada!\nExecute o programa em C (backend) primeiro para criar a estrutura.")
            self.destroy()
            return None
        try:
            # Lê cada CSV e armazena em um dicionário de DataFrames
            self.dados_brutos = {nome: pd.read_csv(caminho, sep=';', encoding='utf-8') for nome, caminho in ARQUIVOS_CSV.items()}
            # Converte a coluna 'id' para numérico para evitar erros de tipo
            self.dados_brutos['usuarios']['id'] = pd.to_numeric(self.dados_brutos['usuarios']['id'])
            self.dados = self.dados_brutos
            return self.dados_brutos
        except Exception as e:
            messagebox.showerror("Erro de Leitura de Dados", f"Não foi possível ler os arquivos de dados da pasta '{DATA_DIR}'.\nVerifique se os arquivos estão formatados corretamente.\n\nDetalhe do Erro: {e}")
            self.destroy()
            return None
            
    def recarregar_e_redesenhar(self, frame_nome):
        """Força a releitura dos dados do disco e recarrega a tela atual."""
        self.dados = self.carregar_dados(refresh=True)
        self.mostrar_frame(frame_nome)

    def mostrar_frame(self, nome_frame):
        """Destrói o frame atual e exibe o frame solicitado."""
        for widget in self._container.winfo_children():
            widget.destroy()
        
        frame_class = globals().get(nome_frame)
        if frame_class:
            frame = frame_class(self._container, self)
            frame.pack(fill="both", expand=True)
            
    def on_closing(self):
        """Função chamada quando a janela principal é fechada."""
        registrar_log("SISTEMA FINALIZADO")
        self.destroy()

# --- Janela Pop-up para Formulário de Usuário ---
class UserFormWindow(tk.Toplevel):
    """
    Janela pop-up para adicionar ou editar usuários.
    É chamada pelo painel do Administrador.
    """
    def __init__(self, parent, controller, user_data=None):
        super().__init__(parent)
        self.transient(parent) # Mantém a janela na frente da principal
        self.controller = controller
        self.user_data = user_data # Se 'user_data' for fornecido, é um formulário de edição
        
        self.title("Editar Usuário" if user_data is not None else "Adicionar Novo Usuário")
        self.geometry("400x450")
        self.resizable(False, False)
        self.configure(bg=CORES["fundo_claro"])
        
        # --- Criação dos campos do formulário ---
        tk.Label(self, text="Nome Completo:", font=FONT_NORMAL, bg=CORES["fundo_claro"]).pack(pady=(20,0), padx=20, anchor="w")
        self.nome_entry = tk.Entry(self, font=FONT_NORMAL); self.nome_entry.pack(pady=5, padx=20, fill="x", ipady=4)
        
        tk.Label(self, text="Usuário (Login/RA):", font=FONT_NORMAL, bg=CORES["fundo_claro"]).pack(pady=(10,0), padx=20, anchor="w")
        self.usuario_entry = tk.Entry(self, font=FONT_NORMAL); self.usuario_entry.pack(pady=5, padx=20, fill="x", ipady=4)
        
        tk.Label(self, text="Senha:", font=FONT_NORMAL, bg=CORES["fundo_claro"]).pack(pady=(10,0), padx=20, anchor="w")
        self.senha_entry = tk.Entry(self, font=FONT_NORMAL, show="*"); self.senha_entry.pack(pady=5, padx=20, fill="x", ipady=4)
        
        tk.Label(self, text="Papel:", font=FONT_NORMAL, bg=CORES["fundo_claro"]).pack(pady=(10,0), padx=20, anchor="w")
        self.papel_combo = ttk.Combobox(self, values=["ALUNO", "PROFESSOR"], state="readonly", font=FONT_NORMAL); self.papel_combo.pack(pady=5, padx=20, fill="x")
        
        # Se for um formulário de edição, preenche os campos com os dados existentes
        if self.user_data is not None:
            self.nome_entry.insert(0, self.user_data['nome'])
            self.usuario_entry.insert(0, self.user_data['usuario'])
            self.papel_combo.set(self.user_data['papel'])
            # Por segurança, a senha não é preenchida, mas pode ser alterada

        tk.Button(self, text="Salvar", font=FONT_BOTAO, bg=CORES["sucesso"], fg=CORES["texto_claro"], relief="flat", command=self.salvar).pack(pady=20, ipady=8, ipadx=20)
        
        self.grab_set() # Foca a interação nesta janela até que seja fechada

    def salvar(self):
        """Valida e salva os dados do formulário no arquivo usuarios.csv."""
        nome = self.nome_entry.get().strip()
        usuario = self.usuario_entry.get().strip()
        senha = self.senha_entry.get().strip()
        papel = self.papel_combo.get()

        if not all([nome, usuario, senha, papel]):
            messagebox.showerror("Erro de Validação", "Todos os campos são obrigatórios.", parent=self)
            return

        df_usuarios = self.controller.dados['usuarios']

        # Validação: Verifica se o nome de usuário já existe
        existing_user = df_usuarios[df_usuarios['usuario'] == usuario]
        is_editing = self.user_data is not None
        if not existing_user.empty and (not is_editing or existing_user.iloc[0]['id'] != self.user_data['id']):
            messagebox.showerror("Erro de Validação", f"O usuário '{usuario}' já existe no sistema.", parent=self)
            return
            
        try:
            if is_editing: # Lógica para Edição
                user_id = self.user_data['id']
                df_usuarios.loc[df_usuarios['id'] == user_id, ['nome', 'usuario', 'senha', 'papel']] = [nome, usuario, senha, papel]
                msg = "Usuário atualizado com sucesso!"
            else: # Lógica para Adição
                novo_id = df_usuarios['id'].max() + 1 if not df_usuarios.empty else 1
                nova_linha = pd.DataFrame([{'id': novo_id, 'usuario': usuario, 'senha': senha, 'papel': papel, 'nome': nome}])
                df_usuarios = pd.concat([df_usuarios, nova_linha], ignore_index=True)
                msg = "Usuário adicionado com sucesso!"
            
            # Salva o DataFrame modificado de volta no arquivo CSV
            df_usuarios.to_csv(ARQUIVOS_CSV['usuarios'], sep=';', index=False, encoding='utf-8')
            
            # Registra a ação no log
            admin_user = self.controller.usuario_logado['usuario']
            log_msg = (f"ADMIN '{admin_user}' ATUALIZOU usuario ID {self.user_data['id']}." if is_editing 
                       else f"ADMIN '{admin_user}' ADICIONOU novo usuario '{usuario}'.")
            registrar_log(log_msg)
            
            messagebox.showinfo("Sucesso", msg)
            self.destroy() # Fecha a janela pop-up
            self.controller.recarregar_e_redesenhar("AdminDashboard") # Atualiza a tela principal
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados no arquivo CSV:\n{e}", parent=self)


# --- Tela de Login ---
class LoginScreen(tk.Frame):
    """A tela inicial onde o usuário insere suas credenciais."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=CORES["fundo_claro"])
        self.controller = controller

        # Frame central para o conteúdo do login
        main_frame = tk.Frame(self, bg=CORES["fundo_componente"], bd=1, relief="solid")
        main_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=450)
        
        tk.Label(main_frame, text="Bem-Vindo", font=FONT_TITULO, bg=CORES["fundo_componente"], fg=CORES["destaque"]).pack(pady=(40, 10))
        tk.Label(main_frame, text="Acesse o Sistema Acadêmico", font=FONT_NORMAL, bg=CORES["fundo_componente"], fg=CORES["texto_escuro"]).pack(pady=(0, 30))
        
        tk.Label(main_frame, text="Usuário (RA para Aluno)", font=FONT_NORMAL, bg=CORES["fundo_componente"], fg=CORES["texto_escuro"]).pack(anchor="w", padx=50)
        self.login_entry = tk.Entry(main_frame, font=FONT_NORMAL, relief="solid", bd=1); self.login_entry.pack(pady=5, ipady=8, padx=50, fill="x")
        
        tk.Label(main_frame, text="Senha", font=FONT_NORMAL, bg=CORES["fundo_componente"], fg=CORES["texto_escuro"]).pack(anchor="w", padx=50, pady=(10, 0))
        self.senha_entry = tk.Entry(main_frame, font=FONT_NORMAL, show="*", relief="solid", bd=1); self.senha_entry.pack(pady=5, ipady=8, padx=50, fill="x")
        
        tk.Button(main_frame, text="Entrar", font=FONT_BOTAO, bg=CORES["destaque"], fg=CORES["texto_claro"], command=self.verificar_login, relief="flat").pack(pady=30, ipady=8, ipadx=20)
        
        # Preenche com dados de admin para facilitar o teste
        self.login_entry.insert(0, "admin"); self.senha_entry.insert(0, "admin")
        
        # Permite fazer login pressionando a tecla Enter
        self.controller.bind('<Return>', lambda event: self.verificar_login())

    def verificar_login(self):
        """Verifica as credenciais inseridas contra os dados em usuarios.csv."""
        login, senha = self.login_entry.get(), str(self.senha_entry.get())
        usuarios_df = self.controller.dados["usuarios"]
        # Garante que a coluna senha seja do tipo string para comparação
        usuarios_df['senha'] = usuarios_df['senha'].astype(str)
        
        # Procura por uma correspondência de usuário e senha
        match = usuarios_df[(usuarios_df['usuario'] == login) & (usuarios_df['senha'] == senha)]
        
        if not match.empty:
            self.controller.usuario_logado = match.iloc[0]
            registrar_log(f"LOGIN SUCESSO: Usuario '{login}' (ID {self.controller.usuario_logado['id']}) logou.")
            
            # Redireciona para o painel correto com base no papel do usuário
            papel = self.controller.usuario_logado['papel']
            if papel == "ADMINISTRADOR":
                self.controller.mostrar_frame("AdminDashboard")
            elif papel == "PROFESSOR":
                self.controller.mostrar_frame("ProfessorDashboard")
            elif papel == "ALUNO":
                self.controller.mostrar_frame("AlunoDashboard")
        else: 
            registrar_log(f"LOGIN FALHA: Tentativa para usuario '{login}'.")
            messagebox.showerror("Falha no Login", "Usuário ou senha incorretos.")
        
        # Remove o binding do Enter para não interferir em outras telas
        self.controller.unbind('<Return>')

# --- Classe Base para os Painéis (Dashboards) ---
class BaseDashboard(tk.Frame):
    """Classe base que contém funcionalidades comuns aos painéis, como criar tabelas."""
    def __init__(self, parent, controller): 
        super().__init__(parent, bg=CORES["fundo_claro"])
        self.controller = controller
        self.tree = None # Referência para a tabela (Treeview)

    def criar_tabela(self, parent_frame, dataframe, widths):
        """Cria e popula uma tabela (Treeview) com os dados de um DataFrame."""
        for widget in parent_frame.winfo_children(): widget.destroy()
        
        if dataframe.empty:
            tk.Label(parent_frame, text="Nenhum dado para exibir.", font=FONT_NORMAL, bg=CORES["fundo_componente"]).pack(pady=20)
            return
            
        cols = list(dataframe.columns)
        tree_frame = tk.Frame(parent_frame, bg=CORES["fundo_componente"])
        tree_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings')
        
        # Define os cabeçalhos e larguras das colunas
        for col in cols:
            self.tree.heading(col, text=col.replace('_', ' ').title())
            self.tree.column(col, width=widths.get(col, 150), anchor='center')
        
        # Insere os dados na tabela, usando o ID do registro como identificador de item (iid)
        for _, row in dataframe.iterrows():
            self.tree.insert("", "end", values=list(row), iid=row.get('id', None))
        
        # Adiciona uma barra de rolagem
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree.pack(expand=True, fill='both')

# --- Painel do Administrador ---
class AdminDashboard(BaseDashboard):
    """
    O painel principal para o usuário Administrador, com abas para
    Dashboard, Gerenciamento de Usuários e Sistema (Backup).
    """
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        tk.Label(self, text="Painel do Administrador", font=FONT_TITULO, bg=CORES["fundo_claro"], fg=CORES["texto_escuro"]).pack(pady=(20,10), padx=40, anchor="w")
        
        self.notebook = ttk.Notebook(self)
        
        # --- Aba 1: Dashboard Estratégico ---
        self.aba_dashboard = tk.Frame(self.notebook, bg=CORES["fundo_componente"])
        self.notebook.add(self.aba_dashboard, text="Dashboard")
        self.criar_dashboard()

        # --- Aba 2: Gerenciar Usuários ---
        self.aba_gerenciar_usuarios = tk.Frame(self.notebook, bg=CORES["fundo_componente"])
        self.notebook.add(self.aba_gerenciar_usuarios, text="Gerenciar Usuários")
        self.criar_gerenciador_usuarios()

        # --- Aba 3: Sistema e Backup ---
        self.aba_sistema = tk.Frame(self.notebook, bg=CORES["fundo_componente"])
        self.notebook.add(self.aba_sistema, text="Sistema")
        self.criar_aba_sistema()

        self.notebook.pack(expand=True, fill='both', padx=30, pady=20)

    def criar_dashboard(self):
        """Cria os indicadores e gráficos da tela inicial do admin."""
        frame = self.aba_dashboard
        df_usuarios = self.controller.dados['usuarios']
        df_atividades = self.controller.dados['atividades']

        # Cálculos das métricas
        total_alunos = len(df_usuarios[df_usuarios['papel'] == 'ALUNO'])
        total_professores = len(df_usuarios[df_usuarios['papel'] == 'PROFESSOR'])
        media_geral = df_atividades['nota'].mean() if not df_atividades.empty else 0

        frame.column_configure((0, 1, 2), weight=1)

        # Criação dos cartões de indicadores
        self.criar_indicador(frame, "Total de Alunos", total_alunos, CORES["suporte"]).grid(row=0, column=0, padx=10, pady=20, sticky="ew")
        self.criar_indicador(frame, "Total de Professores", total_professores, CORES["suporte"]).grid(row=0, column=1, padx=10, pady=20, sticky="ew")
        self.criar_indicador(frame, "Média Geral de Notas", f"{media_geral:.2f}", CORES["destaque"]).grid(row=0, column=2, padx=10, pady=20, sticky="ew")
        
        # Criação do gráfico de pizza
        chart_frame = tk.Frame(frame, bg=CORES["fundo_componente"])
        chart_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.criar_grafico_papeis(chart_frame, total_alunos, total_professores)

    def criar_indicador(self, parent, titulo, valor, cor):
        """Cria um widget de 'cartão' para exibir uma métrica."""
        indicador_frame = tk.Frame(parent, bg=cor, bd=1, relief="solid")
        tk.Label(indicador_frame, text=titulo, font=FONT_NORMAL, bg=cor, fg=CORES["texto_claro"]).pack(pady=(10,0))
        tk.Label(indicador_frame, text=valor, font=FONT_INDICADOR, bg=cor, fg=CORES["texto_claro"]).pack(pady=(5,10))
        return indicador_frame

    def criar_grafico_papeis(self, parent, alunos, profs):
        """Cria um gráfico de pizza mostrando a distribuição de usuários."""
        fig = Figure(figsize=(6, 4), dpi=100, facecolor=CORES["fundo_componente"])
        ax = fig.add_subplot(111)
        ax.pie([alunos, profs], labels=['Alunos', 'Professores'], autopct='%1.1f%%', startangle=90, colors=[CORES["acento"], CORES["suporte"]])
        ax.set_title("Distribuição de Usuários no Sistema")
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20, fill='x', expand=True)

    def criar_gerenciador_usuarios(self):
        """Cria a interface da aba de gerenciamento de usuários (tabela + botões)."""
        frame = self.aba_gerenciar_usuarios
        tk.Label(frame, text="Gestão de Usuários do Sistema", font=FONT_SUBTITULO, bg=CORES["fundo_componente"], fg=CORES["texto_escuro"]).pack(pady=20, padx=10, anchor="w")

        main_content = tk.Frame(frame, bg=CORES["fundo_componente"])
        main_content.pack(fill="both", expand=True)
        main_content.column_configure(0, weight=4); main_content.column_configure(1, weight=1)
        
        tabela_frame = tk.Frame(main_content, bg=CORES["fundo_componente"])
        tabela_frame.grid(row=0, column=0, sticky="nsew")
        self.criar_tabela(tabela_frame, self.controller.dados['usuarios'], {'id': 50, 'nome': 250, 'usuario': 150, 'papel': 150})

        botoes_frame = tk.Frame(main_content, bg=CORES["fundo_componente"])
        botoes_frame.grid(row=0, column=1, sticky="ns", padx=20)
        tk.Button(botoes_frame, text="Adicionar Novo", font=FONT_BOTAO, bg=CORES["sucesso"], fg=CORES["texto_claro"], relief="flat", command=self.adicionar_usuario).pack(pady=10, ipady=8, fill="x")
        tk.Button(botoes_frame, text="Editar Selecionado", font=FONT_BOTAO, bg=CORES["acento"], fg=CORES["texto_claro"], relief="flat", command=self.editar_usuario).pack(pady=10, ipady=8, fill="x")
        tk.Button(botoes_frame, text="Excluir Selecionado", font=FONT_BOTAO, bg=CORES["erro"], fg=CORES["texto_claro"], relief="flat", command=self.excluir_usuario).pack(pady=10, ipady=8, fill="x")

    def adicionar_usuario(self):
        """Abre a janela de formulário para adicionar um novo usuário."""
        UserFormWindow(self, self.controller)

    def editar_usuario(self):
        """Abre a janela de formulário para editar o usuário selecionado na tabela."""
        selected_item = self.tree.focus() if self.tree else None
        if not selected_item:
            messagebox.showwarning("Nenhum Usuário Selecionado", "Por favor, selecione um usuário na lista para editar.")
            return
        
        user_id = int(selected_item)
        user_data = self.controller.dados['usuarios'][self.controller.dados['usuarios']['id'] == user_id].iloc[0]
        UserFormWindow(self, self.controller, user_data)
        
    def excluir_usuario(self):
        """Exclui o usuário selecionado na tabela após confirmação."""
        selected_item = self.tree.focus() if self.tree else None
        if not selected_item:
            messagebox.showwarning("Nenhum Usuário Selecionado", "Por favor, selecione um usuário na lista para excluir.")
            return

        user_id = int(selected_item)
        # Proteção para não excluir o admin principal
        if user_id == 1:
            messagebox.showerror("Ação Proibida", "Não é possível excluir o administrador principal do sistema.")
            return

        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir o usuário selecionado? Esta ação não pode ser desfeita."):
            df_usuarios = self.controller.dados['usuarios']
            df_usuarios = df_usuarios[df_usuarios['id'] != user_id]
            try:
                df_usuarios.to_csv(ARQUIVOS_CSV['usuarios'], sep=';', index=False, encoding='utf-8')
                admin_user = self.controller.usuario_logado['usuario']
                registrar_log(f"ADMIN '{admin_user}' EXCLUIU usuario ID {user_id}.")
                messagebox.showinfo("Sucesso", "Usuário excluído com sucesso.")
                self.controller.recarregar_e_redesenhar("AdminDashboard")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar as alterações: {e}")

    def criar_aba_sistema(self):
        """Cria a interface da aba de sistema, com a funcionalidade de backup."""
        frame = self.aba_sistema
        tk.Label(frame, text="Manutenção do Sistema", font=FONT_SUBTITULO, bg=CORES["fundo_componente"], fg=CORES["texto_escuro"]).pack(pady=20, padx=20, anchor="w")
        
        tk.Label(frame, text="Crie uma cópia de segurança de todos os dados do sistema.", font=FONT_NORMAL, bg=CORES["fundo_componente"]).pack(padx=20, anchor="w")
        tk.Button(frame, text="Fazer Backup dos Dados Agora", font=FONT_BOTAO, bg=CORES["acento"], fg=CORES["texto_claro"], relief="flat", command=self.fazer_backup).pack(pady=20, ipady=10, ipadx=20)
    
    def fazer_backup(self):
        """Copia todos os arquivos da pasta 'data' para uma nova pasta de backup."""
        backup_dir = "backup"
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            backup_subdir = os.path.join(backup_dir, f"backup_{timestamp}")
            
            # Copia a pasta 'data' inteira para o novo subdiretório de backup
            shutil.copytree(DATA_DIR, backup_subdir)
            
            registrar_log(f"BACKUP SUCESSO: Backup dos dados realizado para a pasta '{backup_subdir}'.")
            messagebox.showinfo("Backup Concluído", f"Cópia de segurança dos dados foi salva com sucesso em:\n{os.path.abspath(backup_subdir)}")

        except Exception as e:
            registrar_log(f"BACKUP FALHA: Erro durante o processo de backup - {e}")
            messagebox.showerror("Erro de Backup", f"Ocorreu um erro durante o backup: {e}")

# --- Os painéis de Professor e Aluno são incluídos abaixo ---
class ProfessorDashboard(BaseDashboard):
    pass
    
class AlunoDashboard(BaseDashboard):
    pass

# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = App()
    app.mainloop()
