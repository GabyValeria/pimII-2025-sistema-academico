#include "funcoes.h"
#include <sys/stat.h> // Para a função mkdir

#ifdef _WIN32
#include <direct.h> // Para _mkdir no Windows
#define mkdir(dir, mode) _mkdir(dir)
#endif

// --- FUNÇÕES AUXILIARES ---

/**
 * @brief Limpa o buffer de entrada do teclado (stdin).
 * Essencial para evitar problemas de leitura após usar scanf.
 */
void limpar_buffer(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF);
}

/**
 * @brief Remove caracteres de quebra de linha ('\n' ou '\r') do final de uma string.
 * @param s A string a ser modificada.
 * @return Ponteiro para a string modificada.
 */
char *remover_quebra(char *s) {
    if (!s) return s;
    size_t n = strlen(s);
    while (n > 0 && (s[n-1] == '\n' || s[n-1] == '\r')) {
        s[n-1] = '\0';
        n--;
    }
    return s;
}

/**
 * @brief Converte um valor inteiro para o tipo enumerado Papel.
 * @param p O inteiro representando o papel (0=Admin, 1=Professor, 2=Aluno).
 * @return O valor correspondente do enum Papel.
 */
Papel papel_de_int(int p) {
    if (p == 0) return PAPEL_ADMIN;
    if (p == 1) return PAPEL_PROFESSOR;
    return PAPEL_ALUNO;
}

/**
 * @brief Converte um valor do tipo Papel para sua representação em string.
 * @param p O valor do enum Papel.
 * @return Uma string constante descrevendo o papel.
 */
const char* papel_para_str(Papel p) {
    switch(p) {
        case PAPEL_ADMIN: return "ADMINISTRADOR";
        case PAPEL_PROFESSOR: return "PROFESSOR";
        case PAPEL_ALUNO: return "ALUNO";
        default: return "DESCONHECIDO";
    }
}

// --- GERENCIAMENTO DE ARQUIVOS E DIRETÓRIOS ---

/**
 * @brief Abre um arquivo com tratamento de erro.
 * @param caminho O caminho do arquivo.
 * @param modo O modo de abertura (ex: "r", "w", "a").
 * @return Um ponteiro para o arquivo (FILE*) ou NULL em caso de erro.
 */
FILE* abrir_arquivo(const char* caminho, const char* modo) {
    FILE* f = fopen(caminho, modo);
    if (!f) {
        fprintf(stderr, "ERRO CRITICO: Nao foi possivel abrir o arquivo '%s' no modo '%s'.\n", caminho, modo);
    }
    return f;
}

/**
 * @brief Garante que o diretório 'data' exista. Se não existir, tenta criá-lo.
 */
void garantir_diretorio_dados(void) {
    struct stat st = {0};
    if (stat(DATA_DIR, &st) == -1) {
        printf("Info: Diretorio 'data' nao encontrado. Tentando criar...\n");
        if (mkdir(DATA_DIR, 0777) == 0) {
            printf("Info: Diretorio 'data' criado com sucesso.\n");
        } else {
            fprintf(stderr, "ERRO: Falha ao criar o diretorio 'data'. Verifique as permissoes.\n");
        }
    }
}

/**
 * @brief Garante que um arquivo específico exista. Se não, cria um arquivo vazio.
 * @param caminho O caminho do arquivo a ser verificado/criado.
 * @return 1 se o arquivo existe ou foi criado, 0 em caso de erro.
 */
int garantir_arquivo(const char* caminho) {
    FILE* f = fopen(caminho, "a+"); // "a+" abre para leitura e escrita, cria se não existir
    if (!f) {
        fprintf(stderr, "ERRO: Nao foi possivel criar o arquivo '%s'.\n", caminho);
        return 0;
    }
    fclose(f);
    return 1;
}

/**
 * @brief Garante que o arquivo de usuários exista e tenha um administrador padrão.
 * @return 1 em caso de sucesso, 0 em caso de falha.
 */
int garantir_admin_padrao(void) {
    FILE* f = abrir_arquivo(ARQ_USUARIOS, "r");
    if (!f) return 0;

    char linha[512];
    long tamanho_arquivo = 0;
    fseek(f, 0, SEEK_END);
    tamanho_arquivo = ftell(f);
    fclose(f);

    // Se o arquivo estiver vazio, insere o admin
    if (tamanho_arquivo == 0) {
        printf("Info: Arquivo de usuarios vazio. Criando administrador padrao (admin/admin).\n");
        f = abrir_arquivo(ARQ_USUARIOS, "w");
        if (!f) return 0;
        // Formato: id;usuario;senha;papel;nome
        fprintf(f, "1;admin;admin;0;Administrador do Sistema\n");
        fclose(f);
        registrar_log("SISTEMA: Administrador padrao criado.");
    }
    return 1;
}

