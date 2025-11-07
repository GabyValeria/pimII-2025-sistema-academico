#include "estruturas.h" 

// =================================================================
// --- 1. FUNÇÕES AUXILIARES DE BUSCA E CALLBACK ---
// =================================================================

// Funções de Callback para obter o ID
int obter_id_aluno(const void *registro) {
    return ((const Aluno *)registro)->id;
}

int obter_id_professor(const void *registro) {
    return ((const Professor *)registro)->id;
}

int obter_id_turma(const void *registro) {
    return ((const Turma *)registro)->id;
}

int obter_id_atividade(const void *registro) {
    return ((const Atividade *)registro)->id;
}

// Funções de Busca
Aluno *buscar_aluno_por_id(int id_aluno) {
    for (int i = 0; i < num_alunos; i++) {
        if (alunos[i].id == id_aluno) {
            return &alunos[i];
        }
    }
    return NULL;
}

Professor *buscar_professor_por_id(int id_prof) {
    for (int i = 0; i < num_professores; i++) {
        if (professores[i].id == id_prof) {
            return &professores[i];
        }
    }
    return NULL;
}

Turma *buscar_turma_por_id(int id_turma) {
    for (int i = 0; i < num_turmas; i++) {
        if (turmas[i].id == id_turma) {
            return &turmas[i];
        }
    }
    return NULL;
}

char *buscar_nome_professor_por_id(int id_prof) {
    Professor *p = buscar_professor_por_id(id_prof);
    return p ? p->nome : "Professor Desconhecido";
}

// =================================================================
// --- 2. FUNÇÕES AUXILIARES DE MEMÓRIA (GENÉRICAS) ---
// =================================================================

void *alocar_novo_registro_generico(void **registros, int *num_registros, size_t tamanho_struct) {
    (*num_registros)++;
    *registros = realloc(*registros, (*num_registros) * tamanho_struct);
    if (*registros == NULL) {
        printf("❌ Erro de alocacao de memoria.\n");
        (*num_registros)--;
        exit(EXIT_FAILURE);
    }
    // Retorna o endereço do novo registro adicionado
    return (char *)*registros + ((*num_registros) - 1) * tamanho_struct;
}

int excluir_registro_generico(void **registros, int *num_registros, size_t tamanho_struct, int id_excluir, int (*obter_id)(const void *)) {
    int indice_excluir = -1;

    // 1. Encontrar o índice
    for (int i = 0; i < *num_registros; i++) {
        void *registro_atual = (char *)*registros + i * tamanho_struct;
        if (obter_id(registro_atual) == id_excluir) {
            indice_excluir = i;
            break;
        }
    }

    if (indice_excluir == -1) {
        return 0; // Registro não encontrado
    }

    // 2. Mover os elementos posteriores para trás
    if (indice_excluir < (*num_registros) - 1) {
        size_t bytes_mover = ((*num_registros) - 1 - indice_excluir) * tamanho_struct;
        void *destino = (char *)*registros + indice_excluir * tamanho_struct;
        void *origem = (char *)*registros + (indice_excluir + 1) * tamanho_struct;
        memmove(destino, origem, bytes_mover);
    }

    // 3. Reduzir o contador e realocar a memória
    (*num_registros)--;
    *registros = realloc(*registros, (*num_registros) * tamanho_struct);
    
    return 1; // Sucesso
}


// =================================================================
// --- 3. FUNÇÕES CRUD: ALUNOS ---
// =================================================================

