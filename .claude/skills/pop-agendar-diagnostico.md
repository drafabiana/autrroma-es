---
name: pop-agendar-diagnostico
description: Agenda a Reuniao de Diagnostico do lead pelo link oficial do escritorio, com as regras do comercial sobre agenda da Dra. Fabiana, remarcacao e cancelamento. Use ao marcar, remarcar ou cancelar reuniao de diagnostico.
trigger: /agendar-diagnostico
---

# Skill: Agendamento de Reuniao de Diagnostico

> Fonte: `G:\Meu Drive\ALVES CARNEIRO\RCC E POP\POP – AGENDAMENTO DE REUNIÃO DE DIAGNÓSTICO.docx`
> Setor: Comercial.

## Regra principal

Todo agendamento e feito **exclusivamente pelo link oficial "Reuniao de
Diagnostico"** do escritorio. **Nunca criar o atendimento manualmente no Google
Agenda.**

O link ja considera os horarios liberados pela Dra. Fabiana e os compromissos
bloqueados na agenda dela (audiencias, clientes, Forcas Armadas, producao de
conteudo, reunioes).

## Passo a passo

1. **Qualificar o lead** — confirmar: nome completo · demanda juridica ·
   telefone/WhatsApp · e-mail · interesse em realizar a reuniao.
2. **Abrir a pagina de agendamento** pelo favorito `📅 AGENDAR REUNIAO DE DIAGNOSTICO`.
3. **Consultar os horarios** — informar ao lead **somente** o que aparece disponivel.
4. **Confirmar o horario com o lead**, oferecendo opcoes:
   > "Tenho disponibilidade para segunda-feira às 14h ou 16h10. Qual horário fica
   > melhor para você?"
5. **Fazer a reserva** com **os dados do LEAD**, nunca os da colaboradora:
   nome · sobrenome · e-mail do lead · telefone/WhatsApp. Revisar antes de confirmar.
6. **Confirmar o agendamento** — finalizar e verificar se o horario saiu da lista de
   disponiveis. O Google envia as informacoes e, quando aplicavel, o link do Meet.
7. **Confirmar com o lead pelo WhatsApp** — avisar que a reuniao foi registrada e
   pedir que verifique o convite recebido por e-mail.

## Regras do comercial

1. Nao criar reuniao manualmente na agenda da Dra. Fabiana.
2. Nao criar reuniao manualmente na agenda Comercial quando for Reuniao de Diagnostico.
3. Usar sempre a pagina oficial de agendamento.
4. Nunca oferecer horario que nao esteja disponivel na pagina.
5. Nunca substituir ou remover compromisso existente para encaixar um lead.
6. Nunca pedir disponibilidade a Dra. Fabiana antes de consultar a pagina.
7. Preencher sempre os dados do lead na reserva.
8. Conferir **principalmente o e-mail** antes de finalizar — e por ele que o cliente
   recebe as informacoes da reuniao.

## Remarcacao ou cancelamento

- Nao criar uma segunda reuniao sem tratar a anterior;
- Verificar os novos horarios disponiveis;
- Confirmar o novo horario com o lead;
- Realizar a remarcacao/cancelamento pelo procedimento do escritorio;
- Confirmar a alteracao com o lead.

**Nunca deixar dois horarios reservados para o mesmo lead.**

## Duvida ou conflito

Se o lead pedir horario que nao aparece disponivel, informar que aquele horario nao
esta disponivel e apresentar as alternativas. **Nao fazer encaixe sem autorizacao.**
Havendo erro, conflito de agenda ou situacao excepcional, comunicar o responsavel
**antes** de alterar qualquer compromisso.

## Fluxo

```
LEAD QUALIFICADO
  ↓ abrir link "REUNIAO DE DIAGNOSTICO"
  ↓ consultar horarios disponiveis
  ↓ oferecer opcoes ao lead
  ↓ lead escolhe o horario
  ↓ preencher DADOS DO LEAD
  ↓ confirmar reserva
  ↓ confirmar agendamento pelo WhatsApp
```

## Regra de ouro

**Se o horario nao aparece disponivel na pagina de agendamento, ele nao deve ser
oferecido ao lead.**

## Nota para a automacao

Esta skill nao tem acesso a pagina de agendamento nem a agenda do Google — ela
**monta o roteiro e os textos** e a colaboradora executa. Antes disso, ver
`/lead-consulta`: o agendamento so acontece depois do envio dos documentos e da
confirmacao do pagamento da consulta.

**Excecao — campanhas de isencao de IR e do Acordao 2225** (Dra. Fabiana, 03 e
04/11/2026): a reuniao **nao e cobrada** e se marca logo apos a qualificacao, sem
esperar documento nem pagamento. O SDR nao fala de honorarios; o fechamento e da
Dra. Fabiana na reuniao. Roteiros em `/script-isencao-ir` e `/script-acordao-2225`,
secao 6.

> Referencia de organizacao da agenda: `RCC E POP\BLOCOS DE CORES – AGENDA GOOGLE.docx`.
