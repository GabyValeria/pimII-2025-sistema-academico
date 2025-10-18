# 📘 Manual de Uso Completo  
## Sistema Acadêmico Colaborativo (PIM II)

---

## 1. Introdução  

Bem-vindo ao **Manual do Sistema Acadêmico Colaborativo**.  
Este software foi desenvolvido como parte do **Projeto Integrado Multidisciplinar (PIM)** do curso de **Análise e Desenvolvimento de Sistemas da UNIP**.

O sistema possui uma arquitetura **cliente-servidor**, utilizando:  
- **Linguagem C** no backend — responsável pela manipulação e persistência de dados em arquivos `.csv`.  
- **Python com Tkinter** no frontend — responsável pela interface gráfica moderna, intuitiva e funcional para a interação do usuário.  

Este documento detalha todos os passos necessários para a **instalação, configuração e utilização** de todas as funcionalidades do sistema.

---

## 2. Primeiros Passos: Instalação e Configuração  

### 2.1. Pré-requisitos  

Antes de iniciar, certifique-se de que os seguintes programas estão instalados:  

- **Python 3.8+** → Necessário para executar a interface gráfica.  
  - Baixe em [python.org](https://www.python.org/downloads/).  
  - **Importante:** marque a opção *“Add Python to PATH”* durante a instalação.  

- **Compilador GCC (MinGW-w64)** → Necessário para compilar o programa em C.  
  - Siga um guia de instalação (ex: MSYS2).  
  - Certifique-se de que o compilador está adicionado ao **PATH** do sistema.

---

### 2.2. Estrutura de Pastas  

O projeto deve seguir a seguinte estrutura para funcionar corretamente:  

```
PIM_II_UNIP_ADS_2025/
│
├── backend_c/
├── frontend_python/
├── data/
├── docs/
├── compilar_backend.bat
└── requirements.txt
```

---

### 2.3. Instalação das Dependências (Python)

1. Abra o **Prompt de Comando** ou **PowerShell**.  
2. Navegue até a pasta raiz do projeto:  
   ```bash
   cd Desktop\PIM_II_UNIP_ADS_2025
   ```  
3. Instale as dependências necessárias:  
   ```bash
   pip install -r requirements.txt
   ```

---

### 2.4. Compilação do Backend (C)

1. Localize o arquivo **compilar_backend.bat** na pasta raiz.  
2. Dê **duplo clique** para executar.  
3. O terminal abrirá e executará o processo de compilação.  
4. Ao final, um arquivo `sistema_academico.exe` será criado dentro da pasta `backend_c`.

---

## 3. Acesso ao Sistema  

### 3.1. Tela de Login  

Para iniciar a interface gráfica, execute o arquivo **`app.py`** localizado na pasta `frontend_python`.  
A primeira tela exibida será a **Tela de Login**.

- **Usuário:** nome de usuário (RA para alunos).  
- **Senha:** senha cadastrada.

---

### 3.2. Credenciais de Teste  

| Perfil        | Usuário     | Senha     |
|----------------|-------------|-----------|
| Administrador  | admin       | admin     |
| Professor      | prof.silva  | senha123  |
| Aluno          | H74IAI3     | aluno1    |

---

## 4. Painel do Administrador  

O administrador possui **acesso total** a todas as funcionalidades de gestão e manutenção do sistema.

---

### 4.1. Aba: Dashboard  

Tela inicial do administrador, oferecendo uma visão geral do sistema.  

- **Indicadores Principais:**  
  - Total de Alunos  
  - Total de Professores  
  - Média Geral de Notas  

- **Gráfico de Distribuição:**  
  - Exibe a proporção de alunos e professores cadastrados (gráfico de pizza).

---

### 4.2. Aba: Gerenciar Usuários  

Controle completo sobre as contas de usuários (exceto o admin principal).

#### ➤ Visualizar Usuários  
Tabela com todos os usuários, incluindo ID, nome, login e papel.

#### ➤ Adicionar Novo Usuário  
1. Clique em **“Adicionar Novo”**.  
2. Preencha:
   - Nome Completo  
   - Usuário (Login/RA)  
   - Senha  
   - Papel (Aluno ou Professor)  
3. Clique em **“Salvar”**.

#### ➤ Editar Usuário  
1. Selecione o usuário na tabela.  
2. Clique em **“Editar Selecionado”**.  
3. Altere as informações desejadas.  
4. Clique em **“Salvar”**.

#### ➤ Excluir Usuário  
1. Selecione o usuário.  
2. Clique em **“Excluir Selecionado”**.  
3. Confirme a exclusão na caixa de diálogo.  

> ⚠️ Nota: o usuário **admin (ID 1)** não pode ser excluído.

---

### 4.3. Aba: Sistema  

Ferramentas de **manutenção e segurança** do sistema.  

#### ➤ Backup de Dados  
- Clique em **“Fazer Backup dos Dados Agora”**.  
- O sistema criará uma cópia completa da pasta `data/` (arquivos `.csv` e log).  
- O backup será salvo em `backup/backup_YYYY-MM-DD_HH-MM-SS/`.

---

## 5. Painel do Professor  

O professor gerencia as atividades acadêmicas relacionadas às suas turmas.

---

### 5.1. Aba: Lançar/Editar Notas e Frequência  

1. **Selecione o Aluno** → Lista suspensa com os alunos da turma.  
2. **Selecione a Aula** → Aula desejada.  
3. **Insira a Nota** → Valor entre 0.0 e 10.0.  
4. **Defina a Frequência** → *Presente* ou *Ausente*.  
5. **Salvar Atividade** → Registra ou atualiza os dados.

---

### 5.2. Aba: Relatórios da Turma  

Gere relatórios consolidados de desempenho.  

1. **Selecione a Turma.**  
2. **Clique em “Gerar Relatório em PDF”.**  
3. **Escolha o local e nome do arquivo.**  

O PDF conterá as **notas e frequências** de todos os alunos da turma.

---

## 6. Painel do Aluno  

O aluno tem acesso ao seu próprio desempenho acadêmico.

---

### 6.1. Painel de Desempenho  

- **Minhas Notas e Frequência:**  
  Tabela com histórico completo.  

- **Métricas de Desempenho:**  
  - Média Geral  
  - Taxa de Presença Total  

- **Análise com IA:**  
  - Exibe **alertas de desempenho** se a média for inferior a 6.0.  
  - Sugere foco nos estudos.  

- **Gráfico de Evolução:**  
  - Mostra a progressão das notas ao longo do tempo (gráfico de linha).

---

### 6.2. Gerar Relatório Individual  

Clique em **“Gerar Relatório PDF”** para exportar seu histórico completo de notas e presenças.  
O arquivo conterá todos os registros acadêmicos do aluno em formato PDF.

---

## 📄 Fim do Documento  
**Sistema Acadêmico Colaborativo - (PIM II - UNIP ADS 2025)**
