#ifndef ESTRUTURAS_H
#define ESTRUTURAS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h> 
#include <errno.h> // Para a verificação de erro EEXIST

// --- Headers condicionais para gerenciamento de diretórios ---
#ifdef _WIN32
    #include <direct.h>    // Para _mkdir
    #include <windows.h>   // Para GetLastError() e ERROR_ALREADY_EXISTS
    #define MAKE_DIR(name) _mkdir(name)
#else
    #include <sys/stat.h>  // Para mkdir
    #include <sys/types.h>
    #define MAKE_DIR(name) mkdir(name, 0777) // Permissões 777 (rwxrwxrwx)
#endif
// -----------------------------------------------------------


// =================================================================
// --- 1. DEFINIÇÕES E CONSTANTES ---
// =================================================================

#define MAX_NOME 100
#define MAX_LOGIN 50
#define MAX_SENHA 50
#define MAX_MATRICULA 20
#define MAX_SIAPE 20
#define MAX_CPF 15
#define MAX_CODIGO 20
#define MAX_SEMESTRE 10
#define MAX_DESCRICAO_ATIVIDADE 150
#define MAX_DATA 11 
#define CHAVE_CRIPTOGRAFIA 5

#define ACESSO_ADMIN 1
#define ACESSO_PROFESSOR 2
#define ACESSO_ALUNO 3
#define ACESSO_NAO_AUTENTICADO 0

#define PASTA_DADOS "dados/"
#define TAMANHO_CAMINHO 256


// =================================================================
// --- 2. ESTRUTURAS DE DADOS (STRUCTS) ---
// =================================================================

typedef struct {
    int id;
    char nome[MAX_NOME];
    char matricula[MAX_MATRICULA];
    char cpf[MAX_CPF];
    char login[MAX_LOGIN];
    char senha[MAX_SENHA];
} Aluno;

typedef struct {
    int id;
    char nome[MAX_NOME];
    char siape[MAX_SIAPE];
    char cpf[MAX_CPF];
    char login[MAX_LOGIN];
    char senha[MAX_SENHA];
} Professor;

typedef struct {
    int id;
    char nome[MAX_NOME];
    char codigo[MAX_CODIGO];
    char semestre[MAX_SEMESTRE];
    int id_professor_responsavel;
} Turma;

typedef struct {
    int id;
    char descricao[MAX_DESCRICAO_ATIVIDADE];
    int id_turma;
    float peso;
    char data_entrega[MAX_DATA];
} Atividade;

typedef struct {
    int id_aluno;
    int id_turma;
} Matricula;

typedef struct {
    int id_atividade;
    int id_aluno;
    float nota;
} Nota;

// Struct para o Usuário/Admin
typedef struct {
    int id;
    char nome[MAX_NOME];
    char login[MAX_LOGIN];
    char senha[MAX_SENHA];
    int tipo_acesso;
} Usuario;


// =================================================================
// --- 3. VARIÁVEIS GLOBAIS DE DADOS ---
// =================================================================

extern Aluno *alunos;
extern int num_alunos;

extern Professor *professores;
extern int num_professores;

extern Turma *turmas;
extern int num_turmas;

extern Atividade *atividades;
extern int num_atividades;

extern Matricula *matriculas;
extern int num_matriculas;

extern Nota *notas;
extern int num_notas;

extern Usuario admin_master;


// =================================================================
// --- 4. PROTÓTIPOS DE FUNÇÕES AUXILIARES, CRIPTOGRAFIA E I/O ---
// =================================================================

void limpa_buffer();
int obter_proximo_id(const char *nome_arquivo, size_t tamanho_struct);
int salvar_dados_csv(const char *nome_arquivo, const void *dados, int num_registros, size_t tamanho_struct, int tipo_acesso);
int carregar_dados_csv();
void liberar_memoria();
void inicializar_sistema(); 
int fazer_login(int tipo_acesso_desejado, int *id_usuario_logado);
int salvar_admin_csv();
int carregar_admin_csv();

int garantir_diretorio_dados();

void criptografar_string(char *str);
void descriptografar_string(char *str);

void *alocar_novo_registro_generico(void **registros, int *num_registros, size_t tamanho_struct);
int excluir_registro_generico(void **registros, int *num_registros, size_t tamanho_struct, int id_excluir, int (*obter_id)(const void *));

int obter_id_aluno(const void *registro);
int obter_id_professor(const void *registro);
int obter_id_turma(const void *registro);
int obter_id_atividade(const void *registro);

Aluno *buscar_aluno_por_id(int id_aluno);
Professor *buscar_professor_por_id(int id_prof);
Turma *buscar_turma_por_id(int id_turma);
char *buscar_nome_professor_por_id(int id_prof);


// =================================================================
// --- 5. PROTÓTIPOS DE FUNÇÕES CRUD E LÓGICA DE NEGÓCIO ---
// =================================================================

void cadastrar_aluno();
void listar_alunos();
void editar_aluno();
void excluir_aluno();
void cadastrar_professor();
void listar_professores();
void editar_professor();
void excluir_professor();
void cadastrar_turma();
void listar_turmas();
void editar_turma();
void excluir_turma();
void listar_atividades_turma(int id_turma);
void cadastrar_atividade(int id_professor);
void matricular_aluno_turma();
void lancar_nota(int id_professor);
void visualizar_matriculas_aluno(int id_aluno);
void visualizar_notas_aluno(int id_aluno);
void submenu_crud_aluno();
void submenu_crud_professor();
void submenu_crud_turma();
void menu_admin(int id_admin);
void menu_professor(int id_professor);
void menu_aluno(int id_aluno);
void main_menu();


#endif 
