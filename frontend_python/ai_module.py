import os
from dotenv import load_dotenv
import re
from typing import Dict, Any, Optional, Union, Callable
from decimal import Decimal, InvalidOperation

# =================================================================
# --- CARREGAR VARIÁVEIS DE AMBIENTE ---
# =================================================================
load_dotenv()  

# Importação condicional e mock para robustez
try:
    from google import genai
    from google.genai import types
    from google.genai.client import Client as GeminiClient
    from google.genai.errors import APIError
except ImportError:
    genai = None
    types = None
    # Define o mock da classe
    GeminiClient = Any 
    APIError = type('APIError', (Exception,), {}) 

# =================================================================
# --- CONFIGURAÇÕES E CONSTANTES ---
# =================================================================

# 🚨 CHAVE DE API 🚨
API_KEY = os.environ.get("GEMINI_API_KEY", "PLACEHOLDER_NOT_FOUND")

# Constantes para a lógica da IA Manual (Offline)
LIMITE_ALERTA = 6.0              # Notas abaixo disso indicam risco de reprovação
LIMITE_MARGINAL = 7.0            # Notas entre 6.0 e 7.0 precisam de consolidação
LIMITE_BOM_DESEMPENHO = 8.0      # Média geral ou nota acima disso é satisfatória (Melhorado de 7.0 para 8.0 para maior rigor)
LIMITE_DESTAQUE = 9.0            # Nota acima disso é excelência (Melhorado de 8.5 para 9.0)
LIMITE_EVASAO_ALERTA_MONITOR = 0.08 # 8% - Monitoramento Necessário
LIMITE_EVASAO_ALERTA_CRISE = 0.15    # 15% - Crise de Retenção

# --- Inicialização do Cliente Gemini ---
CLIENTE_GEMINI: Optional['GeminiClient'] = None  # type: ignore

# Verifica se a biblioteca está instalada e se a chave NÃO é o placeholder
if genai and API_KEY and API_KEY != "PLACEHOLDER_NOT_FOUND":
    try:
        CLIENTE_GEMINI = genai.Client(api_key=API_KEY)
        # print("INFO: Cliente Gemini inicializado com sucesso. Modo ONLINE ativo.")
    except Exception as e:
        # print(f"ERRO ao inicializar o cliente Gemini com a chave fornecida: {e}")
        CLIENTE_GEMINI = None
# elif API_KEY == "PLACEHOLDER_NOT_FOUND":
#     print("AVISO: Variável de ambiente GEMINI_API_KEY não encontrada (Verifique o .env). Apenas o motor manual estará disponível.")
# elif not genai:
#     print("AVISO: Biblioteca Google GenAI (google-genai) não encontrada. Apenas o motor manual estará disponível.")


# =================================================================
# --- FUNÇÕES DE IA MANUAL (OFFLINE) ---
# =================================================================

