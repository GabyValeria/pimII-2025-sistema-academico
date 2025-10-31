#include "dados.h"

// --- VARIÁVEIS GLOBAIS ---

Aluno *alunos = NULL;
int num_alunos = 0;

Professor *professores = NULL;
int num_professores = 0;

Turma *turmas = NULL;
int num_turmas = 0;

Matricula *matriculas = NULL;
int num_matriculas = 0;

Atividade *atividades = NULL;
int num_atividades = 0;

Nota *notas = NULL;
int num_notas = 0;

// Admin master fixo
Usuario admin_master = {1, "admin", "123", "Administrador Principal"};


// =================================================================
// --- 1. FUNÇÕES DE UTILIDADE E MANIPULAÇÃO DE CSV (I/O) ---
// =================================================================

// Função Auxiliar para limpeza de buffer do teclado (mais robusta)
void limpa_buffer() {
    int c;
    while ((c = getchar()) != '\n' && c != EOF);
}

// Função para garantir a existência do diretório 'dados/'
void criar_diretorio_dados() {
    // MKDIR é um macro definido em estruturas.h que usa mkdir (Unix) ou _mkdir (Windows)
    if (MKDIR("dados") == 0) {
        printf("Diretorio 'dados/' criado com sucesso.\n");
    } else if (errno != EEXIST) {
        // EEXIST significa que o diretório já existe, o que é OK
        perror("Erro ao criar diretorio 'dados/'");
        exit(EXIT_FAILURE); // Saída em caso de erro crítico
    }
}

// Função Auxiliar para obter o próximo ID (Simples)
int obter_proximo_id(const char *nome_arquivo, size_t tamanho_struct) {
    // Gera um ID grande para evitar colisão inicial
    static int ultimo_id = 1000;
    return ++ultimo_id; 
}

// Liberação de memória (função auxiliar, não usada em todo lugar, mas bom ter)
void liberar_memoria(void *ptr) {
    if (ptr != NULL) {
        free(ptr);
    }
}

// --- Funções de Formatação (Struct para Linha CSV) ---
void formatar_linha_aluno(Aluno *a, char *linha) {
    sprintf(linha, "%d;%s;%s;%s;%s;%s\n", a->id, a->nome, a->matricula, a->cpf, a->login, a->senha);
}
void formatar_linha_professor(Professor *p, char *linha) {
    sprintf(linha, "%d;%s;%s;%s;%s;%s\n", p->id, p->nome, p->siape, p->cpf, p->login, p->senha);
}
void formatar_linha_turma(Turma *t, char *linha) {
    sprintf(linha, "%d;%s;%s;%d;%s\n", t->id, t->nome, t->codigo, t->id_professor_responsavel, t->semestre);
}
void formatar_linha_atividade(Atividade *a, char *linha) {
    sprintf(linha, "%d;%d;%s;%.2f;%s\n", a->id, a->id_turma, a->descricao, a->peso, a->data_entrega);
}
void formatar_linha_matricula(Matricula *m, char *linha) {
    sprintf(linha, "%d;%d\n", m->id_turma, m->id_aluno);
}
void formatar_linha_nota(Nota *n, char *linha) {
    sprintf(linha, "%d;%d;%.2f\n", n->id_atividade, n->id_aluno, n->nota);
}

// --- Funções de Parsing (Linha CSV para Struct) ---
void parse_linha_aluno(char *linha, Aluno *a) {
    // Usa "%99[^;]" para garantir que a string tenha no máximo 99 chars antes do delimitador ;
    sscanf(linha, "%d;%99[^;];%19[^;];%14[^;];%49[^;];%49[^\n]", &a->id, a->nome, a->matricula, a->cpf, a->login, a->senha);
}
void parse_linha_professor(char *linha, Professor *p) {
    sscanf(linha, "%d;%99[^;];%19[^;];%14[^;];%49[^;];%49[^\n]", &p->id, p->nome, p->siape, p->cpf, p->login, p->senha);
}
void parse_linha_turma(char *linha, Turma *t) {
    sscanf(linha, "%d;%99[^;];%19[^;];%d;%9[^\n]", &t->id, t->nome, t->codigo, &t->id_professor_responsavel, t->semestre);
}
void parse_linha_atividade(char *linha, Atividade *a) {
    sscanf(linha, "%d;%d;%149[^;];%f;%10[^\n]", &a->id, &a->id_turma, a->descricao, &a->peso, a->data_entrega);
}
void parse_linha_matricula(char *linha, Matricula *m) {
    sscanf(linha, "%d;%d", &m->id_turma, &m->id_aluno);
}
void parse_linha_nota(char *linha, Nota *n) {
    sscanf(linha, "%d;%d;%f", &n->id_atividade, &n->id_aluno, &n->nota);
}

