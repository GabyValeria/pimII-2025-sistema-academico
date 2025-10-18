#ifndef FUNCOES_H
#define FUNCOES_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h> // Para registrar logs com data e hora

// --- DEFINIÇÃO DOS CAMINHOS DOS ARQUIVOS ---
#define DATA_DIR "data"
#define ARQ_USUARIOS   "data/usuarios.csv"
#define ARQ_TURMAS     "data/turmas.csv"
#define ARQ_AULAS      "data/aulas.csv"
#define ARQ_ATIVIDADES "data/atividades.csv"
#define ARQ_LOG        "data/logs.txt"

// --- ESTRUTURAS DE DADOS ---

/**
 * @enum Papel
 * @brief Define os níveis de acesso dos usuários.
 */
typedef enum {
    PAPEL_ADMIN,      // Nível 0: Acesso total
    PAPEL_PROFESSOR,  // Nível 1: Acesso a suas turmas e alunos
    PAPEL_ALUNO       // Nível 2: Acesso apenas aos seus próprios dados
} Papel;

/**
 * @struct Usuario
 * @brief Armazena os dados de um usuário do sistema.
 */
typedef struct {
    int id;
    char usuario[50]; // RA para aluno, login para outros
    char senha[50];
    Papel papel;
    char nome[100];
} Usuario;

/**
 * @struct Turma
 * @brief Armazena os dados de uma turma.
 */
typedef struct {
    int id;
    char nome[100];
    int id_professor; // Chave estrangeira para a struct Usuario
} Turma;

/**
 * @struct Aula
 * @brief Armazena os dados de uma aula específica.
 */
typedef struct {
    int id;
    int id_turma; // Chave estrangeira para a struct Turma
    char data[11]; // Formato "DD/MM/AAAA"
    char topico[150];
} Aula;

/**
 * @struct Atividade
 * @brief Armazena a nota e a frequência de um aluno em uma aula.
 */
typedef struct {
    int id;
    int id_aula;  // Chave estrangeira para a struct Aula
    int id_aluno; // Chave estrangeira para a struct Usuario
    float nota;
    int frequencia; // 1 para presente, 0 para ausente
} Atividade;

// --- PROTÓTIPOS DAS FUNÇÕES ---

// Funções Auxiliares
void limpar_buffer(void);
char* remover_quebra(char *s);
Papel papel_de_int(int p);
const char* papel_para_str(Papel p);

// Gerenciamento de Arquivos
FILE* abrir_arquivo(const char* caminho, const char* modo);
void garantir_diretorio_dados(void);
void garantir_arquivos_base(void);

// Validação e Logs (Novas funções de segurança)
void registrar_log(const char* mensagem);
int validar_nota(float nota);

// Funções de Usuário
int proximo_id_usuario(void);
int buscar_usuario_por_nome(const char* usuario, Usuario* saida);
int adicionar_usuario(Usuario u);
Usuario fazer_login(void);

// Funções de Atividade
int adicionar_atividade(Atividade nova_atividade);

// Menus do Terminal
void menu_admin(Usuario u);
void menu_professor(Usuario u);
void menu_aluno(Usuario u);

#endif // FUNCOES_H