def _analisar_dados_aluno(dados_para_ia: str) -> str:
    """
    Analisa a string de dados do aluno e gera o resumo com base nas regras (Melhorado).
    """
    linhas = dados_para_ia.strip().split('\n')
    notas: Dict[str, float] = {}

    regex_nota = re.compile(r'([^:]+):\s*([\d\.\,]+)') 
    
    # 1. Parsing dos dados (DISCIPLINA: NOTA)
    for linha in linhas:
        if 'RELATORIO_NOTAS:' in linha:
            continue
            
        match = regex_nota.search(linha)
        if match:
            disciplina, nota_str = match.groups()
            disciplina = disciplina.strip()
            
            try:
                # Converte para float, garantindo que vírgulas sejam pontos
                nota = float(nota_str.replace(',', '.').strip())
                notas[disciplina] = nota
            except ValueError:
                pass # Ignora notas inválidas

    if not notas:
        return "**Relatório de Aluno:** Não foram encontradas notas válidas para análise."
        
    # 2. Heurísticas de Análise
    media_geral = sum(notas.values()) / len(notas)
    disciplinas_risco = {d: n for d, n in notas.items() if n < LIMITE_ALERTA}
    disciplinas_marginais = {d: n for d, n in notas.items() if LIMITE_ALERTA <= n < LIMITE_MARGINAL}
    disciplinas_altas = {d: n for d, n in notas.items() if n >= LIMITE_DESTAQUE}
    
    # 3. Geração do Relatório Estruturado (Melhorado)
    relatorio = [
        f"**VISÃO GERAL DO ALUNO:** (Média: {media_geral:.2f})",
        "---"
    ]
    
    # TENDÊNCIAS
    relatorio.append(f"**TENDÊNCIAS:**")
    if media_geral >= LIMITE_DESTAQUE:
        desempenho_label = 'excelente (ACIMA DE 9.0)'
    elif media_geral >= LIMITE_BOM_DESEMPENHO:
        desempenho_label = 'bom (ACIMA DE 8.0)'
    else:
        desempenho_label = 'regular'
        
    relatorio.append(f" * Desempenho geral é **{desempenho_label}** na média.")
    
    if disciplinas_altas:
        destaques = [f"{d} ({n:.1f})" for d, n in disciplinas_altas.items()]
        relatorio.append(f" * **Destaques:** Aproveitamento de excelência em: {', '.join(destaques)}.")
    else:
        relatorio.append(" * Não há disciplinas de excelência neste período (nota >= 9.0).")


    # PONTOS DE ATENÇÃO
    relatorio.append(f"\n**PONTOS DE ATENÇÃO:**")
    if disciplinas_risco:
        alertas = [f"{d} (Nota: {n:.1f})" for d, n in disciplinas_risco.items()]
        relatorio.append(f" * **ALERTA DE RISCO (ABAixo de 6.0):** Atenção urgente em: {'; '.join(alertas)}.")
    
    if disciplinas_marginais:
        marginais = [f"{d} (Nota: {n:.1f})" for d, n in disciplinas_marginais.items()]
        relatorio.append(f" * **Notas Marginais (6.0 a 7.0):** Necessitam de consolidação: {'; '.join(marginais)}.")
    
    if not disciplinas_risco and not disciplinas_marginais:
        relatorio.append(" * Nenhuma disciplina identificada com nota inferior a 7.0.")
        
    # AÇÕES SUGERIDAS
    relatorio.append(f"\n**RECOMENDAÇÕES:**")
    if disciplinas_risco or disciplinas_marginais:
        relatorio.append(" * **Prioridade:** Revisão focada e monitoria nas disciplinas de risco e marginais.")
        if disciplinas_risco:
             relatorio.append(" * Urgente: Criar plano de recuperação para elevar notas críticas acima de 7.0.")
        else:
             relatorio.append(" * Foco: Trabalhar na consistência para que as notas marginais atinjam o patamar de 8.0.")
    else:
        relatorio.append(" * Continuar a consistência. Explorar o aprofundamento nas áreas de destaque.")
        
    return "\n".join(relatorio)