// Função Genérica para Carregar Dados CSV
void *carregar_dados_csv(const char *nome_arquivo, size_t tamanho_struct, int *num_registros, void **buffer_registros) {
    char caminho_completo[100];
    sprintf(caminho_completo, "dados/%s", nome_arquivo);

    FILE *arquivo = fopen(caminho_completo, "r");
    if (arquivo == NULL) {
        *num_registros = 0;
        *buffer_registros = NULL;
        return NULL; // Retorna NULL se o arquivo não existe
    }

    char linha[512];
    int capacidade = 50; 
    *num_registros = 0;

    // Pular cabeçalho
    if (fgets(linha, sizeof(linha), arquivo) == NULL) {
        fclose(arquivo);
        return NULL;
    }
    
    *buffer_registros = malloc(capacidade * tamanho_struct);
    if (*buffer_registros == NULL) {
        perror("Erro na alocacao de memoria");
        fclose(arquivo);
        return NULL;
    }

    while (fgets(linha, sizeof(linha), arquivo) != NULL) {
        if (strlen(linha) < 5) continue; 

        if (*num_registros >= capacidade) {
            capacidade *= 2; 
            void *novo_ptr = realloc(*buffer_registros, capacidade * tamanho_struct);
            if (novo_ptr == NULL) {
                perror("Erro na realocacao de memoria. Carregamento parcial.");
                break;
            }
            *buffer_registros = novo_ptr;
        }

        void *registro_atual = (char *)*buffer_registros + (*num_registros * tamanho_struct);

        // Chamada ao parser apropriado
        if (tamanho_struct == sizeof(Aluno)) parse_linha_aluno(linha, (Aluno *)registro_atual);
        else if (tamanho_struct == sizeof(Professor)) parse_linha_professor(linha, (Professor *)registro_atual);
        else if (tamanho_struct == sizeof(Turma)) parse_linha_turma(linha, (Turma *)registro_atual);
        else if (tamanho_struct == sizeof(Atividade)) parse_linha_atividade(linha, (Atividade *)registro_atual);
        else if (tamanho_struct == sizeof(Matricula)) parse_linha_matricula(linha, (Matricula *)registro_atual);
        else if (tamanho_struct == sizeof(Nota)) parse_linha_nota(linha, (Nota *)registro_atual);
        
        (*num_registros)++;
    }

    fclose(arquivo);
    // Redimensiona para o tamanho exato dos dados lidos para economizar memória
    if (*num_registros > 0) {
        void *novo_ptr = realloc(*buffer_registros, (*num_registros) * tamanho_struct);
        if (novo_ptr != NULL) {
            *buffer_registros = novo_ptr;
        }
    }
    return *buffer_registros;
}


// Função Genérica para Salvar Dados CSV 
int salvar_dados_csv(const char *nome_arquivo, void *registros, int num_registros, size_t tamanho_struct, NivelAcesso tipo) {
    criar_diretorio_dados(); 

    char caminho_completo[100];
    sprintf(caminho_completo, "dados/%s", nome_arquivo);

    FILE *arquivo = fopen(caminho_completo, "w");
    if (arquivo == NULL) {
        perror("Erro ao abrir arquivo para escrita");
        return 0;
    }

    // Geração de cabeçalho
    if (tipo == ALUNO) fprintf(arquivo, "id;nome;matricula;cpf;login;senha\n");
    else if (tipo == PROFESSOR) fprintf(arquivo, "id;nome;siape;cpf;login;senha\n");
    else if (tamanho_struct == sizeof(Turma)) fprintf(arquivo, "id;nome;codigo;id_professor_responsavel;semestre\n");
    else if (tamanho_struct == sizeof(Atividade)) fprintf(arquivo, "id;id_turma;descricao;peso;data_entrega\n");
    else if (tamanho_struct == sizeof(Matricula)) fprintf(arquivo, "id_turma;id_aluno\n");
    else if (tamanho_struct == sizeof(Nota)) fprintf(arquivo, "id_atividade;id_aluno;nota\n");

    char linha[512];
    for (int i = 0; i < num_registros; i++) {
        void *registro_atual = (char *)registros + (i * tamanho_struct);

        if (tamanho_struct == sizeof(Aluno)) formatar_linha_aluno((Aluno *)registro_atual, linha);
        else if (tamanho_struct == sizeof(Professor)) formatar_linha_professor((Professor *)registro_atual, linha);
        else if (tamanho_struct == sizeof(Turma)) formatar_linha_turma((Turma *)registro_atual, linha);
        else if (tamanho_struct == sizeof(Atividade)) formatar_linha_atividade((Atividade *)registro_atual, linha);
        else if (tamanho_struct == sizeof(Matricula)) formatar_linha_matricula((Matricula *)registro_atual, linha);
        else if (tamanho_struct == sizeof(Nota)) formatar_linha_nota((Nota *)registro_atual, linha);
        else {
            continue; 
        }
        
        fputs(linha, arquivo);
    }

    fclose(arquivo);
    return 1;
}

// Função de Inicialização: Carrega todos os dados na memória
void inicializar_sistema() {
    criar_diretorio_dados(); // Garante que o diretório existe
    printf("\nCarregando dados do sistema na pasta 'dados/'...\n");
    
    // As alocações são feitas dentro da função `carregar_dados_csv`
    alunos = (Aluno *)carregar_dados_csv("alunos.csv", sizeof(Aluno), &num_alunos, (void **)&alunos);
    professores = (Professor *)carregar_dados_csv("professores.csv", sizeof(Professor), &num_professores, (void **)&professores);
    turmas = (Turma *)carregar_dados_csv("turmas.csv", sizeof(Turma), &num_turmas, (void **)&turmas);
    matriculas = (Matricula *)carregar_dados_csv("matriculas.csv", sizeof(Matricula), &num_matriculas, (void **)&matriculas);
    atividades = (Atividade *)carregar_dados_csv("atividades.csv", sizeof(Atividade), &num_atividades, (void **)&atividades);
    notas = (Nota *)carregar_dados_csv("notas.csv", sizeof(Nota), &num_notas, (void **)&notas);
    
    printf("Carregamento concluido. Alunos: %d, Professores: %d, Turmas: %d.\n", num_alunos, num_professores, num_turmas);
}

