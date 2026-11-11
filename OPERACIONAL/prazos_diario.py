"""
=============================================================================
  RELATORIO DIARIO DE PRAZOS - ALVES CARNEIRO ADVOCACIA E CONSULTORIA JURIDICA
=============================================================================

  Roda todo dia as 9h (Agendador de Tarefas do Windows), consulta o ADVBOX e
  envia por e-mail a lista de prazos em aberto: os VENCIDOS primeiro, depois os
  que vencem hoje e os dos proximos 14 dias.

  Uso:
    python OPERACIONAL/prazos_diario.py                 # gera, salva e envia
    python OPERACIONAL/prazos_diario.py --sem-enviar    # so gera e salva (teste)
    python OPERACIONAL/prazos_diario.py --dias 30       # outro horizonte
    python OPERACIONAL/prazos_diario.py --sem-prazo     # inclui as sem data

  Somente leitura no ADVBOX - este script NAO conclui, cria nem altera tarefa.
  Concluir tarefa continua sendo ato humano no painel do ADVBOX (a API de
  /posts nao permite concluir).

  E-mail: configurar no config/.env (ver bloco "RELATORIO DIARIO DE PRAZOS").
  Sem SMTP configurado o relatorio e gerado e salvo normalmente, e o script
  avisa que nao enviou - nunca falha calado.
=============================================================================
"""
import os
import sys
import io
import ssl
import smtplib
import argparse
from email.message import EmailMessage
from datetime import date

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, 'INTEGRACOES'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(RAIZ, 'config', '.env'))

import prazos as mod_prazos

ESCRITORIO = os.getenv('ESCRITORIO_NOME', 'Alves Carneiro Advocacia e Consultoria Juridica')
PASTA_RELATORIOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'relatorios_prazos')

MESES = ['', 'janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho',
         'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']


def _data_extenso(d):
    return '%d de %s de %d' % (d.day, MESES[d.month], d.year)


# ============================================================
# TEXTO
# ============================================================

def montar_texto(dados, dias_adiante):
    hoje = dados['hoje']
    L = []
    L.append('=' * 72)
    L.append('  PRAZOS EM ABERTO - %s' % _data_extenso(hoje))
    L.append('  %s' % ESCRITORIO)
    L.append('=' * 72)
    L.append('')

    nv, nh, np_ = len(dados['vencidos']), len(dados['hoje_lista']), len(dados['proximos'])
    L.append('  RESUMO: %d prazo(s) em aberto' % dados['total'])
    L.append('    - vencidos .............. %d' % nv)
    L.append('    - vencem hoje ........... %d' % nh)
    L.append('    - proximos %2d dias ...... %d' % (dias_adiante, np_))
    if dados['sem_prazo']:
        L.append('    - pendentes SEM prazo ... %d' % len(dados['sem_prazo']))
    L.append('')

    if dados['total'] == 0:
        L.append('  Nenhum prazo em aberto na janela. Nada a fazer hoje.')
        L.append('')

    for titulo, chave in (('VENCIDOS - PRIORIDADE', 'vencidos'),
                          ('VENCEM HOJE', 'hoje_lista'),
                          ('PROXIMOS %d DIAS' % dias_adiante, 'proximos')):
        itens = dados[chave]
        if not itens:
            continue
        L.append('-' * 72)
        L.append('  %s (%d)' % (titulo, len(itens)))
        L.append('-' * 72)
        for i in itens:
            L.append('')
            L.append('  %s  (%s)%s' % (
                i['prazo'].strftime('%d/%m/%Y'),
                mod_prazos.descrever_dias(i['dias']),
                '  [URGENTE]' if i['urgente'] else ''))
            L.append('    Cliente ....: %s' % (i['cliente'] or '(sem cliente)'))
            if len(i['clientes']) > 1:
                L.append('    Demais partes: %s' % ', '.join(i['clientes'][1:]))
            L.append('    Tarefa .....: %s' % i['tarefa'])
            L.append('    Responsavel : %s' % ', '.join(i['responsaveis']))
            L.append('    Processo ...: %s' % (i['processo'] or 'S/N'))
            if i['notas']:
                for n, linha in enumerate(i['notas'].splitlines()):
                    if linha.strip():
                        L.append('    %s %s' % ('Anotacao ...:' if n == 0 else '             ', linha.strip()))
        L.append('')

    if dados['sem_prazo']:
        L.append('-' * 72)
        L.append('  PENDENTES SEM PRAZO (%d)' % len(dados['sem_prazo']))
        L.append('-' * 72)
        for i in dados['sem_prazo']:
            L.append('  %s | %-28s | %-26s | %s' % (
                i['criada'], i['tarefa'][:28], (i['cliente'] or '')[:26],
                i['notas'].replace('\n', ' ')[:60]))
        L.append('')

    L.append('=' * 72)
    L.append('  Fonte: ADVBOX (consulta somente leitura).')
    L.append('  Tarefa concluida some desta lista - concluir e ato humano no painel')
    L.append('  do ADVBOX; a API nao permite concluir tarefa.')
    L.append('=' * 72)
    return '\n'.join(L)