def _analisar_dados_professor(dados_para_ia: str) -> str:
    """
    Analisa dados de professor com parsing mais robusto para média e desvio padrão.
    """
    
    # 1. BUSCA E TRATAMENTO DA MÉDIA DA TURMA
    match_media = re.search(r'Media_Turma:\s*([\d\.\,]+)', dados_para_ia)
    media_turma = 0.0
    if match_media:
        try:
            # Substitui vírgula por ponto (caso venha no formato brasileiro) e converte para float
            media_turma = float(match_media.group(1).replace(',', '.'))
        except ValueError:
             # Se a conversão falhar, mantém 0.0
             pass 

    # 2. BUSCA E TRATAMENTO DO DESVIO PADRÃO
    match_desvio_padrao = re.search(r'Desvio_Padrao:\s*([\d\.\,]+)', dados_para_ia)
    desvio_padrao = 0.0
    if match_desvio_padrao:
        try:
            desvio_padrao = float(match_desvio_padrao.group(1).replace(',', '.'))
        except ValueError:
            # Se a conversão falhar, mantém 0.0
            pass 

    # 3. BUSCA DO TOTAL DE TURMAS
    match_turmas = re.search(r'Total_Turmas:\s*(\d+)', dados_para_ia)
    total_turmas = int(match_turmas.group(1)) if match_turmas else 0
    
    
    # 4. LÓGICA DE ANÁLISE 
    
    # Ajustando limites para consistência com o restante do código
    LIMITE_ALERTA = 6.0
    LIMITE_BOM_DESEMPENHO = 8.0 

    alerta_media = ""
    if media_turma >= LIMITE_BOM_DESEMPENHO:
        alerta_media = f"Desempenho geral da turma é satisfatório (acima de {LIMITE_BOM_DESEMPENHO:.1f})."
    elif media_turma > LIMITE_ALERTA:
        alerta_media = "Desempenho mediano. Necessário foco na consolidação das notas."
    elif media_turma > 0.0:
        alerta_media = "**ALERTA DE DESEMPENHO COLETIVO!** Revisão da metodologia ou conteúdo é sugerida."
    else:
        alerta_media = "Dados insuficientes ou inválidos para análise de média."
        
    alerta_variacao = ""
    if desvio_padrao > 2.0:
        alerta_variacao = "**ALERTA DE VARIAÇÃO ALTA!** Indica grande diferença de notas. Sugere-se nivelamento e suporte aos extremos."
    elif desvio_padrao > 1.0:
        alerta_variacao = "Variação moderada nas notas. Monitorar alunos nos extremos de desempenho."
    else:
        alerta_variacao = "Variação normal."

            
    resumo_analise = (
        f"**VISÃO GERAL DO PROFESSOR:**\n"
        f" * **Total de Turmas:** {total_turmas}\n"
        f" * **Média da Turma:** {media_turma:.2f}\n"
        f" * **Variação (Desvio Padrão):** {desvio_padrao:.2f}\n"
        f" * **Análise de Média:** {alerta_media}\n"
        f" * **Análise de Variação:** {alerta_variacao}\n"
        f"\n**RECOMENDAÇÕES:**\n"
        f" * Focar em atividades de recuperação para o quartil de baixo desempenho.\n"
        f" * Promover a troca de boas práticas com professores de turmas de alto desempenho."
    )
    return resumo_analise

def _analisar_dados_admin(dados_para_ia: str) -> str:
    """
    Analisa dados de administrador (placeholder) com base em regras (Melhorado).
    """
    
    # Constantes 
    LIMITE_EVASAO_ALERTA_CRISE = 0.15
    LIMITE_EVASAO_ALERTA_MONITOR = 0.08
    
    # 1. Busca de Taxa de Evasão 
    match_evasao = re.search(r'Taxa_Evasao_Ultimo_Semestre:\s*([\d\.]+)', dados_para_ia)
    taxa_evasao_float = 0.0
    taxa_evasao = 'N/A'
    alerta_evasao = "KPIs de retenção em controle."
    
    if match_evasao:
        try:
            taxa_evasao_float = float(match_evasao.group(1)) 
            taxa_evasao = f"{taxa_evasao_float * 100:.2f}%"
            
            if taxa_evasao_float > LIMITE_EVASAO_ALERTA_CRISE:
                alerta_evasao = f"**ALERTA DE CRISE DE RETENÇÃO!** Evasão ({taxa_evasao}) acima de {LIMITE_EVASAO_ALERTA_CRISE * 100:.0f}%."
            elif taxa_evasao_float > LIMITE_EVASAO_ALERTA_MONITOR:
                alerta_evasao = f"**ALERTA DE MONITORAMENTO!** Evasão ({taxa_evasao}) acima do limite de {LIMITE_EVASAO_ALERTA_MONITOR * 100:.0f}%."
                
        except ValueError:
            pass 

    # 2. Busca de Totais Administrativos 
    
    # Função auxiliar para busca segura de inteiros
    def buscar_total(chave: str, dados: str) -> int:
        match = re.search(rf'{chave}:\s*(\d+)', dados)
        return int(match.group(1)) if match else 0

    total_alunos = buscar_total('Total_Alunos', dados_para_ia)
    total_professores = buscar_total('Total_Professores', dados_para_ia)
    total_turmas = buscar_total('Total_Turmas', dados_para_ia)

    # 3. Geração do Relatório 
    resumo_analise = (
        f"**RELATÓRIO INSTITUCIONAL (GESTÃO):**\n"
        f" * **Total de Alunos:** {total_alunos}\n"
        f" * **Total de Professores:** {total_professores}\n"
        f" * **Total de Turmas:** {total_turmas}\n"
        f" * **Taxa de Evasão Semestral:** {taxa_evasao}\n"
        f" * **Status de Retenção:** {alerta_evasao}\n"
        f"\n**RECOMENDAÇÕES:**\n"
        f" * Investigar a correlação entre as disciplinas com menor média geral e os dados de evasão.\n"
        f" * Avaliar a necessidade de suporte financeiro ou acadêmico para alunos em risco."
    )
    return resumo_analise

