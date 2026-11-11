"""
Termos do monitor diario de acordaos do TCU (OPERACIONAL/monitor_tcu.py).

Cada tema e uma lista de expressoes regulares aplicadas ao texto do acordao
NORMALIZADO: minusculo, sem acento, espacos colapsados. Escrever os padroes
assim ("pensao militar", nao "Pensão Militar").

Acordao que nao bate em nenhum tema nem cita cliente e descartado sem gastar
API. Para incluir um assunto novo, acrescentar um tema aqui - nada mais muda.

Os clientes NAO ficam aqui: vem do snapshot do ADVBOX
(SYNC/espelhamento/snapshot.json, atualizado as 07:30) e, para quem ainda nao
esta no ADVBOX, de config/tcu_clientes_extra.txt (um nome por linha).
"""

TEMAS = {
    'Controle de legalidade de ato de pessoal militar': [
        r'pensao militar',
        r'reforma (?:de|do|da)? ?(?:militar|soldado|cabo|sargento|subtenente|oficial)',
        r'reserva remunerada',
        r'proventos? (?:de|da) (?:inatividade|reforma)',
        r'comando da (?:marinha|aeronautica)|comando do exercito',
        r'(?:ilegal|ilegalidade)[^.]{0,120}(?:pensao|reforma|reserva)',
        r'negar registro|negado o registro|recusa(?:r)? (?:de|do)? ?registro',
    ],
    'Habilitacao inicial / concessao inicial de pensao': [
        r'habilitacao (?:inicial|a pensao|de beneficiari)',
        r'concessao inicial',
        r'ato inicial de (?:pensao|reforma)',
        r'lei (?:n[o.]? )?3\.?765',
        r'(?:mp|medida provisoria) (?:n[o.]? )?2\.?215',
        r'contribuicao (?:especifica|adicional) de 1,5',
        r'filhas? (?:maior(?:es)?|solteira)',
        r'dependencia economica',
        r'acordao (?:n[o.]? )?2\.?225/2019',
        r'companheir[ao][^.]{0,80}(?:pensao|uniao estavel)',
        r'curatel|interdicao',
    ],
    'Cumulacao de duas aposentadorias com pensao militar': [
        r'(?:duas|dois|2) aposentadorias',
        r'(?:cumulacao|acumulacao|percepcao (?:simultanea|cumulativa))[^.]{0,160}(?:pensao|proventos|aposentadoria)',
        r'triplice (?:acumulacao|percepcao)',
        r'tres (?:beneficios|fontes)',
    ],
    'Cumulacao militar + professor / medico / saude': [
        r'(?:cargo|funcao) (?:de|publico de) (?:professor|magisterio)',
        r'(?:militar|oficial)[^.]{0,160}(?:professor|magisterio|medic[oa]|profissional de saude)',
        r'art(?:igo)?\.? 142,? (?:§|par\w*) ?3',
        r'(?:ec|emenda constitucional) (?:n[o.]? )?(?:77/2014|101/2019)',
        r'art(?:igo)?\.? 37,? (?:inciso )?xvi',
        r'acumulacao (?:licita|ilicita|de cargos)',
    ],
    'Fator redutor / abate-teto': [
        # "redutor" solto casava acordao de energia eletrica (Aneel): so perto de
        # verba de pessoal
        r'(?:fator (?:de )?redu(?:tor|cao)|redutor)[^.]{0,120}(?:pensao|proventos|remuneracao|aposentadoria|beneficio|teto)',
        r'(?:pensao|proventos|remuneracao|aposentadoria|beneficio)[^.]{0,120}(?:fator (?:de )?redu(?:tor|cao)|redutor)',
        r'art(?:igo)?\.? 24 da (?:ec|emenda constitucional) (?:n[o.]? )?103',
        r'abate[- ]teto|teto (?:constitucional|remuneratorio)',
        r'art(?:igo)?\.? 37,? (?:inciso )?xi\b',
        r'(?:tema|re) (?:n[o.]? )?(?:359|377|384|602\.?584|612\.?975)',
    ],
    'Decadencia, boa-fe e devolucao de valores': [
        r'tema (?:n[o.]? )?445',
        r'(?:re|recurso extraordinario) (?:n[o.]? )?636\.?553',
        r'sumula (?:tcu )?(?:n[o.]? )?(?:106|249|278)',
        r'boa[- ]fe[^.]{0,100}(?:dispensa|reposicao|devolucao|ressarcimento)',
        r'(?:dispensa|dispensad[ao]) (?:a |da )?(?:reposicao|devolucao)',
    ],
    'Isencao de IR por molestia grave': [
        r'molestia grave|doenca grave',
        r'art(?:igo)?\.? 6[o.]?,? (?:inciso )?xiv',
        r'isencao (?:de|do) (?:imposto de renda|irpf)',
    ],
}

# Expressoes que, sozinhas, indicam ato de pessoal - usadas para dizer se um
# acordao com cliente citado e ou nao de pessoal (cliente pode aparecer como
# responsavel em tomada de contas, que e outro assunto).
INDICIOS_ATO_PESSOAL = [
    r'pensao', r'reforma', r'aposentadoria', r'reserva remunerada', r'admissao',
    r'atos? de pessoal', r'para fins de registro',
]

# Nomes que nunca sao tratados como cliente, mesmo vindos do ADVBOX (parte
# contraria cadastrada como cliente, orgao publico, empresa).
NOMES_IGNORADOS = [
    r'\buniao\b', r'\binss\b', r'\binstituto\b', r'\bltda\b', r'\bs\.?a\.?$',
    r'\bmunicipio\b', r'\bestado do\b', r'\bfazenda\b', r'\bbanco\b',
    r'\bcomando\b', r'\bmarinha\b', r'\bexercito\b', r'\baeronautica\b',
    r'\bfundacao\b', r'\bassociacao\b', r'\bcondominio\b', r'\bme\b$', r'\beireli\b',
    r'\bministerio\b', r'\bpublico\b', r'\bfederal\b', r'\bcaixa\b', r'\bempresa\b',
    r'\bservico\b', r'\btribunal\b', r'\breceita\b', r'\bsecretaria\b', r'\bprefeitura\b',
    r'\bcompanhia\b', r'\bcia\b', r'\bsindicato\b', r'\bconselho\b', r'\buniversidade\b',
    r'\bhospital\b', r'\bprevidencia\b', r'\bseguro', r'\badvocacia\b', r'\bdefensoria\b',
    r'\bjustica\b', r'\bjuizo\b', r'\bclube\b', r'\bigreja\b', r'\bescola\b', r'\bcomercio\b',
    r'\bnacional\b', r'\bgoverno\b', r'\bagencia\b', r'\bautarquia\b',
]

# Palavras de nome que nao contam para o minimo de 2 palavras "de verdade"
# (evita casar "C O", "A P" - iniciais cadastradas no ADVBOX).
CONECTIVOS_NOME = {'de', 'da', 'do', 'das', 'dos', 'e'}