# ============================================================
# HTML
# ============================================================

def _esc(t):
    return (str(t or '').replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def montar_html(dados, dias_adiante):
    hoje = dados['hoje']
    nv, nh, np_ = len(dados['vencidos']), len(dados['hoje_lista']), len(dados['proximos'])

    H = []
    H.append('<html><body style="font-family:Segoe UI,Arial,sans-serif;'
             'font-size:14px;color:#1a1a1a;line-height:1.5;">')
    H.append('<h2 style="margin:0 0 2px 0;">Prazos em aberto</h2>')
    H.append('<div style="color:#666;font-size:13px;margin-bottom:4px;">%s</div>'
             % _esc(_data_extenso(hoje)))
    H.append('<div style="color:#666;font-size:12px;margin-bottom:16px;">%s</div>'
             % _esc(ESCRITORIO))

    H.append('<p style="margin:0 0 16px 0;"><strong>%d prazo(s) em aberto</strong> &mdash; '
             '<span style="color:#b00020;">%d vencido(s)</span>, '
             '%d vencendo hoje, %d nos proximos %d dias.</p>'
             % (dados['total'], nv, nh, np_, dias_adiante))

    if dados['total'] == 0:
        H.append('<p style="padding:12px;background:#eef7ee;border-left:4px solid #2e7d32;">'
                 'Nenhum prazo em aberto na janela. Nada a fazer hoje.</p>')

    blocos = (('Vencidos &mdash; prioridade', 'vencidos', '#b00020', '#fdecec'),
              ('Vencem hoje', 'hoje_lista', '#e65100', '#fff4e5'),
              ('Proximos %d dias' % dias_adiante, 'proximos', '#1565c0', '#e8f1fb'))

    for titulo, chave, cor, fundo in blocos:
        itens = dados[chave]
        if not itens:
            continue
        H.append('<h3 style="margin:22px 0 8px 0;color:%s;font-size:15px;">%s (%d)</h3>'
                 % (cor, titulo, len(itens)))
        H.append('<table cellpadding="7" cellspacing="0" border="0" '
                 'style="border-collapse:collapse;width:100%;font-size:13px;">')
        H.append('<tr style="background:%s;">'
                 '<th align="left" style="border-bottom:2px solid %s;">Prazo</th>'
                 '<th align="left" style="border-bottom:2px solid %s;">Cliente</th>'
                 '<th align="left" style="border-bottom:2px solid %s;">Tarefa</th>'
                 '<th align="left" style="border-bottom:2px solid %s;">Resp.</th></tr>'
                 % (fundo, cor, cor, cor, cor))
        for i in itens:
            detalhe = []
            if i['processo']:
                detalhe.append('Processo %s' % _esc(i['processo']))
            if len(i['clientes']) > 1:
                detalhe.append('Demais partes: %s' % _esc(', '.join(i['clientes'][1:])))
            if i['notas']:
                detalhe.append(_esc(i['notas'].replace('\n', ' &middot; ')))
            H.append('<tr style="border-bottom:1px solid #e6e6e6;vertical-align:top;">')
            H.append('<td><strong>%s</strong><br>'
                     '<span style="color:%s;font-size:12px;">%s</span>%s</td>'
                     % (i['prazo'].strftime('%d/%m/%Y'), cor,
                        _esc(mod_prazos.descrever_dias(i['dias'])),
                        '<br><span style="color:#b00020;font-size:11px;"><strong>URGENTE</strong></span>'
                        if i['urgente'] else ''))
            H.append('<td><strong>%s</strong></td>' % _esc(i['cliente'] or '(sem cliente)'))
            H.append('<td>%s%s</td>' % (
                _esc(i['tarefa']),
                ('<br><span style="color:#666;font-size:12px;">%s</span>'
                 % ' &middot; '.join(detalhe)) if detalhe else ''))
            H.append('<td>%s</td>' % _esc(', '.join(i['responsaveis'])))
            H.append('</tr>')
        H.append('</table>')

    if dados['sem_prazo']:
        H.append('<h3 style="margin:22px 0 8px 0;color:#555;font-size:15px;">'
                 'Pendentes sem prazo (%d)</h3><ul style="margin:0;padding-left:18px;">'
                 % len(dados['sem_prazo']))
        for i in dados['sem_prazo']:
            H.append('<li style="margin-bottom:3px;"><strong>%s</strong> &mdash; %s '
                     '<span style="color:#666;">(%s, desde %s)</span></li>'
                     % (_esc(i['cliente'] or '(sem cliente)'), _esc(i['tarefa']),
                        _esc(', '.join(i['responsaveis'])), _esc(i['criada'])))
        H.append('</ul>')

    H.append('<p style="margin-top:26px;color:#888;font-size:11px;border-top:1px solid #ddd;'
             'padding-top:10px;">Gerado automaticamente a partir do ADVBOX (consulta somente '
             'leitura). Tarefa concluida sai desta lista; concluir e ato humano no painel do '
             'ADVBOX, porque a API nao permite concluir tarefa.</p>')
    H.append('</body></html>')
    return '\n'.join(H)


# ============================================================
# WHATSAPP
# ============================================================
# Mensagem curta: o relatorio do e-mail nao cabe num WhatsApp (limite ~4096
# caracteres) e ninguem le tabela no celular. Aqui vai uma linha por prazo.

LIMITE_WHATSAPP = 3800   # margem sobre o limite real (~4096)


def montar_whatsapp(dados, dias_adiante):
    hoje = dados['hoje']
    nv = len(dados['vencidos'])

    L = []
    L.append('*PRAZOS EM ABERTO* - %s' % hoje.strftime('%d/%m/%Y'))
    if dados['total'] == 0:
        L.append('')
        L.append('Nenhum prazo em aberto. Nada a fazer hoje.')
        return '\n'.join(L)

    resumo = '%d em aberto' % dados['total']
    if nv:
        resumo += ' | %d VENCIDO%s' % (nv, 'S' if nv > 1 else '')
    L.append(resumo)

    for titulo, chave in (('VENCIDOS', 'vencidos'),
                          ('VENCEM HOJE', 'hoje_lista'),
                          ('PROXIMOS %d DIAS' % dias_adiante, 'proximos')):
        itens = dados[chave]
        if not itens:
            continue
        L.append('')
        L.append('*%s (%d)*' % (titulo, len(itens)))
        for i in itens:
            marca = ' !' if i['urgente'] else ''
            L.append('')
            L.append('%s (%s)%s' % (i['prazo'].strftime('%d/%m'),
                                    mod_prazos.descrever_dias(i['dias']), marca))
            L.append('%s' % (i['cliente'] or '(sem cliente)'))
            L.append('%s - %s' % (i['tarefa'], ', '.join(
                n.split()[0] for n in i['responsaveis'] if n)))
            if i['notas']:
                nota = ' '.join(i['notas'].split())
                L.append('_%s_' % (nota[:110] + ('...' if len(nota) > 110 else '')))

    texto = '\n'.join(L)
    if len(texto) > LIMITE_WHATSAPP:
        texto = (texto[:LIMITE_WHATSAPP].rsplit('\n', 1)[0]
                 + '\n\n_(lista truncada - relatorio completo no e-mail)_')
    return texto


def _config_whatsapp():
    numero = (os.getenv('PRAZOS_WHATSAPP_PARA', '').strip()
              or os.getenv('ESCRITORIO_TELEFONE', '').strip())
    token = os.getenv('ATENDE_DIREITO_TOKEN', '').strip()
    faltando = []
    if not token:
        faltando.append('ATENDE_DIREITO_TOKEN')
    if not numero:
        faltando.append('PRAZOS_WHATSAPP_PARA')
    return numero, faltando


def enviar_whatsapp(texto, numero):
    """Envia via Atende Direito. Devolve (ok, detalhe)."""
    import atendedireito_integration as ad_wpp
    ok, contato = ad_wpp.enviar_texto_por_telefone(numero, texto)
    if ok:
        return True, numero
    # O Atende Direito manda para CONTATO existente (subscriber). Se o numero
    # nao estiver cadastrado la, nao ha user_ns e o envio nao sai.
    if not contato:
        return False, ('numero %s nao encontrado como contato no Atende Direito '
                       '- cadastrar lá primeiro' % numero)
    return False, 'Atende Direito recusou o envio para %s' % numero


# ============================================================
# E-MAIL
# ============================================================

def _config_smtp():
    cfg = {
        'host': os.getenv('SMTP_HOST', '').strip(),
        'port': os.getenv('SMTP_PORT', '587').strip(),
        'user': os.getenv('SMTP_USER', '').strip(),
        'senha': os.getenv('SMTP_PASSWORD', '').strip(),
        'seguranca': (os.getenv('SMTP_SEGURANCA', 'starttls').strip() or 'starttls').lower(),
        'de': (os.getenv('SMTP_REMETENTE', '').strip()
               or os.getenv('SMTP_USER', '').strip()),
        'para': (os.getenv('PRAZOS_EMAIL_PARA', '').strip()
                 or os.getenv('ESCRITORIO_EMAIL_RESPONSAVEL', '').strip()),
    }
    # Sem senha SMTP, envia pela API do Gmail com o login OAuth do Google
    # (config/token.json com permissao gmail.send). Senha SMTP preenchida tem
    # precedencia.
    cfg['via'] = 'smtp'
    if not cfg['senha']:
        try:
            from google_integration import gmail_disponivel
            if gmail_disponivel():
                cfg['via'] = 'gmail_api'
        except Exception:
            pass
    obrigatorios = ('host', 'user', 'senha', 'para') if cfg['via'] == 'smtp' else ('para',)
    faltando = [k for k in obrigatorios if not cfg[k]]
    return cfg, faltando


def enviar_email(assunto, texto, html, cfg):
    msg = EmailMessage()
    msg['Subject'] = assunto
    msg['From'] = cfg['de']
    destinos = [e.strip() for e in cfg['para'].replace(';', ',').split(',') if e.strip()]
    msg['To'] = ', '.join(destinos)
    msg.set_content(texto)
    msg.add_alternative(html, subtype='html')

    if cfg.get('via') == 'gmail_api':
        from google_integration import enviar_email_gmail
        if not cfg['de']:
            del msg['From']   # o Gmail preenche com a conta do token
        enviar_email_gmail(msg)
        return destinos

    porta = int(cfg['port'] or 587)
    if cfg['seguranca'] == 'ssl':
        with smtplib.SMTP_SSL(cfg['host'], porta, context=ssl.create_default_context(),
                              timeout=60) as s:
            s.login(cfg['user'], cfg['senha'])
            s.send_message(msg, to_addrs=destinos)
    else:
        with smtplib.SMTP(cfg['host'], porta, timeout=60) as s:
            s.ehlo()
            if cfg['seguranca'] != 'nenhuma':
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
            s.login(cfg['user'], cfg['senha'])
            s.send_message(msg, to_addrs=destinos)
    return destinos


# ============================================================
# MAIN
# ============================================================

def main():
    ap = argparse.ArgumentParser(description='Relatorio diario de prazos em aberto (ADVBOX)')
    ap.add_argument('--dias', type=int, default=mod_prazos.DIAS_ADIANTE,
                    help='horizonte futuro em dias (padrao: 14)')
    ap.add_argument('--sem-enviar', action='store_true',
                    help='gera e salva, mas nao envia nada')
    ap.add_argument('--sem-prazo', action='store_true',
                    help='inclui tambem as tarefas pendentes sem data de prazo')
    ap.add_argument('--canal', choices=('email', 'whatsapp', 'ambos'), default=None,
                    help='canal de envio; o padrao vem de PRAZOS_ENVIO no .env')
    args = ap.parse_args()

    canal = (args.canal or os.getenv('PRAZOS_ENVIO', 'ambos').strip().lower())
    if canal not in ('email', 'whatsapp', 'ambos'):
        canal = 'ambos'

    print('Consultando prazos em aberto no ADVBOX...')
    dados = mod_prazos.coletar(dias_adiante=args.dias, incluir_sem_prazo=args.sem_prazo)

    texto = montar_texto(dados, args.dias)
    html = montar_html(dados, args.dias)
    print()
    print(texto)

    # Copia em arquivo (um por dia; reexecucao no mesmo dia sobrescreve)
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    caminho = os.path.join(PASTA_RELATORIOS,
                           'prazos-%s.txt' % dados['hoje'].strftime('%Y-%m-%d'))
    with io.open(caminho, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto + '\n')
    print('\n  Copia salva em: %s' % caminho)

    nv = len(dados['vencidos'])
    assunto = 'Prazos em aberto - %s - %d em aberto%s' % (
        dados['hoje'].strftime('%d/%m/%Y'), dados['total'],
        ' (%d VENCIDO%s)' % (nv, 'S' if nv > 1 else '') if nv else '')

    if args.sem_enviar:
        print('  --sem-enviar: nada enviado.')
        print('  Assunto que seria usado: %s' % assunto)
        print('\n  --- previa da mensagem de WhatsApp ---')
        print(montar_whatsapp(dados, args.dias))
        return 0

    falhas = []
    entregue = False

    # ---- WhatsApp ----
    if canal in ('whatsapp', 'ambos'):
        numero, faltando = _config_whatsapp()
        if faltando:
            print('\n  AVISO: WhatsApp NAO enviado - falta no config/.env: %s'
                  % ', '.join(faltando))
        else:
            try:
                ok, detalhe = enviar_whatsapp(montar_whatsapp(dados, args.dias), numero)
                if ok:
                    print('\n  WhatsApp enviado para: %s' % detalhe)
                    entregue = True
                else:
                    print('\n  FALHA no WhatsApp: %s' % detalhe)
                    falhas.append('whatsapp')
            except Exception as e:
                print('\n  ERRO no WhatsApp: %s: %s' % (type(e).__name__, e))
                falhas.append('whatsapp')

    # ---- E-mail ----
    if canal in ('email', 'ambos'):
        cfg, faltando = _config_smtp()
        if faltando:
            # Nomear a variavel EXATA do .env - nome aproximado faz criar a
            # variavel errada e o envio continua sem funcionar.
            rotulos = {'host': 'SMTP_HOST', 'user': 'SMTP_USER',
                       'senha': 'SMTP_PASSWORD', 'para': 'PRAZOS_EMAIL_PARA'}
            print('\n  AVISO: e-mail NAO enviado - falta no config/.env: %s'
                  % ', '.join(rotulos[f] for f in faltando))
        else:
            try:
                destinos = enviar_email(assunto, texto, html, cfg)
                print('\n  E-mail enviado para: %s' % ', '.join(destinos))
            except Exception as e:
                print('\n  ERRO ao enviar e-mail: %s: %s' % (type(e).__name__, e))
                falhas.append('email')

    if falhas:
        print('\n  O relatorio esta salvo em %s - nada foi perdido.' % caminho)
        return 1
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.exit(main())