def gerar_relatorio_manual(nome_usuario: str, dados_para_ia: str, tipo_usuario: str) -> str:
    """
    Motor de Análise de IA Manual/Offline. Implementa a lógica de regras para diferentes usuários.
    """
    
    tipo_usuario = tipo_usuario.lower()
    
    # Mapeamento para evitar grandes blocos if/elif
    analisadores: Dict[str, Callable[[str], str]] = {
        'aluno': _analisar_dados_aluno,
        'professor': _analisar_dados_professor,
        'admin': _analisar_dados_admin
    }
    
    analisador = analisadores.get(tipo_usuario)
    
    if analisador:
        resumo_analise = analisador(dados_para_ia)
    else:
        resumo_analise = "Simulação IA Manual: Tipo de usuário não reconhecido."
        
    # Formatação final
    return (
        f"--- RELATÓRIO MANUAL DE ANÁLISE DE DADOS PARA {nome_usuario} ({tipo_usuario.upper()}) ---\n"
        f"***Este relatório foi gerado OFFLINE pelo motor de análise de regras.***\n\n"
        f"{resumo_analise}\n"
    )

# =================================================================
# --- FUNÇÃO PRINCIPAL (API ou Manual) ---
# =================================================================

def gerar_relatorio_ia(nome_usuario: str, dados_para_ia: str, tipo_usuario: str) -> str:
    """
    Gera um relatório de análise de dados. Tenta usar o modelo Gemini e, 
    em caso de falha de inicialização ou indisponibilidade, usa o motor manual.
    """

    # 1. VERIFICAÇÃO INICIAL (Chave inválida, biblioteca ausente ou erro de inicialização)
    if CLIENTE_GEMINI is None:
        # print("INFO: Cliente Gemini não disponível ou chave não configurada. Gerando relatório manualmente (OFFLINE).")
        return gerar_relatorio_manual(nome_usuario, dados_para_ia, tipo_usuario)

    # --- Construção do Prompt ---
    
    tipo_usuario_lower = tipo_usuario.lower()
    
    # Perfil de Análise para cada tipo de usuário (para guiar o Gemini)
    perfis: Dict[str, str] = {
        'aluno': "Foque a análise em correlações entre disciplinas, sugerindo planos de ação estritamente individuais.",
        'professor': "Foque a análise na performance coletiva da turma, variância de notas e o impacto potencial da metodologia de ensino. Suas recomendações devem ser pedagógicas.",
        'admin': "Foque a análise em KPIs institucionais como taxas de retenção/evasão, volume de alunos e impacto financeiro/estrutural. Suas recomendações devem ser estratégicas e de gestão.",
    }
    
    perfil_analise = perfis.get(tipo_usuario_lower, "Gere um relatório de análise de alto nível.")

    contexto = (
        f"Você é uma IA analítica especializada em dados acadêmicos. "
        f"Gere um relatório EXTREMAMENTE CONCISO (máximo de 5 parágrafos curtos) e de ALTO NÍVEL "
        f"para o usuário '{nome_usuario}', que é um {tipo_usuario_lower}. "
        f"{perfil_analise} "
        f"Use **apenas** formatação Markdown (títulos, negrito e bullet points). "
        f"NUNCA repita os dados brutos de entrada. "
        f"Sua análise deve conter OBRIGATORIAMENTE e APENAS as seções: **TENDÊNCIAS**, **PONTOS DE ATENÇÃO** e **RECOMENDAÇÕES**. "
        f"Responda APENAS o conteúdo do relatório, sem introduções, saudações ou texto extra. "
        f"O relatório deve começar com a seção **TENDÊNCIAS**. "
        f"Siga o formato Markdown EXATO abaixo:\n"
        f"## **TENDÊNCIAS**\n\n * [Ponto 1]\n * [Ponto 2]\n\n## **PONTOS DE ATENÇÃO**\n\n * [Ponto 1]\n\n## **RECOMENDAÇÕES**\n\n * [Recomendação 1]"
    )
    
    prompt = f"""
{contexto}

--- DADOS ACADÊMICOS BRUTOS PARA ANÁLISE ---
{dados_para_ia}
"""

    # --- Chamada à API (com Fallback em caso de erro de rede ou API) ---
    try:
        # print(f"INFO: Tentando gerar relatório via API Gemini (ONLINE)...")
        # Define o modelo e faz a chamada
        response = CLIENTE_GEMINI.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1, # Temperatura baixa para resultados mais factuais e menos criativos
            )
        )
        
        # O modelo pode gerar o prompt de formato, então removemos o cabeçalho gerado pelo prompt
        relatorio_limpo = response.text.strip()
        
        # Heurística para remover o cabeçalho do formato que foi injetado no prompt, caso o modelo o repita
        format_start = "## **TENDÊNCIAS**"
        format_index = relatorio_limpo.find(format_start)
        if format_index > 0:
            # Tenta encontrar a primeira ocorrência do cabeçalho obrigatório para garantir o início limpo
            relatorio_limpo = relatorio_limpo[format_index:].strip()

        return (
            f"--- RELATÓRIO DE ANÁLISE DE DADOS PARA {nome_usuario} ({tipo_usuario.upper()}) ---\n"
            f"***Este relatório foi gerado ONLINE pelo modelo Gemini-2.5-Flash.***\n\n"
            f"{relatorio_limpo}"
        )
    
    except APIError as e:
        # 2. FALLBACK: ERRO NA API
        # print(f"ALERTA: Erro na API Gemini. Detalhes: {e}. Executando fallback manual...")
        return gerar_relatorio_manual(nome_usuario, dados_para_ia, tipo_usuario)
        
    except Exception as e:
        # 3. FALLBACK: ERRO DE CONEXÃO ou OUTROS ERROS
        # print(f"ALERTA: Erro desconhecido (provavelmente de conexão/rede): {e}. Executando fallback manual...")
        return gerar_relatorio_manual(nome_usuario, dados_para_ia, tipo_usuario)

