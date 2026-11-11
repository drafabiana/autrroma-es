"""
Integracao unificada com ZapSign - assinatura digital.

Funcoes disponiveis:
  Baixo nivel:
    get_zapsign_headers()
    exportar_google_doc_pdf(drive, doc_id)
    pdf_bytes_para_base64(pdf_bytes)
    normalizar_telefone(tel)
    criar_signatario(nome, email, telefone, auth_mode)

  Alto nivel - criacao:
    criar_documento(nome, pdf_base64, signers, folder_path, external_id) -> dict
    enviar_documento(drive, doc_id, signers, folder_path) -> dict
    enviar_para_zapsign(drive, nome_cliente, docs_gerados, dados_cliente) -> list[link]
      (compat INTAKE/COMERCIAL)

  Alto nivel - consulta/download:
    listar_documentos(status='signed', page=1) -> (docs, has_next)
    buscar_documento(token) -> dict
    listar_signatarios_documento(doc_token) -> list
    baixar_pdf_assinado(url_signed_file) -> bytes

  Sincronizacao:
    sincronizar_assinados_para_drive(drive, log_path, buscar_pasta_cliente_fn)
      -> dict com resumo (novos, ja_sincronizados, erros)

  Manutencao de documento pendente (escrevem no ZapSign - so com pedido explicito):
    atualizar_signatario(signer_token, **campos) -> (ok, resposta)
    reenviar_notificacoes(doc_token) -> (ok, resposta)
    signatarios_pendentes(doc_token) -> list   (somente leitura)

Endpoints ZapSign:
  POST /api/v1/docs/            criar doc
  GET  /api/v1/docs/?page=N     listar docs
  GET  /api/v1/docs/{token}/    buscar doc

Auth: Bearer token via ZAPSIGN_API_TOKEN (.env).
"""
import os
import sys
import json
import time
import base64
import logging
import requests

log = logging.getLogger('integracoes.zapsign')

ZAPSIGN_BASE = 'https://api.zapsign.com.br/api/v1'


# ============================================================
# BAIXO NIVEL
# ============================================================

def get_zapsign_headers():
    """Retorna headers Bearer. Fails hard se o token nao estiver setado."""
    token = os.getenv('ZAPSIGN_API_TOKEN')
    if not token:
        print('ERRO: ZAPSIGN_API_TOKEN nao encontrado no .env')
        sys.exit(1)
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


def exportar_google_doc_pdf(drive_service, doc_id):
    """Exporta um Google Doc como PDF e retorna os bytes."""
    return drive_service.files().export(
        fileId=doc_id, mimeType='application/pdf'
    ).execute()


def pdf_bytes_para_base64(pdf_bytes):
    """Converte bytes de PDF em string base64 pronta pra API."""
    return base64.b64encode(pdf_bytes).decode('utf-8')


def normalizar_telefone(tel):
    """Retorna so digitos do telefone, removendo DDI 55 inicial."""
    if not tel:
        return ''
    d = ''.join(c for c in str(tel) if c.isdigit())
    if d.startswith('55') and len(d) > 11:
        d = d[2:]
    return d


# Modo de autenticacao padrao do signatario. Pode ser trocado sem mexer no codigo
# por ZAPSIGN_AUTH_MODE no config/.env. Valores aceitos pela API: 'assinaturaTela',
# 'tokenWhatsapp' (so o codigo, sem desenho - plano B de quem trava na tela),
# 'assinaturaTela-tokenWhatsapp' (desenho + codigo por WhatsApp, que chega com mais
# confianca que o SMS), 'tokenSms', 'assinaturaTela-tokenSms', 'certificadoDigital'.
MODO_ASSINATURA_PADRAO = 'assinaturaTela'


def criar_signatario(nome, email=None, telefone=None, auth_mode=None,
                     send_email=None, send_whatsapp=None):
    """
    Monta um dict de signatario para a API do ZapSign.

    auth_mode: None = ZAPSIGN_AUTH_MODE do .env, senao 'assinaturaTela'.
               Tambem aceita 'certificadoDigital', 'tokenWhatsapp' etc.
    send_email / send_whatsapp: None = autodetecta pelos dados; True/False sobrescreve.
    """
    auth_mode = auth_mode or os.getenv('ZAPSIGN_AUTH_MODE') or MODO_ASSINATURA_PADRAO
    tel = normalizar_telefone(telefone) or None
    em = email or None
    return {
        'name': nome,
        'email': em,
        'phone_country': '55',
        'phone_number': tel,
        'auth_mode': auth_mode,
        'send_automatic_email': bool(em) if send_email is None else send_email,
        'send_automatic_whatsapp': bool(tel) if send_whatsapp is None else send_whatsapp,
    }