// =================================================================
// --- 2. FUNÇÕES DE LOGIN ---
// =================================================================

int fazer_login(NivelAcesso nivel, int *id_usuario_logado) {
    char login[50], senha[50];
    printf("\n--- LOGIN ---\n");
    printf("Login: ");
    scanf("%49s", login);
    printf("Senha: ");
    scanf("%49s", senha);
    limpa_buffer(); 

    if (nivel == ADMIN) {
        if (strcmp(login, admin_master.login) == 0 && strcmp(senha, admin_master.senha) == 0) {
            *id_usuario_logado = admin_master.id;
            return 1;
        }
    } else if (nivel == PROFESSOR) {
        for (int i = 0; i < num_professores; i++) {
            if (strcmp(login, professores[i].login) == 0 && strcmp(senha, professores[i].senha) == 0) {
                *id_usuario_logado = professores[i].id;
                return 1;
            }
        }
    } else if (nivel == ALUNO) {
        for (int i = 0; i < num_alunos; i++) {
            if (strcmp(login, alunos[i].login) == 0 && strcmp(senha, alunos[i].senha) == 0) {
                *id_usuario_logado = alunos[i].id;
                return 1;
            }
        }
    }

    printf("\n❌ Login ou senha incorretos. Tente novamente.\n");
    return 0;
}


// =================================================================
// --- 3. FUNÇÕES CRUD COMPLETO ---
// =================================================================

// --- CRUD ALUNO ---
void cadastrar_aluno() {
    printf("\n--- CADASTRO DE ALUNO ---\n");
    int novo_tamanho = num_alunos + 1;
    Aluno *novo_alunos = (Aluno *)realloc(alunos, novo_tamanho * sizeof(Aluno));

    if (novo_alunos == NULL) { printf("❌ Erro: Falha ao alocar memoria para novo aluno.\n"); return; }
    alunos = novo_alunos;
    Aluno *novo_aluno = &alunos[num_alunos];

    novo_aluno->id = obter_proximo_id("alunos.csv", sizeof(Aluno));

    printf("Nome: ");
    scanf(" %99[^\n]", novo_aluno->nome); 
    printf("Matricula: ");
    scanf(" %19s", novo_aluno->matricula);
    printf("CPF: ");
    scanf(" %14s", novo_aluno->cpf);
    printf("Login: ");
    scanf(" %49s", novo_aluno->login);
    printf("Senha: ");
    scanf(" %49s", novo_aluno->senha);

    limpa_buffer(); 

    num_alunos = novo_tamanho;
    
    if (salvar_dados_csv("alunos.csv", alunos, num_alunos, sizeof(Aluno), ALUNO)) {
        printf("\n✅ Aluno %s (ID: %d) cadastrado com sucesso e salvo.\n", novo_aluno->nome, novo_aluno->id);
    } else {
        printf("\n❌ Erro ao salvar aluno em arquivo.\n");
    }
}
void listar_alunos() {
    printf("\n--- LISTA DE ALUNOS (%d Registros) ---\n", num_alunos);
    if (num_alunos == 0) { printf("Nenhum aluno cadastrado.\n"); return; }
    printf("ID | Nome | Matrícula | CPF | Login\n");
    printf("---|---|---|---|---\n");
    for (int i = 0; i < num_alunos; i++) {
        printf("%d | %s | %s | %s | %s\n", alunos[i].id, alunos[i].nome, alunos[i].matricula, alunos[i].cpf, alunos[i].login);
    }
}
void editar_aluno() {
    int id_editar;
    printf("\n--- EDITAR ALUNO ---\n");
    listar_alunos();
    printf("Digite o ID do aluno a ser editado: ");
    scanf("%d", &id_editar);
    limpa_buffer();

    for (int i = 0; i < num_alunos; i++) {
        if (alunos[i].id == id_editar) {
            Aluno *a = &alunos[i];
            printf("Editando Aluno: %s\n", a->nome);
            printf("Novo Nome (%s): ", a->nome);
            scanf(" %99[^\n]", a->nome); 
            printf("Novo Login (%s): ", a->login);
            scanf(" %49s", a->login);
            printf("Nova Senha (deixe em branco para manter): ");
            char temp_senha[50] = "";
            scanf(" %49s", temp_senha);
            if (strlen(temp_senha) > 0) {
                strcpy(a->senha, temp_senha);
            }
            limpa_buffer();
            if (salvar_dados_csv("alunos.csv", alunos, num_alunos, sizeof(Aluno), ALUNO)) {
                printf("\n✅ Aluno %s (ID: %d) editado e salvo com sucesso.\n", a->nome, a->id);
            }
            return;
        }
    }
    printf("❌ Aluno com ID %d nao encontrado.\n", id_editar);
}
void excluir_aluno() {
    int id_excluir;
    printf("\n--- EXCLUIR ALUNO ---\n");
    listar_alunos();
    printf("Digite o ID do aluno a ser excluido: ");
    scanf("%d", &id_excluir);
    limpa_buffer();

    int indice_encontrado = -1;
    for (int i = 0; i < num_alunos; i++) {
        if (alunos[i].id == id_excluir) {
            indice_encontrado = i;
            break;
        }
    }
    if (indice_encontrado != -1) {
        // Desloca os registros
        for (int i = indice_encontrado; i < num_alunos - 1; i++) {
            alunos[i] = alunos[i+1];
        }
        num_alunos--;
        alunos = (Aluno *)realloc(alunos, num_alunos * sizeof(Aluno));
        
        if (salvar_dados_csv("alunos.csv", alunos, num_alunos, sizeof(Aluno), ALUNO)) {
             printf("\n✅ Aluno (ID: %d) excluido e salvo com sucesso.\n", id_excluir);
        } else {
            printf("\n❌ Erro ao salvar apos exclusao.\n");
        }
    } else {
        printf("❌ Aluno com ID %d nao encontrado.\n", id_excluir);
    }
}