# =================================================================
# --- EXEMPLO DE USO ---
# =================================================================
if __name__ == '__main__':
    print("\n" + "="*50)
    print("DEMONSTRAÇÃO DO SISTEMA DE RELATÓRIOS (APÓS MELHORIAS)")
    print("="*50 + "\n")

    # Exemplo 1: Aluno com baixo desempenho e notas marginais 
    dados_aluno_risco = """
Matemática: 5.5
Português: 6.8
História: 4.8
Ciências: 8.2 
Inglês: 9.3
"""
    print("\n--- TESTE 1: ALUNO (RISCO E MARGINAL) ---\n")
    relatorio_aluno_risco = gerar_relatorio_ia("João Silva", dados_aluno_risco, "Aluno")
    print(relatorio_aluno_risco)
    
    # Exemplo 2: Admin com alta evasão 
    # 0.16 = 16%
    dados_admin_alerta = """
Orçamento_Total: 15.000.000
Total_Alunos: 1500
Total_Professores: 50
Taxa_Evasao_Ultimo_Semestre: 0.16 
Cursos_Novos: 3
"""
    print("\n--- TESTE 2: ADMIN (CRISE DE RETENÇÃO) ---\n")
    relatorio_admin_alerta = gerar_relatorio_ia("Dr. Souza", dados_admin_alerta, "Admin")
    print(relatorio_admin_alerta)
    
    # Exemplo 3: Professor com média satisfatória e alta variação 
    dados_professor_ok_variacao = """
Total_Turmas: 5
Media_Turma: 8.1
Desvio_Padrao: 2.5 
"""
    print("\n--- TESTE 3: PROFESSOR (ALTA VARIAÇÃO) ---\n")
    relatorio_professor_ok = gerar_relatorio_ia("Profa. Mendes", dados_professor_ok_variacao, "Professor")
    print(relatorio_professor_ok)
