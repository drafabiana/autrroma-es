"""
=============================================================================
  TRIAGEM CLIENTE x PARTE CONTRARIA (ADVBOX -> Infinitum)
=============================================================================

  Le o mapa do ADVBOX e propoe, para cada um dos ~310 registros de "cliente",
  se ele e CLIENTE, PARTE CONTRARIA ou DUVIDOSO - e grava um CSV para a
  Dra. Fabiana marcar a coluna DECISAO.

  POR QUE ESTA ETAPA EXISTE
  O ADVBOX nao distingue cliente de parte contraria: `customers[]` do processo
  nao tem campo de papel nenhum, so id/nome/CPF/origem. Entao UNIAO FEDERAL,
  INSS (em 4 grafias), ESTADO DO RIO, LIGHT, MINISTERIO PUBLICO FEDERAL e 15
  empresas com CNPJ estao no mesmo balaio dos clientes de verdade.

  E POR QUE A DECISAO E DELA, NAO MINHA
  O conector do Infinitum **nao tem rota para apagar registro de cadastro nem
  card** (so apaga campo de POP, campo de cadastro, automacao, tarefa e evento
  de agenda). Registro criado por engano some so a mao, na interface. Entao
  nenhuma subida em lote acontece antes da marcacao.

  Heuristica (transparente de proposito - ela sobrepoe):
    PARTE CONTRARIA  CNPJ, ou nome de orgao/empresa por palavra inteira
    DUVIDOSO         aparece em 3+ processos sem CNPJ, ou cadastro vazio
    CLIENTE          o resto
  A comparacao e por PALAVRA INTEIRA: sem isso "FABIANA" casa com "FAB" e
  "CAMILA" casa com "AMIL" - os dois falsos positivos que esta versao evita.

  Uso: python SYNC/triagem_clientes.py
  Saida: SYNC/mapa_advbox/triagem_clientes.csv
=============================================================================
"""
import os
import io
import re
import csv
import json
import sys
from collections import Counter

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mapa_advbox')
CACHE = os.path.join(PASTA, 'cache')

# Termos institucionais, casados por PALAVRA INTEIRA.
ORGAOS = [
    'INSS', 'UNIAO', 'FEDERAL', 'FAZENDA', 'MUNICIPIO', 'PREFEITURA',
    'MINISTERIO', 'PUBLICO', 'DEFENSORIA', 'PROCURADORIA', 'INSTITUTO',
    'FUNDACAO', 'FUNDO', 'AUTARQUIA', 'EXERCITO', 'MARINHA', 'AERONAUTICA',
    'COMANDO', 'UFRJ', 'CIASPREV', 'FUNPRERJ', 'PREVIDENCIA',
]
EMPRESAS = [
    'BANCO', 'BRADESCO', 'SANTANDER', 'CAIXA', 'ECONOMICA', 'AGIBANK', 'BMG',
    'PAN', 'LIGHT', 'ENEL', 'CEMIG', 'AGUAS', 'PETROBRAS', 'AZUL', 'LATAM',
    'GOL', 'VIVO', 'CLARO', 'TIM', 'OI', 'TELEFONICA', 'AMIL', 'UNIMED',
    'HOSPITAL', 'SEGURADORA', 'SEGUROS', 'CONSORCIO', 'COOPERATIVA',
    'CONDOMINIO', 'SINDICATO', 'ASSOCIACAO', 'IMOBILIARIA', 'ADMINISTRADORA',
    'EMPREENDIMENTOS', 'COMERCIO', 'VEICULOS', 'BLINDADOS', 'CONSULTORIA',
    'SERVICOS', 'INSTALACOES', 'HABITACIONAL', 'ELETRICIDADE', 'ENERGIA',
    'LTDA', 'EIRELI', 'SPE', 'MEI',
]
# Sufixos societarios que aparecem soltos
SOCIETARIOS = [r'\bS/?\s?A\b', r'\bS\.A\.?\b', r'\bME\b', r'\bEPP\b']


def _sem_acento(t):
    import unicodedata
    s = unicodedata.normalize('NFKD', str(t or ''))
    return ''.join(c for c in s if not unicodedata.combining(c)).upper()