void cadastrar_aluno() {
    Aluno *novo_aluno = (Aluno *)alocar_novo_registro_generico((void **)&alunos, &num_alunos, sizeof(Aluno));
    
    novo_aluno->id = obter_proximo_id("alunos.csv", sizeof(Aluno));

    printf("\n--- CADASTRO DE ALUNO ---\n");
    printf("Nome: "); scanf(" %99[^\n]", novo_aluno->nome); limpa_buffer();
    printf("Matricula: "); scanf(" %19s", novo_aluno->matricula); limpa_buffer();
    printf("CPF: "); scanf(" %14s", novo_aluno->cpf); limpa_buffer();
    printf("Login: "); scanf(" %49s", novo_aluno->login); limpa_buffer();
    printf("Senha: "); scanf(" %49s", novo_aluno->senha); limpa_buffer();
    
    // CRIPTOGRAFIA: Criptografa a senha antes de salvar no array
    criptografar_string(novo_aluno->senha);

    if (salvar_dados_csv("alunos.csv", alunos, num_alunos, sizeof(Aluno), ACESSO_ALUNO)) {
        printf("✅ Aluno %s cadastrado com sucesso (ID: %d).\n", novo_aluno->nome, novo_aluno->id);
    } else {
        printf("❌ Erro ao salvar dados do aluno.\n");
    }
}

void listar_alunos() {
    if (num_alunos == 0) {
        printf("Nenhum aluno cadastrado.\n");
        return;
    }
    printf("\n--- LISTA DE ALUNOS (%d) ---\n", num_alunos);
    printf("ID | Nome | Matricula | CPF | Login\n");
    printf("---|---|---|---|---\n");
    for (int i = 0; i < num_alunos; i++) {
        printf("%d | %s | %s | %s | %s\n", 
            alunos[i].id, alunos[i].nome, alunos[i].matricula, alunos[i].cpf, alunos[i].login);
    }
}