/**
 * @brief Garante que todos os arquivos base (.csv e .txt) existam na pasta 'data'.
 */
void garantir_arquivos_base(void) {
    garantir_arquivo(ARQ_USUARIOS);
    garantir_arquivo(ARQ_TURMAS);
    garantir_arquivo(ARQ_AULAS);
    garantir_arquivo(ARQ_ATIVIDADES);
    garantir_arquivo(ARQ_LOG);
    garantir_admin_padrao();
}

// --- LOGS E VALIDAÇÃO ---

/**
 * @brief Registra uma mensagem de log no arquivo 'data/logs.txt' com timestamp.
 * @param mensagem A mensagem a ser registrada.
 */
void registrar_log(const char* mensagem) {
    FILE* f_log = abrir_arquivo(ARQ_LOG, "a");
    if (!f_log) return;

    time_t agora = time(NULL);
    struct tm* t = localtime(&agora);
    char timestamp[20];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", t);

    fprintf(f_log, "[%s] [BACKEND] %s\n", timestamp, mensagem);
    fclose(f_log);
}

/**
 * @brief Valida se uma nota está no intervalo permitido (0.0 a 10.0).
 * @param nota A nota a ser validada.
 * @return 1 se a nota for válida, 0 caso contrário.
 */
int validar_nota(float nota) {
    return (nota >= 0.0 && nota <= 10.0);
}

// --- FUNÇÕES DE USUÁRIO ---

/**
 * @brief Encontra o próximo ID disponível para um novo usuário.
 * @return O maior ID encontrado + 1.
 */
int proximo_id_usuario(void) {
    FILE* f = abrir_arquivo(ARQ_USUARIOS, "r");
    int maior_id = 0;
    if (!f) return 1;

    int id_atual;
    while (fscanf(f, "%d;%*[^\n]\n", &id_atual) == 1) {
        if (id_atual > maior_id) {
            maior_id = id_atual;
        }
    }
    fclose(f);
    return maior_id + 1;
}

/**
 * @brief Busca um usuário pelo seu nome de login (RA para alunos).
 * @param usuario O nome de usuário a ser buscado.
 * @param saida Ponteiro para uma struct Usuario onde os dados serão armazenados se encontrado.
 * @return 1 se o usuário foi encontrado, 0 caso contrário.
 */
int buscar_usuario_por_nome(const char* usuario, Usuario* saida) {
    FILE* f = abrir_arquivo(ARQ_USUARIOS, "r");
    if (!f) return 0;

    Usuario u;
    int papel_int;
    char linha[512];
    while (fgets(linha, sizeof(linha), f)) {
        if (sscanf(linha, "%d;%49[^;];%49[^;];%d;%99[^\n]", &u.id, u.usuario, u.senha, &papel_int, u.nome) == 5) {
            u.papel = papel_de_int(papel_int);
            if (strcmp(u.usuario, usuario) == 0) {
                *saida = u;
                fclose(f);
                return 1;
            }
        }
    }
    fclose(f);
    return 0;
}

/**
 * @brief Adiciona um novo usuário ao arquivo 'usuarios.csv' após validação.
 * @param u A struct Usuario com os dados do novo usuário.
 * @return 1 em caso de sucesso, 0 em caso de falha (ex: usuário já existe).
 */
int adicionar_usuario(Usuario u) {
    // Validação de Dados Avançada
    Usuario temp;
    if (buscar_usuario_por_nome(u.usuario, &temp)) {
        printf("ERRO DE VALIDACAO: O nome de usuario/RA '%s' ja existe.\n", u.usuario);
        registrar_log("VALIDACAO FALHA: Tentativa de criar usuario duplicado.");
        return 0;
    }
    if (strlen(u.nome) < 3) {
        printf("ERRO DE VALIDACAO: O nome deve ter pelo menos 3 caracteres.\n");
        return 0;
    }
    if (strlen(u.senha) < 4) {
        printf("ERRO DE VALIDACAO: A senha deve ter pelo menos 4 caracteres.\n");
        return 0;
    }

    FILE* f = abrir_arquivo(ARQ_USUARIOS, "a");
    if (!f) return 0;

    u.id = proximo_id_usuario();
    fprintf(f, "%d;%s;%s;%d;%s\n", u.id, u.usuario, u.senha, u.papel, u.nome);
    fclose(f);

    char log_msg[200];
    sprintf(log_msg, "CADASTRO: Usuario '%s' (ID %d, Papel: %s) foi criado via terminal.", u.usuario, u.id, papel_para_str(u.papel));
    registrar_log(log_msg);

    return 1;
}

/**
 * @brief Processo de login de usuário via terminal.
 * @return Uma struct Usuario preenchida em caso de sucesso (id > 0), ou com id=0 em caso de falha.
 */
