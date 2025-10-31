import os
from google import genai
from google.genai.errors import APIError

API_KEY = "AIzaSyDdQK7-y357LGV-qTNnC6YpbrNSl54oVys"

if not API_KEY:
    CLIENTE_GEMINI = None 
    print("AVISO: Chave API não encontrada.")
else:
    try:
        CLIENTE_GEMINI = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"ERRO ao inicializar o cliente Gemini: {e}")
        CLIENTE_GEMINI = None


def gerar_relatorio_ia(nome_usuario: str, dados_para_ia: str, tipo_usuario: str) -> str:
    """
    Gera um relatório de análise de dados usando o modelo Gemini,
    com foco em ser conciso e objetivo.
    """

    if CLIENTE_GEMINI is None:
        return _relatorio_mock(nome_usuario, tipo_usuario, dados_para_ia)

    # --- Construção do Prompt ---
    
    contexto = (
        f"Você é uma IA analítica especializada em dados acadêmicos e educacionais. "
        f"Gere um relatório EXTREMAMENTE CONCISO, objetivo e de ALTO NÍVEL "
        f"para o usuário '{nome_usuario}', que é um {tipo_usuario}. "
        f"Use formatação clara (títulos e bullet points) e NUNCA repita os dados brutos de entrada. "
        f"Use as informações fornecidas para identificar TENDÊNCIAS, PONTOS DE ATENÇÃO e AÇÕES SUGERIDAS."
        f"Responda APENAS o relatório."
    )
    
    prompt = (
        f"{contexto}\n\n"
        f"--- DADOS ACADÊMICOS BRUTOS PARA ANÁLISE ---\n"
        f"{dados_para_ia}"
    )

    # --- Chamada à API ---
    try:
        # Define o modelo e faz a chamada
        response = CLIENTE_GEMINI.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'temperature': 0.1,
            }
        )
        return response.text
    
    except APIError as e:
        return f"❌ ERRO NA API (Código Gemini): Falha ao gerar relatório de IA. Detalhe: {e}"
    except Exception as e:
        return f"❌ ERRO DESCONHECIDO (Módulo AI): {e}"


def _relatorio_mock(nome_usuario: str, tipo_usuario: str, dados_para_ia: str) -> str:
    """Retorna um relatório mock (falso) se o cliente Gemini não estiver inicializado."""
    
    if tipo_usuario == 'aluno':
        resumo = (
            "**Resumo Geral:** Bom desempenho, mas com risco na área de exatas.\n"
            "**Destaques Positivos:** Programação e Lógica.\n"
            "**Pontos de Atenção:** Cálculo I (Média 4.5).\n"
            "**Próximos Passos:** Revisar os tópicos de derivação e integração."
        )
    elif tipo_usuario == 'professor':
        resumo = (
            "**Visão Geral das Turmas:** 85% das turmas com média acima de 7.0.\n"
            "**Principal Desafio Encontrado:** Atividade 2 (Peso 4) na turma TADS101 teve a média mais baixa (5.1).\n"
            "**Ações Sugeridas:** Revisar o enunciado da Atividade 2 e oferecer uma monitoria extra."
        )
    elif tipo_usuario == 'admin':
        resumo = (
            "**KPIs (Indicadores Chave):** Total de Alunos: 500 | Turmas Ativas: 25 | Média Institucional: 7.2\n"
            "**Alerta Institucional:** A taxa de evasão nos últimos 6 meses subiu 10% nos cursos noturnos.\n"
            "**Prioridade de Gestão:** Analisar o perfil dos alunos evadidos e reestruturar o suporte ao aluno noturno."
        )
    else:
        resumo = "Simulação IA: Tipo de usuário não reconhecido."
        
    return (
        f"--- RELATÓRIO MOCK DE ANÁLISE DE DADOS PARA {nome_usuario} ({tipo_usuario.upper()}) ---\n"
        f"Este relatório é uma simulação, pois o cliente Gemini não foi inicializado.\n\n"
        f"{resumo}\n\n"
        f"Para mais detalhes, verifique os logs de carregamento do ai_module.py."
    )