// --- CRUD PROFESSOR ---
void cadastrar_professor() {
    printf("\n--- CADASTRO DE PROFESSOR ---\n");
    int novo_tamanho = num_professores + 1;
    Professor *novo_professores = (Professor *)realloc(professores, novo_tamanho * sizeof(Professor));

    if (novo_professores == NULL) { printf("❌ Erro: Falha ao alocar memoria.\n"); return; }
    professores = novo_professores;
    Professor *novo_professor = &professores[num_professores];

    novo_professor->id = obter_proximo_id("professores.csv", sizeof(Professor));
    
    printf("Nome: "); scanf(" %99[^\n]", novo_professor->nome); 
    printf("SIAPE: "); scanf(" %19s", novo_professor->siape);
    printf("CPF: "); scanf(" %14s", novo_professor->cpf);
    printf("Login: "); scanf(" %49s", novo_professor->login);
    printf("Senha: "); scanf(" %49s", novo_professor->senha);
    limpa_buffer();

    num_professores = novo_tamanho;
    if (salvar_dados_csv("professores.csv", professores, num_professores, sizeof(Professor), PROFESSOR)) {
        printf("\n✅ Professor %s (ID: %d) cadastrado e salvo.\n", novo_professor->nome, novo_professor->id);
    }
}
void listar_professores() {
    printf("\n--- LISTA DE PROFESSORES (%d Registros) ---\n", num_professores);
    if (num_professores == 0) { printf("Nenhum professor cadastrado.\n"); return; }
    printf("ID | Nome | SIAPE | Login\n");
    printf("---|---|---|---\n");
    for (int i = 0; i < num_professores; i++) {
        printf("%d | %s | %s | %s\n", professores[i].id, professores[i].nome, professores[i].siape, professores[i].login);
    }
}
void editar_professor() {
    int id_editar;
    printf("\n--- EDITAR PROFESSOR ---\n");
    listar_professores();
    printf("Digite o ID do professor a ser editado: ");
    scanf("%d", &id_editar);
    limpa_buffer();

    for (int i = 0; i < num_professores; i++) {
        if (professores[i].id == id_editar) {
            Professor *p = &professores[i];
            printf("Editando Professor: %s\n", p->nome);
            printf("Novo Nome (%s): ", p->nome);
            scanf(" %99[^\n]", p->nome); 
            printf("Novo Login (%s): ", p->login);
            scanf(" %49s", p->login);
            
            limpa_buffer();
            if (salvar_dados_csv("professores.csv", professores, num_professores, sizeof(Professor), PROFESSOR)) {
                printf("\n✅ Professor %s (ID: %d) editado e salvo com sucesso.\n", p->nome, p->id);
            }
            return;
        }
    }
    printf("❌ Professor com ID %d nao encontrado.\n", id_editar);
}
void excluir_professor() {
    int id_excluir;
    printf("\n--- EXCLUIR PROFESSOR ---\n");
    listar_professores();
    printf("Digite o ID do professor a ser excluido: ");
    scanf("%d", &id_excluir);
    limpa_buffer();

    int indice_encontrado = -1;
    for (int i = 0; i < num_professores; i++) {
        if (professores[i].id == id_excluir) {
            indice_encontrado = i;
            break;
        }
    }
    if (indice_encontrado != -1) {
        for (int i = indice_encontrado; i < num_professores - 1; i++) {
            professores[i] = professores[i+1];
        }
        num_professores--;
        professores = (Professor *)realloc(professores, num_professores * sizeof(Professor));
        
        if (salvar_dados_csv("professores.csv", professores, num_professores, sizeof(Professor), PROFESSOR)) {
             printf("\n✅ Professor (ID: %d) excluido e salvo com sucesso.\n", id_excluir);
        }
    } else {
        printf("❌ Professor com ID %d nao encontrado.\n", id_excluir);
    }
}