# ============================================================
# ALTO NIVEL - CRIACAO
# ============================================================

def criar_documento(nome, pdf_base64, signers, folder_path='/', external_id='',
                    lang='pt-br'):
    """
    Cria documento no ZapSign a partir de PDF base64.

    signers: lista de dicts no formato criar_signatario()
    Retorna dict com:
        token       - token unico do doc
        doc_url     - link pro painel do ZapSign
        sign_urls   - list[{'signatario','link','token'}]
        raw         - resposta completa
    """
    headers = get_zapsign_headers()
    payload = {
        'name': nome,
        'url_pdf': '',
        'base64_pdf': pdf_base64,
        'external_id': external_id,
        'signers': signers,
        'folder_path': folder_path,
        'lang': lang,
    }
    r = requests.post(f'{ZAPSIGN_BASE}/docs/', headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    result = r.json()

    sign_urls = []
    for s in result.get('signers') or []:
        sign_urls.append({
            'signatario': s.get('name'),
            'link': s.get('sign_url'),
            'token': s.get('token'),
            'email': s.get('email'),
            'phone_number': s.get('phone_number'),
        })

    token = result.get('token', '')
    return {
        'token': token,
        'doc_url': f'https://app.zapsign.com.br/cli/docs/{token}' if token else None,
        'sign_urls': sign_urls,
        'raw': result,
    }


def enviar_documento(drive_service, doc_id, signers, folder_path='/', external_id=''):
    """
    Atalho: exporta um Google Doc (ou baixa um PDF do Drive) e cria no ZapSign.
    Retorna o mesmo dict de criar_documento() + nome_doc.
    """
    meta = drive_service.files().get(
        fileId=doc_id, fields='name,mimeType', supportsAllDrives=True
    ).execute()
    nome = meta['name']
    mime = meta['mimeType']

    if mime == 'application/vnd.google-apps.document':
        pdf_bytes = exportar_google_doc_pdf(drive_service, doc_id)
    else:
        import io
        from googleapiclient.http import MediaIoBaseDownload
        buf = io.BytesIO()
        req = drive_service.files().get_media(fileId=doc_id, supportsAllDrives=True)
        dl = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
        pdf_bytes = buf.getvalue()

    out = criar_documento(
        nome=nome,
        pdf_base64=pdf_bytes_para_base64(pdf_bytes),
        signers=signers,
        folder_path=folder_path,
        external_id=external_id,
    )
    out['nome_doc'] = nome
    return out


def enviar_para_zapsign(drive_service, nome_cliente, docs_gerados, dados_cliente):
    """
    COMPAT: assinatura original usada por INTAKE/main.py e COMERCIAL/main.py.

    Envia Contrato (2 signers: cliente + advogado responsavel), Procuracao e
    Declaracao (1 signer: cliente). Retorna list[{'documento','signatario','link'}].

    O segundo signatario do contrato (advogado responsavel) e lido das variaveis
    de ambiente ADVOGADO_RESPONSAVEL_NOME e ADVOGADO_RESPONSAVEL_EMAIL.
    """
    nome = dados_cliente.get('nome', nome_cliente)
    email = dados_cliente.get('email', '')
    telefone = dados_cliente.get('telefone', '')

    print(f'\n8. Enviando documentos para ZapSign...')
    links = []

    advogado_nome = os.getenv('ADVOGADO_RESPONSAVEL_NOME', '')
    advogado_email = os.getenv('ADVOGADO_RESPONSAVEL_EMAIL', '')

    for doc in docs_gerados:
        doc_nome = doc['nome']
        doc_id = doc['id']
        up = doc_nome.upper()

        is_contrato = 'CONTRATO' in up
        is_procuracao = 'PROCURAC' in up
        is_declaracao = 'DECLARAC' in up
        if not (is_contrato or is_procuracao or is_declaracao):
            continue

        # Trava anti-modelo (google_integration.gerar_documentos_cliente marca
        # 'bloqueado' quando sobra campo essencial do modelo ou recado da
        # automacao no texto). Documento sem preambulo completo nao vale como
        # titulo e nao vai para o cliente assinar.
        if doc.get('bloqueado'):
            print(f'   BARRADO (nao enviado): {doc_nome} - campo em aberto: '
                  f'{", ".join(doc.get("faltando") or [])}')
            continue

        print(f'   Enviando: {doc_nome}...')
        signatarios = [criar_signatario(nome, email, telefone)]
        if is_contrato and advogado_nome:
            signatarios.append(criar_signatario(
                advogado_nome,
                advogado_email or None,
            ))

        try:
            out = enviar_documento(
                drive_service=drive_service,
                doc_id=doc_id,
                signers=signatarios,
                folder_path=f'/{nome_cliente.upper()}/',
            )
            for s in out['sign_urls']:
                if s['link']:
                    links.append({
                        'documento': doc_nome,
                        'signatario': s['signatario'],
                        'link': s['link'],
                    })
            print('   Enviado com sucesso!')
        except Exception as e:
            print(f'   ERRO ao enviar {doc_nome}: {e}')

        time.sleep(1)

    return links


# ============================================================
# ALTO NIVEL - CONSULTA / DOWNLOAD
# ============================================================

def listar_documentos(status=None, page=1):
    """
    Lista documentos do ZapSign (paginado).

    status: se informado ('signed', 'pending', 'refused'), filtra em memoria.
    Retorna (list_docs, has_next).
    """
    headers = get_zapsign_headers()
    r = requests.get(f'{ZAPSIGN_BASE}/docs/?page={page}', headers=headers, timeout=30)
    if r.status_code != 200:
        log.warning(f'listar_documentos HTTP {r.status_code}: {r.text[:200]}')
        return [], False
    data = r.json()
    docs = data.get('results') or []
    if status:
        docs = [d for d in docs if d.get('status') == status]
    has_next = bool(data.get('next'))
    return docs, has_next


def buscar_documento(token):
    """GET /docs/{token}/ - retorna o doc completo."""
    headers = get_zapsign_headers()
    r = requests.get(f'{ZAPSIGN_BASE}/docs/{token}/', headers=headers, timeout=30)
    if r.status_code != 200:
        log.warning(f'buscar_documento {token} HTTP {r.status_code}: {r.text[:200]}')
        return None
    return r.json()


def listar_signatarios_documento(doc_token):
    """Retorna lista de signatarios com status de assinatura."""
    doc = buscar_documento(doc_token)
    if not doc:
        return []
    return doc.get('signers') or []


def baixar_pdf_assinado(signed_file_url):
    """Baixa o PDF final assinado. Retorna bytes ou None."""
    try:
        r = requests.get(signed_file_url, timeout=120)
        if r.status_code == 200:
            return r.content
    except Exception as e:
        log.warning(f'falha ao baixar pdf assinado: {e}')
    return None


# ============================================================
# SINCRONIZACAO ZAPSIGN -> DRIVE
# ============================================================

def sincronizar_assinados_para_drive(drive_service, log_path, buscar_pasta_cliente_fn,
                                     max_paginas=20):
    """
    Percorre documentos assinados no ZapSign e salva o PDF na pasta do cliente no Drive.

    drive_service: drive autenticado (do google_integration.autenticar_google)
    log_path: caminho do JSON que rastreia tokens ja sincronizados
    buscar_pasta_cliente_fn: callable(drive, nome_cliente) -> pasta_id (ou None)
    max_paginas: limite de paginas do ZapSign a percorrer

    Retorna dict:
        {'novos': int, 'ja_sincronizados': int, 'ignorados': int, 'erros': list, 'itens_novos': list}
    """
    from googleapiclient.http import MediaInMemoryUpload

    # carregar / iniciar log
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            try:
                sync_log = json.load(f)
            except Exception:
                sync_log = {'sincronizados': []}
    else:
        sync_log = {'sincronizados': []}
    sincronizados = set(sync_log.get('sincronizados') or [])

    resumo = {'novos': 0, 'ja_sincronizados': 0, 'ignorados': 0,
              'erros': [], 'itens_novos': []}

    for page in range(1, max_paginas + 1):
        docs, has_next = listar_documentos(status='signed', page=page)
        if not docs:
            break

        for doc in docs:
            token = doc.get('token', '')
            nome_doc = doc.get('name', '')
            signed_file = doc.get('signed_file', '')
            folder_path = doc.get('folder_path', '') or ''

            if token in sincronizados:
                resumo['ja_sincronizados'] += 1
                continue
            if not signed_file:
                resumo['ignorados'] += 1
                continue

            nome_cliente = folder_path.strip('/').strip()
            if not nome_cliente and ' - ' in nome_doc:
                nome_cliente = nome_doc.split(' - ')[0].strip()
            if not nome_cliente:
                resumo['ignorados'] += 1
                resumo['erros'].append(f'{nome_doc}: sem cliente identificavel')
                continue

            pasta_id = None
            try:
                pasta_id = buscar_pasta_cliente_fn(drive_service, nome_cliente)
            except Exception as e:
                resumo['erros'].append(f'{nome_doc}: erro pasta cliente: {e}')
            if not pasta_id:
                resumo['ignorados'] += 1
                resumo['erros'].append(f'{nome_doc}: pasta de "{nome_cliente}" nao encontrada')
                continue

            nome_arquivo = f'{nome_doc} (ASSINADO).pdf'
            # Memoria do log perdida (log apagado, outro log_path) nao pode
            # duplicar o PDF na pasta do cliente: confere o nome antes de subir.
            try:
                escapado = nome_arquivo.replace('\\', '\\\\').replace("'", "\\'")
                existentes = drive_service.files().list(
                    q=f"'{pasta_id}' in parents and trashed=false and name='{escapado}'",
                    fields='files(id)', pageSize=1,
                    supportsAllDrives=True, includeItemsFromAllDrives=True,
                ).execute().get('files', [])
            except Exception:
                existentes = []
            if existentes:
                sincronizados.add(token)
                resumo['ja_sincronizados'] += 1
                continue

            pdf_bytes = baixar_pdf_assinado(signed_file)
            if not pdf_bytes:
                resumo['erros'].append(f'{nome_doc}: falha download PDF')
                continue

            try:
                media = MediaInMemoryUpload(pdf_bytes, mimetype='application/pdf')
                drive_service.files().create(
                    body={'name': nome_arquivo, 'parents': [pasta_id]},
                    media_body=media,
                    supportsAllDrives=True,
                ).execute()
                sincronizados.add(token)
                resumo['novos'] += 1
                resumo['itens_novos'].append({
                    'nome_doc': nome_doc,
                    'nome_cliente': nome_cliente,
                    'pasta_id': pasta_id,
                    'token': token,
                })
            except Exception as e:
                resumo['erros'].append(f'{nome_doc}: erro upload Drive: {e}')

        if not has_next:
            break

    # salvar log
    try:
        sync_log['sincronizados'] = sorted(sincronizados)
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(sync_log, f, ensure_ascii=False, indent=2)
    except Exception as e:
        resumo['erros'].append(f'erro ao salvar log: {e}')

    return resumo


# ============================================================
# MANUTENCAO DE DOCUMENTO PENDENTE
# (escrevem no ZapSign: so chamar com pedido explicito)
# ============================================================

def atualizar_signatario(signer_token, **campos):
    """
    Altera o cadastro de um signatario que AINDA NAO ASSINOU.
    POST /signers/{token}/

    Uso tipico: trocar o auth_mode de quem trava na tela de desenho (para
    'tokenWhatsapp', so o codigo) ou preencher o telefone de um documento que
    nasceu sem ele - caso em que o cliente nunca e avisado.

    Campos aceitos pela API: name, email, phone_country, phone_number, auth_mode,
    lock_name, lock_email, lock_phone, qualification, external_id,
    send_automatic_whatsapp, send_automatic_email, require_cpf, cpf,
    validate_cpf, redirect_link, entre outros.

    Retorna (ok, resposta).
    """
    url = f'{ZAPSIGN_BASE}/signers/{signer_token}/'
    try:
        r = requests.post(url, headers=get_zapsign_headers(), json=campos, timeout=60)
    except requests.RequestException as e:
        log.warning(f'atualizar_signatario {signer_token}: {e}')
        return False, {'erro': str(e)}
    ok = r.status_code in (200, 201)
    if not ok:
        log.warning(f'atualizar_signatario {signer_token}: {r.status_code} {r.text[:200]}')
    try:
        return ok, r.json()
    except ValueError:
        return ok, {'status_code': r.status_code, 'texto': r.text[:300]}


def reenviar_notificacoes(doc_token):
    """
    Reenvia o aviso de assinatura a TODOS os signatarios pendentes do documento.
    POST /docs/{token}/resend-notifications-bulk/

    Quem ja assinou nao recebe nada. A API devolve 429 com 'cooldown_period'
    quando houve reenvio recente - nao e erro, e so aguardar.

    Retorna (ok, resposta); a resposta traz sent_count e failed_signers.
    """
    url = f'{ZAPSIGN_BASE}/docs/{doc_token}/resend-notifications-bulk/'
    try:
        r = requests.post(url, headers=get_zapsign_headers(), json={}, timeout=60)
    except requests.RequestException as e:
        log.warning(f'reenviar_notificacoes {doc_token}: {e}')
        return False, {'erro': str(e)}
    ok = r.status_code in (200, 201)
    if not ok:
        log.warning(f'reenviar_notificacoes {doc_token}: {r.status_code} {r.text[:200]}')
    try:
        return ok, r.json()
    except ValueError:
        return ok, {'status_code': r.status_code, 'texto': r.text[:300]}


def signatarios_pendentes(doc_token):
    """
    Lista quem AINDA NAO assinou o documento (somente leitura).
    Retorna list[{'nome','token','status','link'}].
    """
    pendentes = []
    for s in listar_signatarios_documento(doc_token):
        if s.get('status') != 'signed':
            pendentes.append({
                'nome': s.get('name'),
                'token': s.get('token'),
                'status': s.get('status'),
                'link': s.get('sign_url'),
            })
    return pendentes