void editar_aluno() {
    int id_aluno;
    printf("Digite o ID do aluno para editar: ");
    if (scanf("%d", &id_aluno) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    Aluno *a = buscar_aluno_por_id(id_aluno);
    if (!a) {
        printf("❌ Aluno com ID %d nao encontrado.\n", id_aluno);
        return;
    }

    printf("\n--- EDITANDO ALUNO ID: %d (%s) ---\n", a->id, a->nome);

    printf("Novo Nome (Atual: %s): ", a->nome); 
    scanf(" %99[^\n]", a->nome); limpa_buffer();

    printf("Novo CPF (Atual: %s): ", a->cpf); 
    scanf(" %14s", a->cpf); limpa_buffer();

    printf("Novo Login (Atual: %s): ", a->login); 
    scanf(" %49s", a->login); limpa_buffer();

    printf("Nova Senha (Deixe em branco para manter): ");
    char nova_senha_input[MAX_SENHA] = "";
    scanf(" %49[^\n]", nova_senha_input); limpa_buffer();
    
    if (strlen(nova_senha_input) > 0) {
        // CRIPTOGRAFIA: Criptografa a nova senha antes de salvar
        criptografar_string(nova_senha_input); 
        strcpy(a->senha, nova_senha_input);
        printf("Senha alterada.\n");
    }

    if (salvar_dados_csv("alunos.csv", alunos, num_alunos, sizeof(Aluno), ACESSO_ALUNO)) {
        printf("✅ Aluno %d editado com sucesso.\n", a->id);
    } else {
        printf("❌ Erro ao salvar edicao do aluno.\n");
    }
}

void excluir_aluno() {
    int id_aluno;
    printf("Digite o ID do aluno para excluir: ");
    if (scanf("%d", &id_aluno) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    if (excluir_registro_generico((void **)&alunos, &num_alunos, sizeof(Aluno), id_aluno, obter_id_aluno)) {
        printf("✅ Aluno ID %d excluido com sucesso.\n", id_aluno);
        salvar_dados_csv("alunos.csv", alunos, num_alunos, sizeof(Aluno), ACESSO_ALUNO);
    } else {
        printf("❌ Aluno com ID %d nao encontrado.\n", id_aluno);
    }
}


// =================================================================
// --- 4. FUNÇÕES CRUD: PROFESSORES ---
// =================================================================

void cadastrar_professor() {
    Professor *novo_prof = (Professor *)alocar_novo_registro_generico((void **)&professores, &num_professores, sizeof(Professor));
    
    novo_prof->id = obter_proximo_id("professores.csv", sizeof(Professor));

    printf("\n--- CADASTRO DE PROFESSOR ---\n");
    printf("Nome: "); scanf(" %99[^\n]", novo_prof->nome); limpa_buffer();
    printf("SIAPE: "); scanf(" %19s", novo_prof->siape); limpa_buffer();
    printf("CPF: "); scanf(" %14s", novo_prof->cpf); limpa_buffer();
    printf("Login: "); scanf(" %49s", novo_prof->login); limpa_buffer();
    printf("Senha: "); scanf(" %49s", novo_prof->senha); limpa_buffer();
    
    // CRIPTOGRAFIA: Criptografa a senha antes de salvar no array
    criptografar_string(novo_prof->senha);

    if (salvar_dados_csv("professores.csv", professores, num_professores, sizeof(Professor), ACESSO_PROFESSOR)) {
        printf("✅ Professor %s cadastrado com sucesso (ID: %d).\n", novo_prof->nome, novo_prof->id);
    } else {
        printf("❌ Erro ao salvar dados do professor.\n");
    }
}

void listar_professores() {
    if (num_professores == 0) {
        printf("Nenhum professor cadastrado.\n");
        return;
    }
    printf("\n--- LISTA DE PROFESSORES (%d) ---\n", num_professores);
    printf("ID | Nome | SIAPE | CPF | Login\n");
    printf("---|---|---|---|---\n");
    for (int i = 0; i < num_professores; i++) {
        printf("%d | %s | %s | %s | %s\n", 
            professores[i].id, professores[i].nome, professores[i].siape, professores[i].cpf, professores[i].login);
    }
}

void editar_professor() {
    int id_prof;
    printf("Digite o ID do professor para editar: ");
    if (scanf("%d", &id_prof) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    Professor *p = buscar_professor_por_id(id_prof);
    if (!p) {
        printf("❌ Professor com ID %d nao encontrado.\n", id_prof);
        return;
    }

    printf("\n--- EDITANDO PROFESSOR ID: %d (%s) ---\n", p->id, p->nome);

    printf("Novo Nome (Atual: %s): ", p->nome); 
    scanf(" %99[^\n]", p->nome); limpa_buffer();

    printf("Novo SIAPE (Atual: %s): ", p->siape); 
    scanf(" %19s", p->siape); limpa_buffer();

    printf("Novo Login (Atual: %s): ", p->login); 
    scanf(" %49s", p->login); limpa_buffer();

    printf("Nova Senha (Deixe em branco para manter): ");
    char nova_senha_input[MAX_SENHA] = "";
    scanf(" %49[^\n]", nova_senha_input); limpa_buffer();
    
    if (strlen(nova_senha_input) > 0) {
        // CRIPTOGRAFIA: Criptografa a nova senha antes de salvar
        criptografar_string(nova_senha_input); 
        strcpy(p->senha, nova_senha_input);
        printf("Senha alterada.\n");
    }

    if (salvar_dados_csv("professores.csv", professores, num_professores, sizeof(Professor), ACESSO_PROFESSOR)) {
        printf("✅ Professor %d editado com sucesso.\n", p->id);
    } else {
        printf("❌ Erro ao salvar edicao do professor.\n");
    }
}

void excluir_professor() {
    int id_prof;
    printf("Digite o ID do professor para excluir: ");
    if (scanf("%d", &id_prof) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    if (excluir_registro_generico((void **)&professores, &num_professores, sizeof(Professor), id_prof, obter_id_professor)) {
        printf("✅ Professor ID %d excluido com sucesso.\n", id_prof);
        salvar_dados_csv("professores.csv", professores, num_professores, sizeof(Professor), ACESSO_PROFESSOR);
    } else {
        printf("❌ Professor com ID %d nao encontrado.\n", id_prof);
    }
}


// =================================================================
// --- 5. FUNÇÕES CRUD: TURMAS ---
// =================================================================

void cadastrar_turma() {
    Turma *nova_turma = (Turma *)alocar_novo_registro_generico((void **)&turmas, &num_turmas, sizeof(Turma));
    
    nova_turma->id = obter_proximo_id("turmas.csv", sizeof(Turma));

    printf("\n--- CADASTRO DE TURMA ---\n");
    printf("Nome da Disciplina: "); scanf(" %99[^\n]", nova_turma->nome); limpa_buffer();
    printf("Codigo (Ex: COMP301): "); scanf(" %19s", nova_turma->codigo); limpa_buffer();
    printf("Semestre (Ex: 2023.2): "); scanf(" %9s", nova_turma->semestre); limpa_buffer();
    
    listar_professores();
    printf("ID do Professor Responsavel: ");
    if (scanf("%d", &nova_turma->id_professor_responsavel) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    if (!buscar_professor_por_id(nova_turma->id_professor_responsavel)) {
        printf("❌ ID do professor nao encontrado. Turma nao cadastrada.\n");
        num_turmas--; 
        return;
    }

    if (salvar_dados_csv("turmas.csv", turmas, num_turmas, sizeof(Turma), ACESSO_ADMIN)) {
        printf("✅ Turma %s (%s) cadastrada com sucesso (ID: %d).\n", nova_turma->nome, nova_turma->codigo, nova_turma->id);
    } else {
        printf("❌ Erro ao salvar dados da turma.\n");
    }
}

void listar_turmas() {
    if (num_turmas == 0) {
        printf("Nenhuma turma cadastrada.\n");
        return;
    }
    printf("\n--- LISTA DE TURMAS (%d) ---\n", num_turmas);
    printf("ID | Codigo | Nome | Semestre | Professor\n");
    printf("---|---|---|---|---\n");
    for (int i = 0; i < num_turmas; i++) {
        printf("%d | %s | %s | %s | %s\n", 
            turmas[i].id, turmas[i].codigo, turmas[i].nome, turmas[i].semestre, 
            buscar_nome_professor_por_id(turmas[i].id_professor_responsavel));
    }
}

void editar_turma() {
    int id_turma;
    printf("Digite o ID da turma para editar: ");
    if (scanf("%d", &id_turma) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    Turma *t = buscar_turma_por_id(id_turma);
    if (!t) {
        printf("❌ Turma com ID %d nao encontrada.\n", id_turma);
        return;
    }

    printf("\n--- EDITANDO TURMA ID: %d (%s) ---\n", t->id, t->nome);

    printf("Novo Nome (Atual: %s): ", t->nome); 
    scanf(" %99[^\n]", t->nome); limpa_buffer();

    printf("Novo Codigo (Atual: %s): ", t->codigo); 
    scanf(" %19s", t->codigo); limpa_buffer();

    printf("Novo Semestre (Atual: %s): ", t->semestre); 
    scanf(" %9s", t->semestre); limpa_buffer();

    listar_professores();
    printf("Novo ID do Professor (Atual: %d): ", t->id_professor_responsavel);
    int novo_id_prof;
    if (scanf("%d", &novo_id_prof) == 1 && buscar_professor_por_id(novo_id_prof)) {
        t->id_professor_responsavel = novo_id_prof;
    } else {
        printf("ID de professor invalido ou nao encontrado. Mantendo o professor atual.\n");
    }
    limpa_buffer();

    if (salvar_dados_csv("turmas.csv", turmas, num_turmas, sizeof(Turma), ACESSO_ADMIN)) {
        printf("✅ Turma %d editada com sucesso.\n", t->id);
    } else {
        printf("❌ Erro ao salvar edicao da turma.\n");
    }
}

void excluir_turma() {
    int id_turma;
    printf("Digite o ID da turma para excluir: ");
    if (scanf("%d", &id_turma) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    if (excluir_registro_generico((void **)&turmas, &num_turmas, sizeof(Turma), id_turma, obter_id_turma)) {
        printf("✅ Turma ID %d excluida com sucesso.\n", id_turma);
        salvar_dados_csv("turmas.csv", turmas, num_turmas, sizeof(Turma), ACESSO_ADMIN);
    } else {
        printf("❌ Turma com ID %d nao encontrada.\n", id_turma);
    }
}


// =================================================================
// --- 6. FUNÇÕES CRUD: ATIVIDADES ---
// =================================================================

void listar_atividades_turma(int id_turma) {
    int count = 0;
    Turma *t = buscar_turma_por_id(id_turma);
    if (!t) return;

    printf("\n--- ATIVIDADES DA TURMA: %s (%s) ---\n", t->nome, t->codigo);
    printf("ID | Descricao | Peso (%%) | Data Entrega\n");
    printf("---|---|---|---\n");
    
    for (int i = 0; i < num_atividades; i++) {
        if (atividades[i].id_turma == id_turma) {
            printf("%d | %s | %.0f%% | %s\n", 
                atividades[i].id, atividades[i].descricao, atividades[i].peso * 100, atividades[i].data_entrega);
            count++;
        }
    }
    if (count == 0) {
        printf("Nenhuma atividade cadastrada para esta turma.\n");
    }
}

void cadastrar_atividade(int id_professor) {
    int id_turma;
    printf("\n--- CADASTRO DE ATIVIDADE ---\n");
    listar_turmas();
    printf("ID da Turma: ");
    if (scanf("%d", &id_turma) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();
    
    Turma *t = buscar_turma_por_id(id_turma);
    if (!t || t->id_professor_responsavel != id_professor) {
        printf("❌ Turma nao encontrada ou voce nao e o professor responsavel.\n");
        return;
    }

    Atividade *nova_ativ = (Atividade *)alocar_novo_registro_generico((void **)&atividades, &num_atividades, sizeof(Atividade));
    nova_ativ->id = obter_proximo_id("atividades.csv", sizeof(Atividade));
    nova_ativ->id_turma = id_turma;

    printf("Descricao (Max 150): "); scanf(" %149[^\n]", nova_ativ->descricao); limpa_buffer();
    
    float peso_input;
    printf("Peso (em %% - Ex: 40 para 40%%): ");
    if (scanf("%f", &peso_input) != 1 || peso_input < 0 || peso_input > 100) { 
        limpa_buffer(); 
        printf("Peso invalido. Atividade nao cadastrada.\n");
        num_atividades--;
        return;
    }
    nova_ativ->peso = peso_input / 100.0f;
    limpa_buffer();

    printf("Data de Entrega (DD/MM/AAAA): "); scanf(" %10s", nova_ativ->data_entrega); limpa_buffer();

    // O main.c cuida de salvar em dados/atividades.csv
    if (salvar_dados_csv("atividades.csv", atividades, num_atividades, sizeof(Atividade), ACESSO_PROFESSOR)) {
        printf("✅ Atividade '%s' cadastrada na Turma %s.\n", nova_ativ->descricao, t->codigo);
    } else {
        printf("❌ Erro ao salvar atividade.\n");
    }
}

// =================================================================
// --- 7. FUNÇÕES LÓGICA DE NEGÓCIO E ALUNO ---
// =================================================================

void matricular_aluno_turma() {
    int id_aluno, id_turma;

    listar_alunos();
    printf("Digite o ID do aluno a ser matriculado: ");
    if (scanf("%d", &id_aluno) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    listar_turmas();
    printf("Digite o ID da turma para matricular o aluno: ");
    if (scanf("%d", &id_turma) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    if (!buscar_aluno_por_id(id_aluno) || !buscar_turma_por_id(id_turma)) {
        printf("❌ Aluno ou Turma nao encontrados.\n");
        return;
    }
    
    Matricula *nova_mat = (Matricula *)alocar_novo_registro_generico((void **)&matriculas, &num_matriculas, sizeof(Matricula));
    nova_mat->id_aluno = id_aluno;
    nova_mat->id_turma = id_turma;

    // O main.c cuidará de salvar em dados/matriculas.csv
    if (salvar_dados_csv("matriculas.csv", matriculas, num_matriculas, sizeof(Matricula), 6)) { 
        printf("✅ Aluno ID %d matriculado na Turma ID %d com sucesso.\n", id_aluno, id_turma);
    } else {
        printf("❌ Erro ao salvar dados de matricula.\n");
    }
}

void lancar_nota(int id_professor) {
    int id_turma, id_atividade, id_aluno;
    float nota;

    printf("\n--- LANÇAMENTO DE NOTAS ---\n");
    listar_turmas();
    printf("ID da Turma para lancar nota: ");
    if (scanf("%d", &id_turma) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    Turma *t = buscar_turma_por_id(id_turma);
    if (!t || t->id_professor_responsavel != id_professor) {
        printf("❌ Turma nao encontrada ou voce nao e o professor responsavel.\n");
        return;
    }

    listar_atividades_turma(id_turma);
    printf("ID da Atividade: ");
    if (scanf("%d", &id_atividade) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();
    
    printf("ID do Aluno: ");
    if (scanf("%d", &id_aluno) != 1) { limpa_buffer(); printf("ID invalido.\n"); return; }
    limpa_buffer();

    printf("Nota (0.0 a 10.0): ");
    if (scanf("%f", &nota) != 1 || nota < 0.0 || nota > 10.0) { limpa_buffer(); printf("Nota invalida.\n"); return; }
    limpa_buffer();

    // Lógica para registrar/atualizar a nota
    Nota *nova_nota = (Nota *)alocar_novo_registro_generico((void **)&notas, &num_notas, sizeof(Nota));
    nova_nota->id_atividade = id_atividade;
    nova_nota->id_aluno = id_aluno;
    nova_nota->nota = nota;

    // O main.c cuidará de salvar em dados/notas.csv
    if (salvar_dados_csv("notas.csv", notas, num_notas, sizeof(Nota), 7)) {
        printf("✅ Nota %.2f lancada para o Aluno %d na Atividade %d.\n", nota, id_aluno, id_atividade);
    } else {
        printf("❌ Erro ao salvar dados de nota.\n");
    }
}

void visualizar_matriculas_aluno(int id_aluno) {
    Aluno *a = buscar_aluno_por_id(id_aluno);
    if (!a) return;

    printf("\n--- MATRÍCULAS DE %s ---\n", a->nome);
    printf("Codigo | Nome da Turma | Professor Responsavel\n");
    printf("---|---|---\n");
    int count = 0;
    
    for (int i = 0; i < num_matriculas; i++) {
        if (matriculas[i].id_aluno == id_aluno) {
            Turma *t = buscar_turma_por_id(matriculas[i].id_turma);
            if (t) {
                printf("%s | %s | %s\n", 
                    t->codigo, t->nome, 
                    buscar_nome_professor_por_id(t->id_professor_responsavel));
                count++;
            }
        }
    }
    
    if (count == 0) {
        printf("Nao esta matriculado em nenhuma turma.\n");
    }
}

void visualizar_notas_aluno(int id_aluno) {
    Aluno *a = buscar_aluno_por_id(id_aluno);
    if (!a) return;

    printf("\n--- NOTAS DE %s ---\n", a->nome);
    printf("Atividade ID | Descricao | Turma | Nota\n");
    printf("---|---|---|---\n");
    int count = 0;

    for (int i = 0; i < num_notas; i++) {
        if (notas[i].id_aluno == id_aluno) {
            Atividade *ativ = NULL;
            Turma *t = NULL;
            for(int j=0; j < num_atividades; j++) {
                if(atividades[j].id == notas[i].id_atividade) {
                    ativ = &atividades[j];
                    t = buscar_turma_por_id(ativ->id_turma);
                    break;
                }
            }

            printf("%d | %s | %s | %.2f\n", 
                notas[i].id_atividade, 
                ativ ? ativ->descricao : "Descricao Desconhecida", 
                t ? t->codigo : "N/A",
                notas[i].nota);
            count++;
        }
    }

    if (count == 0) {
        printf("Nenhuma nota lancada ainda.\n");
    }
}


// =================================================================
// --- 8. FUNÇÕES DE MENU E NAVEGAÇÃO ---
// =================================================================

void submenu_crud_aluno() {
    int opcao;
    do {
        printf("\n--- MENU CRUD ALUNOS ---\n");
        printf("1. Cadastrar Novo Aluno\n");
        printf("2. Listar Todos os Alunos\n");
        printf("3. Editar Aluno\n");
        printf("4. Excluir Aluno\n");
        printf("0. Voltar ao Menu Admin\n");
        printf("Opcao: ");

        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        switch (opcao) {
            case 1: cadastrar_aluno(); break;
            case 2: listar_alunos(); break;
            case 3: editar_aluno(); break;
            case 4: excluir_aluno(); break;
            case 0: break;
            default: printf("Opcao invalida.\n");
        }
    } while (opcao != 0);
}

void submenu_crud_professor() {
    int opcao;
    do {
        printf("\n--- MENU CRUD PROFESSORES ---\n");
        printf("1. Cadastrar Novo Professor\n");
        printf("2. Listar Todos os Professores\n");
        printf("3. Editar Professor\n");
        printf("4. Excluir Professor\n");
        printf("0. Voltar ao Menu Admin\n");
        printf("Opcao: ");

        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        switch (opcao) {
            case 1: cadastrar_professor(); break;
            case 2: listar_professores(); break;
            case 3: editar_professor(); break;
            case 4: excluir_professor(); break;
            case 0: break;
            default: printf("Opcao invalida.\n");
        }
    } while (opcao != 0);
}

void submenu_crud_turma() {
    int opcao;
    do {
        printf("\n--- MENU CRUD TURMAS ---\n");
        printf("1. Cadastrar Nova Turma\n");
        printf("2. Listar Todas as Turmas\n");
        printf("3. Editar Turma\n");
        printf("4. Excluir Turma\n");
        printf("5. Matricular Aluno em Turma\n");
        printf("0. Voltar ao Menu Admin\n");
        printf("Opcao: ");

        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        switch (opcao) {
            case 1: cadastrar_turma(); break;
            case 2: listar_turmas(); break;
            case 3: editar_turma(); break;
            case 4: excluir_turma(); break;
            case 5: matricular_aluno_turma(); break;
            case 0: break;
            default: printf("Opcao invalida.\n");
        }
    } while (opcao != 0);
}


void menu_admin(int id_admin) {
    int opcao;
    do {
        printf("\n--- MENU ADMINISTRADOR ---\n");
        printf("1. Gerenciar Alunos (CRUD)\n");
        printf("2. Gerenciar Professores (CRUD)\n");
        printf("3. Gerenciar Turmas/Matriculas\n");
        printf("0. Logout\n");
        printf("Opcao: ");

        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        switch (opcao) {
            case 1: submenu_crud_aluno(); break;
            case 2: submenu_crud_professor(); break;
            case 3: submenu_crud_turma(); break;
            case 0: printf("Fazendo logout...\n"); break;
            default: printf("Opcao invalida.\n"); break;
        }
    } while (opcao != 0);
}

void menu_professor(int id_professor) {
    int opcao;
    Professor *p = buscar_professor_por_id(id_professor);
    if (!p) return; 

    do {
        printf("\n--- MENU PROFESSOR: %s ---\n", p->nome);
        printf("1. Lancar Nota\n");
        printf("2. Cadastrar Atividade\n");
        printf("3. Listar Minhas Turmas\n");
        printf("0. Logout\n");
        printf("Opcao: ");

        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        switch (opcao) {
            case 1: lancar_nota(id_professor); break;
            case 2: cadastrar_atividade(id_professor); break;
            case 3: listar_turmas(); break;
            case 0: printf("Fazendo logout...\n"); break;
            default: printf("Opcao invalida.\n"); break;
        }
    } while (opcao != 0);
}

void menu_aluno(int id_aluno) {
    int opcao;
    Aluno *a = buscar_aluno_por_id(id_aluno);
    if (!a) return;

    do {
        printf("\n--- MENU ALUNO: %s ---\n", a->nome);
        printf("1. Visualizar Matriculas\n");
        printf("2. Visualizar Notas\n");
        printf("0. Logout\n");
        printf("Opcao: ");

        if (scanf("%d", &opcao) != 1) { limpa_buffer(); opcao = -1; }
        limpa_buffer();

        switch (opcao) {
            case 1: visualizar_matriculas_aluno(id_aluno); break;
            case 2: visualizar_notas_aluno(id_aluno); break;
            case 0: printf("Fazendo logout...\n"); break;
            default: printf("Opcao invalida.\n"); break;
        }
    } while (opcao != 0);
}