// --- CRUD TURMA ---
void cadastrar_turma() {
    printf("\n--- CADASTRO DE TURMA ---\n");
    if (num_professores == 0) { printf("❌ E necessario cadastrar professores primeiro.\n"); return; }
    
    int novo_tamanho = num_turmas + 1;
    Turma *novo_turmas = (Turma *)realloc(turmas, novo_tamanho * sizeof(Turma));

    if (novo_turmas == NULL) { printf("❌ Erro: Falha ao alocar memoria.\n"); return; }
    turmas = novo_turmas;
    Turma *nova_turma = &turmas[num_turmas];

    nova_turma->id = obter_proximo_id("turmas.csv", sizeof(Turma));
    
    printf("Nome da Turma (Ex: Eng. Software I): "); scanf(" %99[^\n]", nova_turma->nome); 
    printf("Codigo (Ex: ES101): "); scanf(" %19s", nova_turma->codigo);
    printf("Semestre (Ex: 2025.1): "); scanf(" %9s", nova_turma->semestre);
    
    listar_professores();
    printf("ID do Professor Responsável: "); 
    scanf("%d", &nova_turma->id_professor_responsavel);
    limpa_buffer();

    num_turmas = novo_tamanho;
    if (salvar_dados_csv("turmas.csv", turmas, num_turmas, sizeof(Turma), 0)) {
        printf("\n✅ Turma %s (ID: %d) cadastrada e salva.\n", nova_turma->nome, nova_turma->id);
    }
}
void listar_turmas() {
    printf("\n--- LISTA DE TURMAS (%d Registros) ---\n", num_turmas);
    if (num_turmas == 0) { printf("Nenhuma turma cadastrada.\n"); return; }
    printf("ID | Nome | Código | Semestre | Prof. Responsável\n");
    printf("---|---|---|---|---\n");
    for (int i = 0; i < num_turmas; i++) {
        // Encontrar nome do professor
        char nome_prof[100] = "Não Encontrado";
        for(int j=0; j < num_professores; j++){
            if(professores[j].id == turmas[i].id_professor_responsavel){
                strcpy(nome_prof, professores[j].nome);
                break;
            }
        }
        printf("%d | %s | %s | %s | %s\n", turmas[i].id, turmas[i].nome, turmas[i].codigo, turmas[i].semestre, nome_prof);
    }
}
void editar_turma() {
    int id_editar;
    printf("\n--- EDITAR TURMA ---\n");
    listar_turmas();
    printf("Digite o ID da turma a ser editada: ");
    scanf("%d", &id_editar);
    limpa_buffer();

    for (int i = 0; i < num_turmas; i++) {
        if (turmas[i].id == id_editar) {
            Turma *t = &turmas[i];
            printf("Editando Turma: %s\n", t->nome);
            printf("Novo Nome (%s): ", t->nome);
            scanf(" %99[^\n]", t->nome); 
            printf("Novo Semestre (%s): ", t->semestre);
            scanf(" %9s", t->semestre);
            
            limpa_buffer();
            if (salvar_dados_csv("turmas.csv", turmas, num_turmas, sizeof(Turma), 0)) {
                printf("\n✅ Turma %s (ID: %d) editada e salva com sucesso.\n", t->nome, t->id);
            }
            return;
        }
    }
    printf("❌ Turma com ID %d nao encontrada.\n", id_editar);
}
void excluir_turma() {
    int id_excluir;
    printf("\n--- EXCLUIR TURMA ---\n");
    listar_turmas();
    printf("Digite o ID da turma a ser excluida: ");
    scanf("%d", &id_excluir);
    limpa_buffer();

    int indice_encontrado = -1;
    for (int i = 0; i < num_turmas; i++) {
        if (turmas[i].id == id_excluir) {
            indice_encontrado = i;
            break;
        }
    }
    if (indice_encontrado != -1) {
        for (int i = indice_encontrado; i < num_turmas - 1; i++) {
            turmas[i] = turmas[i+1];
        }
        num_turmas--;
        turmas = (Turma *)realloc(turmas, num_turmas * sizeof(Turma));
        
        if (salvar_dados_csv("turmas.csv", turmas, num_turmas, sizeof(Turma), 0)) {
             printf("\n✅ Turma (ID: %d) excluida e salva com sucesso.\n", id_excluir);
        }
    } else {
        printf("❌ Turma com ID %d nao encontrada.\n", id_excluir);
    }
}

// --- CRUD ATIVIDADE (Feito pelo Professor) ---

void cadastrar_atividade(int id_professor) {
    printf("\n--- CADASTRO DE ATIVIDADE ---\n");
    
    // Lista turmas do professor
    printf("Turmas sob sua responsabilidade:\n");
    int turmas_prof_encontradas = 0;
    for (int i = 0; i < num_turmas; i++) {
        if (turmas[i].id_professor_responsavel == id_professor) {
            printf("ID: %d - %s (%s)\n", turmas[i].id, turmas[i].nome, turmas[i].codigo);
            turmas_prof_encontradas = 1;
        }
    }

    if(turmas_prof_encontradas == 0) { printf("❌ Voce nao é responsavel por nenhuma turma.\n"); return; }
    
    int novo_tamanho = num_atividades + 1;
    Atividade *novo_atividades = (Atividade *)realloc(atividades, novo_tamanho * sizeof(Atividade));
    if (novo_atividades == NULL) { printf("❌ Erro: Falha ao alocar memoria.\n"); return; }
    atividades = novo_atividades;
    Atividade *nova_atividade = &atividades[num_atividades];

    nova_atividade->id = obter_proximo_id("atividades.csv", sizeof(Atividade));
    
    printf("Digite o ID da Turma para a Atividade: "); scanf("%d", &nova_atividade->id_turma);
    printf("Descricao: "); scanf(" %149[^\n]", nova_atividade->descricao); 
    printf("Peso (ex: 0.40): "); scanf("%f", &nova_atividade->peso);
    printf("Data de Entrega (YYYY-MM-DD): "); scanf(" %10s", nova_atividade->data_entrega);

    limpa_buffer();

    num_atividades = novo_tamanho;
    if (salvar_dados_csv("atividades.csv", atividades, num_atividades, sizeof(Atividade), 0)) {
        printf("\n✅ Atividade %s (ID: %d) cadastrada e salva.\n", nova_atividade->descricao, nova_atividade->id);
    }
}
void listar_atividades() {
    printf("\n--- LISTA DE ATIVIDADES (%d Registros) ---\n", num_atividades);
    if (num_atividades == 0) { printf("Nenhuma atividade cadastrada.\n"); return; }
    printf("ID | Turma ID | Descrição | Peso | Entrega\n");
    printf("---|---|---|---|---\n");
    for (int i = 0; i < num_atividades; i++) {
        printf("%d | %d | %s | %.2f | %s\n", atividades[i].id, atividades[i].id_turma, atividades[i].descricao, atividades[i].peso, atividades[i].data_entrega);
    }
}
void listar_atividades_turma(int id_turma) {
    printf("\n--- ATIVIDADES DA TURMA ID %d ---\n", id_turma);
    int encontradas = 0;
    for (int i = 0; i < num_atividades; i++) {
        if (atividades[i].id_turma == id_turma) {
             printf("ID: %d | Descricao: %s | Peso: %.2f | Entrega: %s\n", atividades[i].id, atividades[i].descricao, atividades[i].peso, atividades[i].data_entrega);
             encontradas++;
        }
    }
    if (encontradas == 0) {
        printf("Nenhuma atividade encontrada para esta turma.\n");
    }
}
void editar_atividade() {
    printf("\n⚠️ Funcionalidade Editar Atividade: Nao implementada.\n");
}
void excluir_atividade() {
    printf("\n⚠️ Funcionalidade Excluir Atividade: Nao implementada.\n");
}


