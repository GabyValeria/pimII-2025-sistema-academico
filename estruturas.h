#ifndef ESTRUTURAS_H
#define ESTRUTURAS_H

// Inclusão de bibliotecas
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
// Inclusões para manipulação de diretório:
#include <sys/stat.h> // Para mkdir
#include <errno.h>    // Para verificar erros do mkdir

// Se estiver no Windows (MSVC) usa-se <direct.h>
#ifdef _WIN32
#include <direct.h> 
#define MKDIR(name) _mkdir(name)
#else
// Para sistemas Unix-like (Linux, macOS)
#define MKDIR(name) mkdir(name, 0777)
#endif


// --- Definições de Estruturas (Structs) ---
typedef struct {
    int id;
    char login[50];
    char senha[50];
    char nome[100];
} Usuario;

typedef struct {
    int id;           
    char nome[100];
    char matricula[20];
    char cpf[15];
    char login[50];
    char senha[50];
} Aluno;

typedef struct {
    int id;           
    char nome[100];
    char siape[20];   
    char cpf[15];
    char login[50];
    char senha[50];
} Professor;

typedef struct {
    int id;           
    char nome[100];  
    char codigo[20];  
    int id_professor_responsavel;
    char semestre[10]; 
} Turma;

typedef struct {
    int id_turma;
    int id_aluno;
} Matricula;

typedef struct {
    int id;          
    int id_turma;
    char descricao[150];
    float peso;
    char data_entrega[11]; 
} Atividade;

typedef struct {
    int id_atividade;
    int id_aluno;
    float nota;
} Nota;

// --- Definições de Enums e Constantes ---
typedef enum {
    ADMIN = 1,
    PROFESSOR = 2,
    ALUNO = 3,
    SAIR = 0
} NivelAcesso;

#endif 