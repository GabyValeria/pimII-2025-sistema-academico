#include <stdio.h>
#include <stdlib.h>
#include "dados.h" 

// Funções de Menu (implementadas em dados.c)
extern void inicializar_sistema();
extern int fazer_login(NivelAcesso nivel, int *id_usuario_logado);
extern void menu_admin(int id_admin);
extern void menu_professor(int id_professor);
extern void menu_aluno(int id_aluno);
extern void limpa_buffer();


int main() {
    int opcao;
    int id_logado = -1;

    // 1. Inicialização do Sistema
    // Carrega todos os dados dos arquivos CSV para a memória
    inicializar_sistema();

    // 2. Loop Principal de Login/Menu
    do {
        printf("\n==================================\n");
        printf("SISTEMA DE GESTÃO ACADÊMICA (SGA)\n");
        printf("==================================\n");
        printf("1. Login como Administrador\n");
        printf("2. Login como Professor\n");
        printf("3. Login como Aluno\n");
        printf("0. Sair do Sistema\n");
        printf("Escolha o tipo de acesso: ");

        if (scanf("%d", &opcao) != 1) {
            limpa_buffer(); // Limpa o buffer em caso de entrada não numérica
            opcao = -1;
        }
        limpa_buffer(); // Garante que o buffer esteja limpo após a leitura

        switch (opcao) {
            case 1:
                if (fazer_login(ADMIN, &id_logado)) {
                    menu_admin(id_logado);
                }
                break;
            case 2:
                if (fazer_login(PROFESSOR, &id_logado)) {
                    menu_professor(id_logado);
                }
                break;
            case 3:
                if (fazer_login(ALUNO, &id_logado)) {
                    menu_aluno(id_logado);
                }
                break;
            case 0:
                printf("\nEncerrando o Sistema de Gestão Acadêmica. Até logo!\n");
                break;
            default:
                printf("Opcao invalida. Por favor, escolha 1, 2, 3 ou 0.\n");
                break;
        }

    } while (opcao != 0);

    return 0;
}