// =================================================================
// --- 4. FUNÇÕES DE LÓGICA DE NEGÓCIO (Matrícula e Notas) ---
// =================================================================

void matricular_aluno_turma() {
    printf("\n--- MATRICULAR ALUNO EM TURMA ---\n");
    if (num_alunos == 0 || num_turmas == 0) {
        printf("❌ E necessario ter alunos e turmas cadastradas.\n");
        return;
    }
    listar_alunos();
    listar_turmas();

    int id_aluno, id_turma;
    printf("Digite o ID do Aluno: "); 
    scanf("%d", &id_aluno);
    printf("Digite o ID da Turma: "); 
    scanf("%d", &id_turma);
    limpa_buffer();
    
    // 1. Verificar se a matrícula já existe
    for(int i=0; i<num_matriculas; i++) {
        if (matriculas[i].id_aluno == id_aluno && matriculas[i].id_turma == id_turma) {
            printf("❌ Aluno ja matriculado nesta turma.\n");
            return;
        }
    }

    // 2. Realocar e adicionar a nova matrícula
    int novo_tamanho = num_matriculas + 1;
    Matricula *novo_matriculas = (Matricula *)realloc(matriculas, novo_tamanho * sizeof(Matricula));
    if (novo_matriculas == NULL) { printf("❌ Erro: Falha ao alocar memoria.\n"); return; }
    matriculas = novo_matriculas;
    
    matriculas[num_matriculas].id_aluno = id_aluno;
    matriculas[num_matriculas].id_turma = id_turma;
    num_matriculas = novo_tamanho;

    if (salvar_dados_csv("matriculas.csv", matriculas, num_matriculas, sizeof(Matricula), 0)) {
        printf("\n✅ Aluno %d matriculado na Turma %d com sucesso e salvo.\n", id_aluno, id_turma);
    }
}

void lancar_nota(int id_professor) {
    printf("\n--- LANÇAMENTO DE NOTAS ---\n");

    // 1. Listar Turmas do Professor
    printf("Suas Turmas:\n");
    int count_turmas = 0;
    for (int i = 0; i < num_turmas; i++) {
        if (turmas[i].id_professor_responsavel == id_professor) {
            printf("ID: %d - %s (%s)\n", turmas[i].id, turmas[i].nome, turmas[i].codigo);
            count_turmas++;
        }
    }

    if (count_turmas == 0) { printf("❌ Voce nao é responsavel por nenhuma turma.\n"); return; }

    int id_turma_selecionada;
    printf("Digite o ID da Turma: "); 
    if (scanf("%d", &id_turma_selecionada) != 1) { limpa_buffer(); printf("Entrada invalida.\n"); return; }
    limpa_buffer();

    // 2. Listar Atividades da Turma
    listar_atividades_turma(id_turma_selecionada);
    int id_atividade_selecionada;
    printf("Digite o ID da Atividade: "); 
    if (scanf("%d", &id_atividade_selecionada) != 1) { limpa_buffer(); printf("Entrada invalida.\n"); return; }
    limpa_buffer();

    // 3. Listar Alunos Matriculados na Turma
    printf("\nAlunos matriculados na Turma %d:\n", id_turma_selecionada);
    int count_alunos = 0;
    for (int i = 0; i < num_matriculas; i++) {
        if (matriculas[i].id_turma == id_turma_selecionada) {
            for (int j = 0; j < num_alunos; j++) {
                if (alunos[j].id == matriculas[i].id_aluno) {
                    printf("ID: %d - %s\n", alunos[j].id, alunos[j].nome);
                    count_alunos++;
                    break;
                }
            }
        }
    }
    if(count_alunos == 0) { printf("❌ Nao ha alunos matriculados nesta turma.\n"); return; }

    // 4. Lançar Nota
    int id_aluno_selecionado;
    float nova_nota;

    printf("Digite o ID do Aluno para lançar a nota: "); 
    if (scanf("%d", &id_aluno_selecionado) != 1) { limpa_buffer(); printf("Entrada invalida.\n"); return; }
    printf("Digite a Nota (0.0 a 10.0): "); 
    if (scanf("%f", &nova_nota) != 1) { limpa_buffer(); printf("Entrada invalida.\n"); return; }
    limpa_buffer();
    
    if (nova_nota < 0.0 || nova_nota > 10.0) {
        printf("❌ Nota invalida. Deve ser entre 0.0 e 10.0.\n");
        return;
    }

    // 5. Adicionar/Atualizar no array de Notas
    int nota_existente = 0;
    for (int i = 0; i < num_notas; i++) {
        if (notas[i].id_atividade == id_atividade_selecionada && notas[i].id_aluno == id_aluno_selecionado) {
            notas[i].nota = nova_nota;
            nota_existente = 1;
            break;
        }
    }

    if (!nota_existente) {
        int novo_tamanho = num_notas + 1;
        Nota *novo_notas = (Nota *)realloc(notas, novo_tamanho * sizeof(Nota));
        if (novo_notas == NULL) { printf("❌ Erro ao alocar memoria para nota.\n"); return; }
        notas = novo_notas;

        notas[num_notas].id_atividade = id_atividade_selecionada;
        notas[num_notas].id_aluno = id_aluno_selecionado;
        notas[num_notas].nota = nova_nota;
        num_notas = novo_tamanho;
    }

    if (salvar_dados_csv("notas.csv", notas, num_notas, sizeof(Nota), 0)) {
        printf("\n✅ Nota %.2f lançada/atualizada para o Aluno %d na Atividade %d e salva.\n", nova_nota, id_aluno_selecionado, id_atividade_selecionada);
    }
}