Usuario fazer_login(void) {
    char login[50];
    char senha[50];
    Usuario u = {0}; // Inicializa com ID 0

    printf("\n--- LOGIN ---\n");
    printf("Usuario (RA para aluno): ");
    fgets(login, sizeof(login), stdin);
    remover_quebra(login);

    printf("Senha: ");
    fgets(senha, sizeof(senha), stdin);
    remover_quebra(senha);

    if (buscar_usuario_por_nome(login, &u)) {
        if (strcmp(u.senha, senha) == 0) {
            printf("\nLogin bem-sucedido! Bem-vindo(a), %s (%s).\n", u.nome, papel_para_str(u.papel));
            
            char log_msg[100];
            sprintf(log_msg, "LOGIN SUCESSO: Usuario '%s' (ID %d) logou.", u.usuario, u.id);
            registrar_log(log_msg);
            return u;
        }
    }

    printf("\nERRO: Login ou senha incorretos.\n");
    char log_falha[100];
    sprintf(log_falha, "LOGIN FALHA: Tentativa de login para o usuario '%s'.", login);
    registrar_log(log_falha);
    
    u.id = 0; // Garante que o ID é 0 em caso de falha
    return u;
}

/**
 * @brief Adiciona uma nova atividade (nota/frequência) ao arquivo.
 * @param nova_atividade A struct Atividade com os dados.
 * @return 1 em sucesso, 0 em falha.
 */
int adicionar_atividade(Atividade nova_atividade) {
    if (!validar_nota(nova_atividade.nota)) {
        printf("ERRO DE VALIDACAO: A nota %.2f e invalida. Deve ser entre 0.0 e 10.0.\n", nova_atividade.nota);
        registrar_log("VALIDACAO FALHA: Tentativa de lancar nota invalida.");
        return 0;
    }

    FILE* f = abrir_arquivo(ARQ_ATIVIDADES, "a");
    if (!f) return 0;

    int proximo_id = 1; // Simplificado para este exemplo
    fprintf(f, "%d;%d;%d;%.2f;%d\n", proximo_id, nova_atividade.id_aula, nova_atividade.id_aluno, nova_atividade.nota, nova_atividade.frequencia);
    fclose(f);

    char log_msg[200];
    sprintf(log_msg, "LANCAMENTO: Nota %.2f e frequencia %d lancadas para Aluno ID %d na Aula ID %d.",
            nova_atividade.nota, nova_atividade.frequencia, nova_atividade.id_aluno, nova_atividade.id_aula);
    registrar_log(log_msg);

    return 1;
}

// --- MENUS DE INTERFACE (TERMINAL) ---

/**
 * @brief Exibe o menu de opções para o Administrador.
 * @param u O usuário administrador logado.
 */
void menu_admin(Usuario u) {
    printf("\n== Menu do Administrador ==\n");
    printf("O gerenciamento detalhado (CRUD de usuarios, turmas, etc.)\n");
    printf("e a visualizacao de relatorios estao disponiveis na interface\n");
    printf("grafica em Python (app.py).\n");
    printf("Este backend em C serve para a manipulacao inicial de dados.\n");
    printf("\n0) Logout\n");
    
    int opcao;
    do {
        printf("Escolha uma opcao: ");
        if(scanf("%d", &opcao) != 1) {
            limpar_buffer();
            opcao = -1; // Força repetição
        }
        limpar_buffer();
        if(opcao != 0) printf("Opcao invalida.\n");
    } while (opcao != 0);
}

/**
 * @brief Exibe o menu para o Professor.
 * @param u O usuário professor logado.
 */
void menu_professor(Usuario u) {
    printf("\n== Menu do Professor ==\n");
    printf("Para lancar notas e visualizar relatorios, por favor, utilize\n");
    printf("a interface grafica em Python (app.py), que oferece uma\n");
    printf("experiencia mais completa e visual.\n");
    printf("\n0) Logout\n");

    int opcao;
    do {
        printf("Escolha uma opcao: ");
        if(scanf("%d", &opcao) != 1) {
            limpar_buffer();
            opcao = -1;
        }
        limpar_buffer();
        if(opcao != 0) printf("Opcao invalida.\n");
    } while (opcao != 0);
}

/**
 * @brief Exibe o menu para o Aluno.
 * @param u O usuário aluno logado.
 */
void menu_aluno(Usuario u) {
    printf("\n== Menu do Aluno ==\n");
    printf("Para consultar suas notas, desempenho e gerar relatorios, \n");
    printf("acesse a interface grafica em Python (app.py).\n");
    printf("\n0) Logout\n");
    
    int opcao;
    do {
        printf("Escolha uma opcao: ");
        if(scanf("%d", &opcao) != 1) {
            limpar_buffer();
            opcao = -1;
        }
        limpar_buffer();
        if(opcao != 0) printf("Opcao invalida.\n");
    } while (opcao != 0);
}
