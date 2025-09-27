```mermaid
flowchart LR
  Professor[Professor] -->|Solicitações / Dados| Sistema[(Sistema Acadêmico Colaborativo)]
  Aluno[Aluno] -->|Atividades / Consultas| Sistema
  Admin[Administrador] -->|Configuração / Gerenciamento| Sistema
  Sistema -->|Relatórios PDF / Arquivos| Arquivos[Servidor de Arquivos / PDF]
  Sistema -->|Dados / Insights| IA[Serviço de IA]
```