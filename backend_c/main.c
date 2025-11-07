#include "estruturas.h"

// =================================================================
// --- 1. DEFINIÇÃO DAS VARIÁVEIS GLOBAIS (Inicialização) ---
// =================================================================

Aluno *alunos = NULL;
int num_alunos = 0;

Professor *professores = NULL;
int num_professores = 0;

Turma *turmas = NULL;
int num_turmas = 0;

Atividade *atividades = NULL;
int num_atividades = 0;

Matricula *matriculas = NULL;
int num_matriculas = 0;

Nota *notas = NULL;
int num_notas = 0;

// Usuário Administrador Mestre (ID fixo: 1)
Usuario admin_master = {
    .id = 1,
    .nome = "ADMINISTRADOR GERAL",
    .login = "admin",
    .senha = "1234", // Senha padrao
    .tipo_acesso = ACESSO_ADMIN
};


// =================================================================
// --- 2. FUNÇÕES AUXILIARES DE I/O E UTILIDADE ---
// =================================================================

void limpa_buffer() {
    int c;
    while ((c = getchar()) != '\n' && c != EOF);
}

// Lógica de Criptografia Simples
void criptografar_string(char *str) {
    for (int i = 0; str[i] != '\0'; i++) {
        if (isalnum(str[i])) {
            str[i] = str[i] + CHAVE_CRIPTOGRAFIA;
        }
    }
}

void descriptografar_string(char *str) {
    for (int i = 0; str[i] != '\0'; i++) {
        if (isalnum(str[i])) {
            str[i] = str[i] - CHAVE_CRIPTOGRAFIA;
        }
    }
}

// Obtém o próximo ID disponível 
int obter_proximo_id(const char *nome_arquivo, size_t tamanho_struct) {
    if (strcmp(nome_arquivo, "alunos.csv") == 0) return num_alunos + 1;
    if (strcmp(nome_arquivo, "professores.csv") == 0) return num_professores + 1;
    if (strcmp(nome_arquivo, "turmas.csv") == 0) return num_turmas + 1;
    if (strcmp(nome_arquivo, "atividades.csv") == 0) return num_atividades + 1;
    
    return 1;
}

// Função para garantir a existência do diretório 'dados'
int garantir_diretorio_dados() {
    if (MAKE_DIR(PASTA_DADOS) == 0) {
        printf("✅ Diretorio '%s' criado ou ja existe.\n", PASTA_DADOS);
        return 1;
    } 

#ifdef _WIN32
    // No Windows, MAKE_DIR falha se já existe, mas GetLastError() confirma o motivo.
    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        printf("✅ Diretorio '%s' ja existe.\n", PASTA_DADOS);
        return 1;
    }
#else
    // No Linux/macOS, a variável global errno deve ser verificada.
    if (errno == EEXIST) {
        printf("✅ Diretorio '%s' ja existe.\n", PASTA_DADOS);
        return 1;
    }
#endif

    // Se chegou aqui, houve um erro real (permissão, etc.)
    printf("❌ Erro ao criar diretorio '%s'. Verifique as permissoes.\n", PASTA_DADOS);
    return 0;
}


// =================================================================
// --- 3. FUNÇÕES DE PERSISTÊNCIA (CSV) ---
// =================================================================

// Salva o Administrador Master (Com caminho dados/)
int salvar_admin_csv() {
    char caminho[TAMANHO_CAMINHO];
    snprintf(caminho, TAMANHO_CAMINHO, "%sadmin.csv", PASTA_DADOS);
    
    FILE *f = fopen(caminho, "w");
    if (!f) return 0;
    
    // A senha já está criptografada no struct admin_master
    fprintf(f, "%d,%s,%s,%s\n", 
        admin_master.id, admin_master.nome, admin_master.login, admin_master.senha);

    fclose(f);
    return 1;
}

// Carrega o Administrador Master (Com caminho dados/)
int carregar_admin_csv() {
    char caminho[TAMANHO_CAMINHO];
    snprintf(caminho, TAMANHO_CAMINHO, "%sadmin.csv", PASTA_DADOS);
    
    FILE *f = fopen(caminho, "r");
    if (!f) return 0;

    if (fscanf(f, "%d,%99[^,],%49[^,],%49[^\n]", 
        &admin_master.id, admin_master.nome, admin_master.login, admin_master.senha) == 4) {
        
        fclose(f);
        return 1;
    }
    
    fclose(f);
    return 0;
}