def _palavras(nome):
    return set(re.findall(r'[A-Z0-9]+', _sem_acento(nome)))


def _so_digitos(v):
    return re.sub(r'\D', '', str(v or ''))


def classificar(reg, n_processos):
    nome = reg.get('name') or ''
    pal = _palavras(nome)
    ident = _so_digitos(reg.get('identification'))
    tem_cnpj = bool(reg.get('cnpj')) or len(ident) == 14
    tem_cpf = len(ident) == 11
    contato = bool(reg.get('cellphone') or reg.get('phone') or reg.get('email'))

    achados = sorted((pal & set(ORGAOS)) | (pal & set(EMPRESAS)))
    nome_limpo = _sem_acento(nome)
    societario = [p for p in SOCIETARIOS if re.search(p, nome_limpo)]

    if tem_cnpj:
        return 'PARTE CONTRARIA', 'tem CNPJ'
    if achados:
        return 'PARTE CONTRARIA', 'nome contem %s' % ', '.join(achados[:3])
    if societario:
        return 'PARTE CONTRARIA', 'sufixo societario no nome'
    if n_processos >= 3:
        return 'DUVIDOSO', 'aparece em %d processos (pode ser parte recorrente)' % n_processos
    if not tem_cpf and not contato:
        return 'DUVIDOSO', 'cadastro sem CPF e sem contato - impossivel saber'
    return 'CLIENTE', 'pessoa fisica com %s' % ('CPF' if tem_cpf else 'contato')


def main():
    caminho_cli = os.path.join(CACHE, 'clientes.json')
    caminho_proc = os.path.join(CACHE, 'processos.json')
    if not os.path.exists(caminho_cli):
        print('Rode SYNC/mapear_advbox.py primeiro.')
        return 1

    clientes = json.load(io.open(caminho_cli, encoding='utf-8'))
    processos = json.load(io.open(caminho_proc, encoding='utf-8'))

    vezes = Counter()
    onde = {}
    for pid, p in processos.items():
        for c in (p.get('customers') or []):
            cid = str(c.get('customer_id'))
            vezes[cid] += 1
            onde.setdefault(cid, []).append(
                p.get('process_number') or p.get('folder') or ('proc %s' % pid))

    linhas = []
    resumo = Counter()
    for cid, reg in clientes.items():
        n = vezes.get(cid, 0)
        sugestao, motivo = classificar(reg, n)
        resumo[sugestao] += 1
        ident = reg.get('identification') or ''
        d = _so_digitos(ident)
        tipo_doc = 'CNPJ' if len(d) == 14 else ('CPF' if len(d) == 11 else '')
        linhas.append([
            '',                                   # DECISAO - a Dra. Fabiana marca
            sugestao, motivo, cid,
            reg.get('name') or '', ident, tipo_doc, n,
            'sim' if (reg.get('cellphone') or reg.get('phone')) else 'nao',
            'sim' if reg.get('email') else 'nao',
            reg.get('origin') or '',
            ' / '.join(onde.get(cid, [])[:3]),
        ])

    # Parte contraria primeiro (mais obvia de confirmar), depois duvidoso, depois cliente
    ordem = {'PARTE CONTRARIA': 0, 'DUVIDOSO': 1, 'CLIENTE': 2}
    linhas.sort(key=lambda l: (ordem[l[1]], -l[7], l[4]))

    destino = os.path.join(PASTA, 'triagem_clientes.csv')
    with io.open(destino, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['DECISAO (marque: CLIENTE / PARTE / IGNORAR)', 'sugestao', 'motivo',
                    'id_advbox', 'nome', 'documento', 'tipo_doc', 'n_processos',
                    'tem_telefone', 'tem_email', 'origem', 'processos_exemplo'])
        w.writerows(linhas)

    print('Triagem gravada em: %s' % destino)
    print()
    for k in ('PARTE CONTRARIA', 'DUVIDOSO', 'CLIENTE'):
        print('  %-16s %3d' % (k, resumo[k]))
    print('  %-16s %3d' % ('TOTAL', sum(resumo.values())))
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.exit(main())