// =================================================================
// --- 5. FUNÇÕES DO ALUNO ---
// =================================================================

void visualizar_matriculas_aluno(int id_aluno) {
    printf("\n--- MINHAS TURMAS CADASTRADAS ---\n");
    int count = 0;
    
    printf("ID da Turma | Codigo | Nome da Turma | Professor\n");
    printf("---|---|---|---\n");

    for (int i = 0; i < num_matriculas; i++) {
        if (matriculas[i].id_aluno == id_aluno) {
            
            // 1. Encontrar a Turma
            Turma *t = NULL;
            for (int j = 0; j < num_turmas; j++) {
                if (turmas[j].id == matriculas[i].id_turma) {
                    t = &turmas[j];
                    break;
                }
            }

            if (t != NULL) {
                // 2. Encontrar o Professor
                char nome_prof[100] = "Não Informado";
                for(int k=0; k < num_professores; k++){
                    if(professores[k].id == t->id_professor_responsavel){
                        strcpy(nome_prof, professores[k].nome);
                        break;
                    }
                }
                
                printf("%d | %s | %s | %s\n", t->id, t->codigo, t->nome, nome_prof);
                count++;
            }
        }
    }

    if (count == 0) {
        printf("Nenhuma matricula encontrada para o seu ID.\n");
    }
}

void visualizar_notas_aluno(int id_aluno) {
    printf("\n--- MINHAS NOTAS E DESEMPENHO ---\n");
    int count_turmas = 0;

    for (int i = 0; i < num_matriculas; i++) {
        if (matriculas[i].id_aluno == id_aluno) {
            int id_turma = matriculas[i].id_turma;
            
            // Encontrar o nome da Turma
            char nome_turma[100] = "Turma Desconhecida";
            for (int j = 0; j < num_turmas; j++) {
                if (turmas[j].id == id_turma) {
                    strcpy(nome_turma, turmas[j].nome);
                    break;
                }
            }
            
            printf("\n-- TURMA: %s (ID %d) --\n", nome_turma, id_turma);
            printf("Atividade ID | Descricao | Peso | Minha Nota\n");
            printf("---|---|---|---\n");
            
            float soma_ponderada = 0.0;
            float soma_pesos = 0.0;
            int atividades_encontradas = 0;

            // 1. Listar Atividades da Turma
            for (int j = 0; j < num_atividades; j++) {
                if (atividades[j].id_turma == id_turma) {
                    int id_atividade = atividades[j].id;
                    float nota_aluno = 0.0;
                    int nota_lancada = 0;

                    // 2. Procurar a Nota para esta Atividade/Aluno
                    for (int k = 0; k < num_notas; k++) {
                        if (notas[k].id_atividade == id_atividade && notas[k].id_aluno == id_aluno) {
                            nota_aluno = notas[k].nota;
                            nota_lancada = 1;
                            break;
                        }
                    }

                    printf("%d | %s | %.2f | ", id_atividade, atividades[j].descricao, atividades[j].peso);
                    
                    if (nota_lancada) {
                        printf("%.2f\n", nota_aluno);
                        soma_ponderada += (nota_aluno * atividades[j].peso);
                        soma_pesos += atividades[j].peso;
                    } else {
                        printf("Aguardando Lançamento\n");
                    }
                    atividades_encontradas++;
                }
            }
            
            if (atividades_encontradas == 0) {
                 printf("Nenhuma atividade cadastrada para esta turma.\n");
            } else if (soma_pesos > 0) {
                printf("--------------------------------\n");
                printf(">>> MEDIA PONDERADA PARCIAL: %.2f (Baseada em %.2f de Peso)\n", soma_ponderada / soma_pesos, soma_pesos);
            }
            count_turmas++;
        }
    }
    
    if (count_turmas == 0) {
        printf("Voce nao esta matriculado em nenhuma turma.\n");
    }
}


// =================================================================
// --- 6. FUNÇÕES DE MENU (Submenus e Navegação) ---
// =================================================================

