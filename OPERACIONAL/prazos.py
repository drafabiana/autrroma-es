"""
=============================================================================
  PRAZOS EM ABERTO - ALVES CARNEIRO ADVOCACIA E CONSULTORIA JURIDICA
=============================================================================

  Fonte unica da verdade sobre "prazo em aberto" no ADVBOX. Usado por:
    - OPERACIONAL/main.py prazos          (consulta na tela)
    - OPERACIONAL/prazos_diario.py        (relatorio diario das 9h por e-mail)

  Prazo em aberto = tarefa do ADVBOX (/posts) que tem date_deadline e cujo
  destinatario AINDA NAO concluiu.

  POR QUE ESTE MODULO EXISTE
  A versao anterior do comando `prazos` consultava a API de hoje ate +14 dias.
  Prazo JA VENCIDO e nao concluido ficava fora da janela e, portanto, invisivel:
  na conferencia de 16/10/2026 havia 8 prazos em aberto e o relatorio mostrava
  apenas 2 - os 6 vencidos (um deles "fazer apelacao") nao apareciam. Aqui a
  janela comeca no passado e os vencidos vem PRIMEIRO.

  Somente leitura - nenhuma funcao deste modulo escreve no ADVBOX.
=============================================================================
"""
import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'INTEGRACOES'))

import advbox_integration as ad


# Quanto tempo para tras a busca varre em procura de prazo vencido e nao
# concluido. 3 anos cobre o acervo ativo do escritorio com folga.
DIAS_RETROATIVOS = 365 * 3

# Janela padrao para frente (o mesmo horizonte do comando antigo).
DIAS_ADIANTE = 14


def coletar(dias_adiante=DIAS_ADIANTE, hoje=None, incluir_sem_prazo=False):
    """
    Devolve os prazos em aberto, ja classificados e ordenados.

    dias_adiante: horizonte futuro, em dias.
    hoje: date, para teste; o padrao e a data corrente.
    incluir_sem_prazo: tambem devolve as tarefas pendentes SEM date_deadline
                       (ficam na chave 'sem_prazo', nunca misturadas).

    Retorna dict:
      {
        'hoje': date,
        'vencidos': [item, ...],   # prazo < hoje, mais antigo primeiro
        'hoje_lista': [item, ...], # prazo == hoje
        'proximos': [item, ...],   # hoje < prazo <= hoje + dias_adiante
        'sem_prazo': [item, ...],  # so se incluir_sem_prazo
        'total': int,              # vencidos + hoje + proximos
      }

    Cada item:
      {'id', 'prazo' (date), 'dias' (int, negativo = vencido), 'tarefa',
       'notas', 'urgente' (bool), 'responsaveis' [str], 'cliente', 'clientes',
       'processo', 'lawsuit_id', 'criada'}
    """
    hoje = hoje or date.today()
    inicio = hoje - timedelta(days=DIAS_RETROATIVOS)
    fim = hoje + timedelta(days=dias_adiante)

    # Desde 05/11/2026 o ADVBOX recusa (422) intervalo de prazo maior que 1 ano:
    # consulta em fatias de ate 364 dias, da mais recente para a mais antiga.
    tarefas, vistas = [], set()
    fatia_fim = fim
    while fatia_fim >= inicio:
        fatia_ini = max(inicio, fatia_fim - timedelta(days=364))
        for t in ad.listar_tarefas(deadline_start=fatia_ini.strftime('%Y-%m-%d'),
                                   deadline_end=fatia_fim.strftime('%Y-%m-%d')):
            if t.get('id') not in vistas:   # dia de fronteira nao duplica tarefa
                vistas.add(t.get('id'))
                tarefas.append(t)
        fatia_fim = fatia_ini - timedelta(days=1)

    vencidos, do_dia, proximos = [], [], []
    for t in tarefas:
        item = _montar_item(t, hoje)
        if item is None:
            continue
        if item['dias'] < 0:
            vencidos.append(item)
        elif item['dias'] == 0:
            do_dia.append(item)
        else:
            proximos.append(item)

    vencidos.sort(key=lambda i: i['prazo'])
    do_dia.sort(key=lambda i: i['cliente'])
    proximos.sort(key=lambda i: i['prazo'])

    resultado = {
        'hoje': hoje,
        'vencidos': vencidos,
        'hoje_lista': do_dia,
        'proximos': proximos,
        'sem_prazo': [],
        'total': len(vencidos) + len(do_dia) + len(proximos),
    }

    if incluir_sem_prazo:
        resultado['sem_prazo'] = _coletar_sem_prazo(hoje)

    return resultado


def _coletar_sem_prazo(hoje):
    """Tarefas pendentes que nao tem date_deadline algum."""
    itens = []
    for t in ad.listar_tarefas():
        if t.get('date_deadline'):
            continue
        item = _montar_item(t, hoje, exigir_prazo=False)
        if item:
            itens.append(item)
    itens.sort(key=lambda i: i['criada'] or '')
    return itens


def _montar_item(tarefa, hoje, exigir_prazo=True):
    """Normaliza uma tarefa do /posts. Devolve None se nao estiver em aberto."""
    pendentes = [u for u in (tarefa.get('users') or []) if not u.get('completed')]
    if not pendentes:
        return None

    bruto = (tarefa.get('date_deadline') or '')[:10]
    if exigir_prazo and not bruto:
        return None

    prazo = None
    dias = None
    if bruto:
        try:
            prazo = datetime.strptime(bruto, '%Y-%m-%d').date()
            dias = (prazo - hoje).days
        except ValueError:
            return None

    processo = tarefa.get('lawsuit') or {}
    clientes = [c.get('name', '') for c in (processo.get('customers') or []) if c.get('name')]

    return {
        'id': tarefa.get('id'),
        'prazo': prazo,
        'dias': dias,
        'tarefa': tarefa.get('task') or '',
        'notas': (tarefa.get('notes') or '').strip(),
        'urgente': any(u.get('urgent') or u.get('important') for u in pendentes),
        'responsaveis': [u.get('name', '') for u in pendentes],
        'cliente': clientes[0] if clientes else '',
        'clientes': clientes,
        'processo': processo.get('process_number') or '',
        'lawsuit_id': processo.get('id'),
        'criada': (tarefa.get('created_at') or '')[:10],
    }


def descrever_dias(dias):
    """'vencido ha 56 dias', 'VENCE HOJE', 'em 4 dias'."""
    if dias is None:
        return 'sem prazo'
    if dias < 0:
        d = abs(dias)
        return 'vencido ha %d dia%s' % (d, '' if d == 1 else 's')
    if dias == 0:
        return 'VENCE HOJE'
    return 'em %d dia%s' % (dias, '' if dias == 1 else 's')
