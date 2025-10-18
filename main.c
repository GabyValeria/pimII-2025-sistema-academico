#include "funcoes.h"

/**
 * @brief Função principal que executa o loop do menu inicial.
 * @return 0 em caso de saída bem-sucedida.
 */
int main(void) {
    printf("=======================================\n");
    printf("   Sistema Academico - Backend em C    \n");
    printf("=======================================\n\n");

    // 1. Garante que a pasta 'data' e todos os arquivos .csv e .txt existam
    garantir_diretorio_dados();
    garantir_arquivos_base();

    registrar_log("SISTEMA INICIADO (BACKEND C)");

    int opcao;
    // Loop principal do menu
    while (1) {
        printf("\n--- MENU INICIAL ---\n");
        printf("1) Login no Sistema\n");
        printf("2) Cadastrar Novo Aluno (Primeiro acesso)\n");
        printf("0) Sair do Programa\n");
        printf("Escolha uma opcao: ");

        // Leitura segura da opção do usuário
        if (scanf("%d", &opcao) != 1) {
            limpar_buffer(); // Limpa a entrada inválida
            opcao = -1;      // Atribui um valor inválido para repetir o loop
        }
        limpar_buffer(); // Sempre limpa o buffer após um scanf

        switch (opcao) {
            case 1: {
                // Tenta realizar o login
                Usuario u_logado = fazer_login();

                // Se o login for bem-sucedido (ID diferente de 0)
                if (u_logado.id != 0) {
                    // Redireciona para o menu apropriado com base no papel do usuário
                    if (u_logado.papel == PAPEL_ADMIN) {
                        menu_admin(u_logado);
                    } else if (u_logado.papel == PAPEL_PROFESSOR) {
                        menu_professor(u_logado);
                    } else if (u_logado.papel == PAPEL_ALUNO) {
                        menu_aluno(u_logado);
                    }
                }
                break;
            }
            case 2: {
                // Permite que um novo aluno se cadastre pelo terminal
                // Professores e Admins são cadastrados pela interface gráfica
                printf("\n--- CADASTRO DE NOVO ALUNO ---\n");
                Usuario novo_aluno = {0};
                novo_aluno.papel = PAPEL_ALUNO;

                printf("Nome Completo: ");
                fgets(novo_aluno.nome, sizeof(novo_aluno.nome), stdin);
                remover_quebra(novo_aluno.nome);

                printf("RA (sera seu usuario de login): ");
                fgets(novo_aluno.usuario, sizeof(novo_aluno.usuario), stdin);
                remover_quebra(novo_aluno.usuario);

                printf("Senha: ");
                fgets(novo_aluno.senha, sizeof(novo_aluno.senha), stdin);
                remover_quebra(novo_aluno.senha);

                if (adicionar_usuario(novo_aluno)) {
                    printf("\nAluno cadastrado com sucesso! Voce ja pode fazer o login.\n");
                } else {
                    printf("\nFalha no cadastro. Verifique os dados e tente novamente.\n");
                }
                break;
            }
            case 0:
                // Encerra o programa
                printf("\nEncerrando o backend...\n");
                registrar_log("SISTEMA FINALIZADO (BACKEND C)");
                return 0; // Sai do loop e da função main

            default:
                // Mensagem para qualquer outra entrada
                printf("\nOpcao invalida. Por favor, tente novamente.\n");
                break;
        }
    }

    return 0; // Fim do programa
}