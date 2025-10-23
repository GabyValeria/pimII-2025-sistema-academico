@startuml
title Diagrama de Casos de Uso - Sistema Acadêmico com IA

left to right direction
skinparam packageStyle rectangle
skinparam actorStyle awesome
skinparam usecase {
  BackgroundColor LightBlue
  BorderColor Black
  ArrowColor Black
}
skinparam title {
  FontSize 18
  FontStyle bold
  Alignment center
}

' ---- Atores ----
actor "Professor" as prof
actor "Admin" as admin
actor "Aluno" as aluno
actor "Serviço de IA" as ia

' ---- Sistema ----
rectangle "Sistema" {
    usecase "Gerenciar Alunos" as UC1
    usecase "Gerenciar Turmas" as UC2
    usecase "Publicar Atividades / Upload" as UC3
    usecase "Corrigir / Lançar Notas" as UC4
    usecase "Logar / Autenticar" as UC5
    usecase "Enviar Mensagens" as UC6
    usecase "Buscar / Consultar com IA" as UC7
    usecase "Gerar Relatório Acadêmico (PDF)" as UC8
    usecase "Registrar Aula / Diário" as UC9
    usecase "Entregar Atividade" as UC10
}

' ---- Ligações dos atores ----
prof --> UC1
prof --> UC2
prof --> UC3
prof --> UC4
prof --> UC5
prof --> UC6
prof --> UC7
prof --> UC8
prof --> UC9
prof --> UC10

admin --> UC1
admin --> UC2
admin --> UC3
admin --> UC5

aluno --> UC5
aluno --> UC6
aluno --> UC7
aluno --> UC10

ia --> UC7

' ---- Relações include/extend ----
UC9 .> UC10 : <<include>>
UC8 .> UC9 : <<extends>>
UC7 .> UC8 : <<include>>
UC5 .> UC7 : <<consultar>>
UC4 .> UC5 : <<include>>

@enduml