// Função de salvamento 
int salvar_dados_csv(const char *nome_arquivo, const void *dados, int num_registros, size_t tamanho_struct, int tipo_acesso) {
    char caminho[TAMANHO_CAMINHO];
    snprintf(caminho, TAMANHO_CAMINHO, "%s%s", PASTA_DADOS, nome_arquivo);

    FILE *f = fopen(caminho, "w");
    if (!f) {
        printf("❌ Erro ao abrir arquivo %s para escrita. Verifique o diretorio.\n", caminho);
        return 0;
    }
    
    for (int i = 0; i < num_registros; i++) {
        const void *registro = (const char *)dados + i * tamanho_struct;

        if (tipo_acesso == ACESSO_ALUNO) {
            const Aluno *a = (const Aluno *)registro;
            // Senha já deve estar criptografada antes da chamada de salvamento
            fprintf(f, "%d,%s,%s,%s,%s,%s\n", a->id, a->nome, a->matricula, a->cpf, a->login, a->senha);
        } else if (tipo_acesso == ACESSO_PROFESSOR) {
            const Professor *p = (const Professor *)registro;
            fprintf(f, "%d,%s,%s,%s,%s,%s\n", p->id, p->nome, p->siape, p->cpf, p->login, p->senha);
        } else if (strcmp(nome_arquivo, "turmas.csv") == 0) {
             const Turma *t = (const Turma *)registro;
             fprintf(f, "%d,%s,%s,%s,%d\n", t->id, t->nome, t->codigo, t->semestre, t->id_professor_responsavel);
        } else if (strcmp(nome_arquivo, "atividades.csv") == 0) {
            const Atividade *a = (const Atividade *)registro;
            fprintf(f, "%d,%s,%d,%.2f,%s\n", a->id, a->descricao, a->id_turma, a->peso, a->data_entrega);
        } else if (strcmp(nome_arquivo, "matriculas.csv") == 0) {
            const Matricula *m = (const Matricula *)registro;
            fprintf(f, "%d,%d\n", m->id_aluno, m->id_turma);
        } else if (strcmp(nome_arquivo, "notas.csv") == 0) {
            const Nota *n = (const Nota *)registro;
            fprintf(f, "%d,%d,%.2f\n", n->id_atividade, n->id_aluno, n->nota);
        }
    }
    
    fclose(f);
    return 1;
}

// Função auxiliar para carregar uma lista de structs 
static int carregar_lista(const char *nome_arquivo, void **registros_ptr, int *num_registros_ptr, size_t tamanho_struct, int tipo) {
    char caminho[TAMANHO_CAMINHO];
    snprintf(caminho, TAMANHO_CAMINHO, "%s%s", PASTA_DADOS, nome_arquivo);

    FILE *f = fopen(caminho, "r");
    if (!f) return 0;

    char linha[512];
    *num_registros_ptr = 0;
    *registros_ptr = NULL;

    while (fgets(linha, sizeof(linha), f)) {
        void *novo_registro = alocar_novo_registro_generico(registros_ptr, num_registros_ptr, tamanho_struct);

        // Aluno
        if (tipo == ACESSO_ALUNO) {
            Aluno *a = (Aluno *)novo_registro;
            sscanf(linha, "%d,%99[^,],%19[^,],%14[^,],%49[^,],%49[^\n]", 
                &a->id, a->nome, a->matricula, &a->cpf[0], a->login, a->senha);
        } 
        // Professor
        else if (tipo == ACESSO_PROFESSOR) {
            Professor *p = (Professor *)novo_registro;
            sscanf(linha, "%d,%99[^,],%19[^,],%14[^,],%49[^,],%49[^\n]", 
                &p->id, p->nome, p->siape, &p->cpf[0], p->login, p->senha);
        }
        // Turma 
        else if (tipo == 4) { 
            Turma *t = (Turma *)novo_registro;
            sscanf(linha, "%d,%99[^,],%19[^,],%9[^,],%d", 
                &t->id, t->nome, t->codigo, t->semestre, &t->id_professor_responsavel);
        }
        // Atividade 
        else if (tipo == 5) { 
            Atividade *a = (Atividade *)novo_registro;
            float peso_temp;
            sscanf(linha, "%d,%149[^,],%d,%f,%10[^\n]", 
                &a->id, a->descricao, &a->id_turma, &peso_temp, a->data_entrega);
            a->peso = peso_temp;
        }
        // Matricula
        else if (tipo == 6) { 
            Matricula *m = (Matricula *)novo_registro;
            sscanf(linha, "%d,%d", &m->id_aluno, &m->id_turma);
        }
        // Nota 
        else if (tipo == 7) { 
            Nota *n = (Nota *)novo_registro;
            sscanf(linha, "%d,%d,%f", &n->id_atividade, &n->id_aluno, &n->nota);
        }
    }

    fclose(f);
    printf("✅ %d registros de %s carregados.\n", *num_registros_ptr, nome_arquivo);
    return 1;
}


