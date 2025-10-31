#ifndef DADOS_H
#define DADOS_H

#include "estruturas.h"

// --- Protótipos das Funções de Utilidade/CSV (I/O) ---
void *carregar_dados_csv(const char *nome_arquivo, size_t tamanho_struct, int *num_registros, void **buffer_registros);
int salvar_dados_csv(const char *nome_arquivo, void *registros, int num_registros, size_t tamanho_struct, NivelAcesso tipo);
void inicializar_sistema();

// --- Protótipos de Funções CRUD Genéricas/Auxiliares ---
int obter_proximo_id(const char *nome_arquivo, size_t tamanho_struct);
void liberar_memoria(void *ptr);
void limpa_buffer(); // Função auxiliar para limpar buffer do teclado

// --- Protótipos CRUD de Aluno ---
void cadastrar_aluno();
void listar_alunos();
void editar_aluno();
void excluir_aluno();

// --- Protótipos CRUD de Professor ---
void cadastrar_professor();
void listar_professores();
void editar_professor();
void excluir_professor();

// --- Protótipos CRUD de Turma ---
void cadastrar_turma();
void listar_turmas();
void editar_turma();
void excluir_turma();

// --- Protótipos CRUD de Atividade ---
void cadastrar_atividade(int id_professor);
void listar_atividades(); 
void listar_atividades_turma(int id_turma); 
void editar_atividade();
void excluir_atividade();

// --- Protótipos Lógica de Negócios ---
void matricular_aluno_turma();
void lancar_nota(int id_professor); // Lançamento feito pelo Professor

// --- Protótipos de Login e Menu ---
int fazer_login(NivelAcesso nivel, int *id_usuario_logado);
void menu_admin(int id_admin);
void menu_professor(int id_professor);
void menu_aluno(int id_aluno);

#endif 