void submenu_crud_aluno() {
    int op;
    do {
        printf("\n--- SUBMENU ALUNOS ---\n");
        printf("1. Cadastrar Aluno\n");
        printf("2. Listar Alunos\n");
        printf("3. Editar Aluno\n");
        printf("4. Excluir Aluno\n"); 
        printf("0. Voltar\n");
        printf("Escolha uma opcao: ");
        if (scanf("%d", &op) != 1) { limpa_buffer(); op = -1; }
        limpa_buffer();
        
        switch (op) {
            case 1: cadastrar_aluno(); break;
            case 2: listar_alunos(); break;
            case 3: editar_aluno(); break;
            case 4: excluir_aluno(); break;
            case 0: break;
            default: printf("Opcao invalida.\n");
        }
    } while (op != 0);
}
void submenu_crud_professor() {
    int op;
    do {
        printf("\n--- SUBMENU PROFESSORES ---\n");
        printf("1. Cadastrar Professor\n");
        printf("2. Listar Professores\n");
        printf("3. Editar Professor\n");
        printf("4. Excluir Professor\n"); 
        printf("0. Voltar\n");
        printf("Escolha uma opcao: ");
        if (scanf("%d", &op) != 1) { limpa_buffer(); op = -1; }
        limpa_buffer();

        switch (op) {
            case 1: cadastrar_professor(); break;
            case 2: listar_professores(); break;
            case 3: editar_professor(); break;
            case 4: excluir_professor(); break;
            case 0: break;
            default: printf("Opcao invalida.\n");
        }
    } while (op != 0);
}
void submenu_crud_turma() {
     int op;
    do {
        printf("\n--- SUBMENU TURMAS ---\n");
        printf("1. Cadastrar Turma\n");
        printf("2. Listar Turmas\n");
        printf("3. Editar Turma\n");
        printf("4. Excluir Turma\n"); 
        printf("5. Matricular Aluno em Turma\n");
        printf("0. Voltar\n");
        printf("Escolha uma opcao: ");
        if (scanf("%d", &op) != 1) { limpa_buffer(); op = -1; }
        limpa_buffer();

        switch (op) {
            case 1: cadastrar_turma(); break;
            case 2: listar_turmas(); break;
            case 3: editar_turma(); break;
            case 4: excluir_turma(); break;
            case 5: matricular_aluno_turma(); break;
            case 0: break;
            default: printf("Opcao invalida.\n");
        }
    } while (op != 0);
}


void menu_admin(int id_admin) {
    int opcao;
    Usuario *adm = &admin_master;
    printf("\n>>> BEM-VINDO, ADMIN %s <<<\n", adm->nome);
    
    do {
        printf("\n--- MENU ADMINISTRADOR ---\n");
        printf("1. Gerenciar Alunos (CRUD)\n");
        printf("2. Gerenciar Professores (CRUD)\n");
        printf("3. Gerenciar Turmas (CRUD/Matriculas)\n");
        printf("4. Listar Todas as Atividades\n");
        printf("0. Sair e Fazer Logout\n");
        printf("Escolha uma opcao: ");
        
        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        switch (opcao) {
            case 1: submenu_crud_aluno(); break;
            case 2: submenu_crud_professor(); break;
            case 3: submenu_crud_turma(); break;
            case 4: listar_atividades(); break;
            case 0: printf("Fazendo logout...\n"); break;
            default: printf("Opcao invalida. Tente novamente.\n");
        }
    } while (opcao != 0);
}

void menu_professor(int id_professor) {
    char nome_prof[100] = "Professor Desconhecido";
    for(int i=0; i < num_professores; i++){
        if(professores[i].id == id_professor){
            strcpy(nome_prof, professores[i].nome);
            break;
        }
    }

    int opcao;
    printf("\n>>> BEM-VINDO, PROFESSOR %s <<<\n", nome_prof);
    do {
        printf("\n--- MENU PROFESSOR ---\n");
        printf("1. Listar Minhas Turmas\n");
        printf("2. Lançar Notas\n");
        printf("3. Criar Nova Atividade\n");
        printf("0. Sair e Fazer Logout\n");
        printf("Escolha uma opcao: ");
        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        switch (opcao) {
            case 1: listar_turmas(); break;
            case 2: lancar_nota(id_professor); break;
            case 3: cadastrar_atividade(id_professor); break;
            case 0: printf("Fazendo logout...\n"); break;
            default: printf("Opcao invalida.\n");
        }
    } while (opcao != 0);
}

void menu_aluno(int id_aluno) {
    char nome_aluno[100] = "Aluno Desconhecido";
     for(int i=0; i < num_alunos; i++){
        if(alunos[i].id == id_aluno){
            strcpy(nome_aluno, alunos[i].nome);
            break;
        }
    }
    
    int opcao;
    printf("\n>>> BEM-VINDO, ALUNO %s <<<\n", nome_aluno);
    do {
        printf("\n--- MENU ALUNO ---\n");
        printf("1. Visualizar Minhas Matrículas/Turmas\n");
        printf("2. Visualizar Minhas Notas e Desempenho\n");
        printf("0. Sair e Fazer Logout\n");
        printf("Escolha uma opcao: ");
        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        switch (opcao) {
            case 1: visualizar_matriculas_aluno(id_aluno); break; 
            case 2: visualizar_notas_aluno(id_aluno); break;      
            case 0: printf("Fazendo logout...\n"); break;
            default: printf("Opcao invalida.\n");
        }
    } while (opcao != 0);

}