int carregar_dados_csv() {
    if (!carregar_admin_csv()) {
        if (strcmp(admin_master.senha, "1234") == 0) { // Verifica a senha padrao antes de criptografar
            criptografar_string(admin_master.senha);
            salvar_admin_csv();
            printf("✅ Admin Master inicializado (Login: admin, Senha: 1234).\n");
        }
    } else {
        printf("✅ Admin Master carregado com sucesso.\n");
    }

    // Carregamento de dados de todas as outras estruturas
    carregar_lista("alunos.csv", (void **)&alunos, &num_alunos, sizeof(Aluno), ACESSO_ALUNO);
    carregar_lista("professores.csv", (void **)&professores, &num_professores, sizeof(Professor), ACESSO_PROFESSOR);
    carregar_lista("turmas.csv", (void **)&turmas, &num_turmas, sizeof(Turma), 4);
    carregar_lista("atividades.csv", (void **)&atividades, &num_atividades, sizeof(Atividade), 5);
    carregar_lista("matriculas.csv", (void **)&matriculas, &num_matriculas, sizeof(Matricula), 6);
    carregar_lista("notas.csv", (void **)&notas, &num_notas, sizeof(Nota), 7);

    return 1;
}


void liberar_memoria() {
    free(alunos);
    free(professores);
    free(turmas);
    free(atividades);
    free(matriculas);
    free(notas);
    printf("\nMemoria liberada. Sistema encerrado.\n");
}


// =================================================================
// --- 4. FUNÇÕES DE AUTENTICAÇÃO E INICIALIZAÇÃO ---
// =================================================================

void inicializar_sistema() {
    if (!garantir_diretorio_dados()) {
        printf("🚨 O sistema nao pode continuar sem o diretorio 'dados/'. Encerrando.\n");
        exit(EXIT_FAILURE);
    }
    carregar_dados_csv();
}

int fazer_login(int tipo_acesso_desejado, int *id_usuario_logado) {
    char login_input[MAX_LOGIN];
    char senha_input[MAX_SENHA];

    printf("\n--- LOGIN ---\n");
    printf("Login: "); scanf(" %49s", login_input); limpa_buffer();
    printf("Senha: "); scanf(" %49s", senha_input); limpa_buffer();
    
    // Criptografa a senha de entrada para comparação
    criptografar_string(senha_input);
    
    // 1. Tenta login como ADMIN
    if (tipo_acesso_desejado == ACESSO_ADMIN || tipo_acesso_desejado == ACESSO_NAO_AUTENTICADO) {
        if (strcmp(login_input, admin_master.login) == 0 && strcmp(senha_input, admin_master.senha) == 0) {
            *id_usuario_logado = admin_master.id;
            return ACESSO_ADMIN;
        }
    }

    // 2. Tenta login como PROFESSOR
    if (tipo_acesso_desejado == ACESSO_PROFESSOR || tipo_acesso_desejado == ACESSO_NAO_AUTENTICADO) {
        for (int i = 0; i < num_professores; i++) {
            if (strcmp(login_input, professores[i].login) == 0 && strcmp(senha_input, professores[i].senha) == 0) {
                *id_usuario_logado = professores[i].id;
                return ACESSO_PROFESSOR;
            }
        }
    }

    // 3. Tenta login como ALUNO
    if (tipo_acesso_desejado == ACESSO_ALUNO || tipo_acesso_desejado == ACESSO_NAO_AUTENTICADO) {
        for (int i = 0; i < num_alunos; i++) {
            if (strcmp(login_input, alunos[i].login) == 0 && strcmp(senha_input, alunos[i].senha) == 0) {
                *id_usuario_logado = alunos[i].id;
                return ACESSO_ALUNO;
            }
        }
    }

    return ACESSO_NAO_AUTENTICADO;
}


// =================================================================
// --- 5. FUNÇÃO PRINCIPAL DE MENU E EXECUÇÃO ---
// =================================================================

void main_menu() {
    int tipo_acesso = ACESSO_NAO_AUTENTICADO;
    int id_usuario = 0;
    int opcao;

    do {
        printf("\n===================================\n");
        printf("--- SISTEMA DE GESTÃO ACADÊMICA ---\n");
        printf("===================================\n");
        printf("1. Login\n");
        printf("0. Sair\n");
        printf("Opcao: ");

        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        if (opcao == 1) {
            tipo_acesso = fazer_login(ACESSO_NAO_AUTENTICADO, &id_usuario);

            switch (tipo_acesso) {
                case ACESSO_ADMIN:
                    printf("\n🎉 Login de Administrador bem-sucedido!\n");
                    menu_admin(id_usuario);
                    break;
                case ACESSO_PROFESSOR:
                    printf("\n🎉 Login de Professor bem-sucedido!\n");
                    menu_professor(id_usuario);
                    break;
                case ACESSO_ALUNO:
                    printf("\n🎉 Login de Aluno bem-sucedido!\n");
                    menu_aluno(id_usuario);
                    break;
                default:
                    printf("\n❌ Credenciais invalidas. Tente novamente.\n");
                    break;
            }
        } else if (opcao == 0) {
            printf("Encerrando o sistema...\n");
        } else {
            printf("Opcao invalida.\n");
        }

    } while (opcao != 0);
}


int main() {
    inicializar_sistema();
    main_menu();
    liberar_memoria();
    return 0;

}
