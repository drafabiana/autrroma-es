"""
Integracao Google Drive/Docs/Sheets - Alves Carneiro Advocacia e Consultoria Jurídica.
"""
import os
import sys
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    # So ENVIO - nao le a caixa de entrada. Usado pelos relatorios de prazos e do
    # TCU quando SMTP_PASSWORD esta vazio (ver enviar_email_gmail()).
    'https://www.googleapis.com/auth/gmail.send',
]
GMAIL_SEND_SCOPE = 'https://www.googleapis.com/auth/gmail.send'
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config')
TOKEN_PATH = os.path.join(_CONFIG_DIR, 'token.json')


def gmail_disponivel():
    """True se o token OAuth salvo (config/token.json) tem permissao de envio do Gmail."""
    if not os.path.exists(TOKEN_PATH):
        return False
    try:
        import json
        with open(TOKEN_PATH, encoding='utf-8') as f:
            escopos = json.load(f).get('scopes') or []
        return GMAIL_SEND_SCOPE in escopos
    except Exception:
        return False


def enviar_email_gmail(msg):
    """
    Envia um email.message.EmailMessage pela API do Gmail, com o token ja salvo.

    Nunca abre navegador (roda em tarefa agendada): sem token valido, levanta erro
    com a instrucao de refazer o login (python INTEGRACOES/google_integration.py).
    O remetente e a conta Google do token; o Gmail ignora um From diferente que
    nao seja alias cadastrado.
    """
    import base64
    if not gmail_disponivel():
        raise RuntimeError('token sem permissao gmail.send - refaca o login: '
                           'python INTEGRACOES/google_integration.py')
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        else:
            raise RuntimeError('token do Google invalido - refaca o login: '
                               'python INTEGRACOES/google_integration.py')
    servico = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    bruto = base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii')
    return servico.users().messages().send(userId='me', body={'raw': bruto}).execute()

def autenticar_google():
    """
    Autentica com OAuth2 (conta pessoal do usuario) se oauth_credentials.json existir.
    Caso contrario, usa Service Account como fallback.
    """
    # Buscar credenciais na pasta config/ (raiz do projeto)
    project_root = os.path.join(os.path.dirname(__file__), '..')
    config_dir = os.path.join(project_root, 'config')
    oauth_creds_path = os.getenv("GOOGLE_OAUTH_CREDENTIALS", os.path.join(config_dir, "oauth_credentials.json"))
    token_path = os.path.join(config_dir, "token.json")
    sa_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", os.path.join(config_dir, "credentials.json"))

    creds = None

    # Tenta OAuth2 primeiro (conta pessoal - usa cota do usuario)
    if os.path.exists(oauth_creds_path):
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Renovando token de acesso...")
                creds.refresh(Request())
            else:
                print("Abrindo navegador para login com sua conta Google...")
                print("(isso so precisa ser feito uma vez)")
                flow = InstalledAppFlow.from_client_secrets_file(oauth_creds_path, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        print("Autenticado com sua conta Google pessoal!")

    # Fallback: Service Account
    elif os.path.exists(sa_creds_path):
        print("AVISO: Usando Service Account (cota limitada).")
        print("Para usar sua conta pessoal, configure oauth_credentials.json")
        creds = service_account.Credentials.from_service_account_file(
            sa_creds_path, scopes=SCOPES)
    else:
        print(f"ERRO: Nenhum arquivo de credenciais encontrado.")
        print("Coloque 'oauth_credentials.json' ou 'credentials.json' na pasta do projeto.")
        sys.exit(1)

    try:
        drive_service = build('drive', 'v3', credentials=creds)
        docs_service = build('docs', 'v1', credentials=creds)
        return drive_service, docs_service
    except Exception as e:
        print(f"ERRO DE AUTENTICACAO: {str(e)}")
        sys.exit(1)

def duplicar_template(drive_service, template_id: str, nome_cliente: str, data: str, pasta_destino_id: str = None) -> str:
    """
    Duplica o arquivo de template e o renomeia, mantendo na mesma pasta original
    ou enviando para uma pasta destino específica.
    """
    print("Gerando cópia do Template Ficha no Google Drive...")

    try:
        nome_arquivo = f"{nome_cliente} - Ficha Cliente - {data}"
        body = {
            'name': nome_arquivo,
            'mimeType': 'application/vnd.google-apps.document'
        }

        if pasta_destino_id:
            body['parents'] = [pasta_destino_id]
        else:
            arquivo_origem = drive_service.files().get(fileId=template_id, fields='parents').execute()
            if 'parents' in arquivo_origem:
                body['parents'] = arquivo_origem['parents']

        copia = drive_service.files().copy(
            fileId=template_id, body=body).execute()

        return copia.get('id')

    except HttpError as error:
        print(f"ERRO DE API DRIVE: Falha ao duplicar o arquivo.")
        print("Você compartilhou a pasta destino (ou o template original) com o email robô?")
        print(f"Detalhes técnicos: {error}")
        sys.exit(1)


def criar_pasta_cliente(drive_service, nome_cliente: str) -> str:
    """
    Cria a pasta do cliente dentro de RECLAMANTE com as 3 subpastas padrao:
    - ATOS INTERNOS
    - DOCUMENTOS DO CLIENTE
    - PASTA DO CLIENTE
    Retorna o ID da pasta principal criada.
    """
    pasta_reclamante_id = os.getenv("GOOGLE_PASTA_RECLAMANTE", "")
    if not pasta_reclamante_id:
        print("ERRO: GOOGLE_PASTA_RECLAMANTE nao configurado no .env (ID da pasta-mae no Drive).")
        return None

    nome_alvo = nome_cliente.upper().strip()
    MIME_DIR = 'application/vnd.google-apps.folder'

    try:
        # IDEMPOTENTE: rodar o intake de novo (falha no meio, reprocessamento)
        # nao pode criar uma segunda pasta com o mesmo nome. Com nome repetido,
        # quem arquiva documento (sync de assinados) nao sabe em qual gravar.
        escapado = nome_alvo.replace('\\', '\\\\').replace("'", "\\'")
        achadas = drive_service.files().list(
            q=(f"'{pasta_reclamante_id}' in parents and mimeType='{MIME_DIR}' "
               f"and trashed=false and name='{escapado}'"),
            fields='files(id, name, webViewLink)', pageSize=50).execute().get('files', [])
        if len(achadas) > 1:
            # caso ja sujo: fica com a que tem mais conteudo e NAO cria outra
            def _tamanho(fid):
                try:
                    return len(drive_service.files().list(
                        q=f"'{fid}' in parents and trashed=false",
                        fields='files(id)', pageSize=200).execute().get('files', []))
                except HttpError:
                    return 0
            achadas.sort(key=lambda f: _tamanho(f['id']), reverse=True)
            print(f"ATENCAO: {len(achadas)} pastas com o nome {nome_alvo}. "
                  f"Reuso a de id {achadas[0]['id']} (a com mais conteudo) e NAO crio outra. "
                  "Limpar as duplicadas a mao.")
        if achadas:
            pasta_id = achadas[0]['id']
            pasta_link = achadas[0].get('webViewLink', '')
            print(f"Pasta do cliente JA EXISTIA, reusando: {nome_alvo} ({pasta_id})")
        else:
            print(f"Criando pasta do cliente: {nome_cliente}...")
            pasta_cliente = drive_service.files().create(body={
                'name': nome_alvo,
                'mimeType': MIME_DIR,
                'parents': [pasta_reclamante_id]
            }, fields='id, webViewLink').execute()
            pasta_id = pasta_cliente['id']
            pasta_link = pasta_cliente.get('webViewLink', '')

        # Criar as 3 subpastas que faltarem (nunca duplicar subpasta)
        existentes = {f['name'].strip().upper() for f in drive_service.files().list(
            q=f"'{pasta_id}' in parents and mimeType='{MIME_DIR}' and trashed=false",
            fields='files(id, name)', pageSize=100).execute().get('files', [])}
        subpastas = ['ATOS INTERNOS', 'DOCUMENTOS DO CLIENTE', 'PASTA DO CLIENTE']
        for sub in subpastas:
            if sub in existentes:
                print(f"   Subpasta ja existia: {sub}")
                continue
            drive_service.files().create(body={
                'name': sub,
                'mimeType': MIME_DIR,
                'parents': [pasta_id]
            }).execute()
            print(f"   Subpasta criada: {sub}")

        print(f"Pasta do cliente pronta!")
        print(f"Link: {pasta_link}")
        return pasta_id

    except HttpError as error:
        print(f"ERRO ao criar pasta do cliente: {error}")
        return None


def buscar_proximo_contrato(drive_service, nome_cliente="", empresa="", area=""):
    """
    Busca o proximo numero sequencial de contrato na planilha de controle
    e registra o novo contrato na proxima linha.
    """
    import openpyxl
    import io
    from datetime import datetime
    from googleapiclient.http import MediaInMemoryUpload

    planilha_id = (os.getenv("GOOGLE_SHEETS_CONTRATOS_ID", "")
                   or os.getenv("GOOGLE_PLANILHA_CONTRATOS", ""))
    if not planilha_id:
        print("   Aviso: GOOGLE_SHEETS_CONTRATOS_ID nao configurado; pulando numeracao de contrato.")
        return ""

    # Ano da numeracao acompanha o ano corrente (era '2026' fixo e quebraria em
    # janeiro de 2027). A aba pode ser forcada por GOOGLE_ABA_CONTRATOS.
    ano_atual = str(datetime.now().year)
    aba_contratos = os.getenv("GOOGLE_ABA_CONTRATOS") or f"Contratos {ano_atual}"
    sufixo_ano = f'/{ano_atual}'

    try:
        content = drive_service.files().get_media(fileId=planilha_id).execute()
        wb = openpyxl.load_workbook(io.BytesIO(content))
        ws = wb[aba_contratos]

        # Encontrar ultimo numero e ultima linha preenchida
        ultimo = 0
        ultima_linha = 4
        for row in range(5, ws.max_row + 1):
            val = str(ws.cell(row=row, column=8).value or '')
            if sufixo_ano in val:
                try:
                    num = int(val.split('/')[0])
                    if num > ultimo:
                        ultimo = num
                        ultima_linha = row
                except:
                    pass

        proximo = ultimo + 1
        nova_linha = ultima_linha + 1
        numero_contrato = f"{proximo}{sufixo_ano}"

        # Preencher nova linha no padrao
        ws.cell(row=nova_linha, column=4, value=nome_cliente.upper())  # D: Nome
        ws.cell(row=nova_linha, column=6, value=datetime.now())  # F: Data cadastro
        ws.cell(row=nova_linha, column=8, value=numero_contrato)  # H: CT.
        ws.cell(row=nova_linha, column=9, value=empresa.upper())  # I: Parte contraria
        ws.cell(row=nova_linha, column=10, value=area)  # J: Area

        # Salvar e fazer upload de volta
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        media = MediaInMemoryUpload(
            buffer.read(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        drive_service.files().update(
            fileId=planilha_id,
            media_body=media
        ).execute()

        print(f"   Planilha atualizada: linha {nova_linha} - {nome_cliente.upper()} - {numero_contrato}")
        return f"CT. {numero_contrato}"

    except Exception as e:
        print(f"   Aviso: Nao conseguiu atualizar planilha: {e}")
        return ""


def gerar_documentos_cliente(drive_service, docs_service, nome_cliente: str,
                             dados: dict, numero_contrato: str = None):
    """
    Gera Contrato, Procuracao e Declaracao de Hipossuficiencia
    a partir dos templates, preenchendo com os dados do cliente.

    IDs de template e pasta de destino sao lidos de variaveis de ambiente
    (o escritorio configura os modelos proprios no Drive dele).

    numero_contrato: ao REFAZER um contrato, passar o numero original - assim
    nao se queima numero novo na planilha nem se troca o que o cliente ja viu.

    Cada item devolvido traz 'faltando' (marcadores/recados que sobraram no
    texto) e 'bloqueado' = True quando falta campo essencial. Ver
    documentos_prontos_para_assinatura().
    """
    from datetime import datetime

    templates = {
        'Contrato de Honorarios': {
            'template_id': os.getenv('GOOGLE_TEMPLATE_CONTRATO_ID', ''),
            'pasta_id': os.getenv('GOOGLE_PASTA_CONTRATO_ID', ''),
        },
        'Procuracao': {
            'template_id': os.getenv('GOOGLE_TEMPLATE_PROCURACAO_ID', ''),
            'pasta_id': os.getenv('GOOGLE_PASTA_PROCURACAO_ID', ''),
        },
        'Declaracao de Hipossuficiencia': {
            'template_id': os.getenv('GOOGLE_TEMPLATE_DECLARACAO_ID', ''),
            'pasta_id': os.getenv('GOOGLE_PASTA_DECLARACAO_ID', ''),
        },
    }

    hoje = datetime.now().strftime('%d de %B de %Y').replace(
        'January', 'Janeiro').replace('February', 'Fevereiro').replace(
        'March', 'Marco').replace('April', 'Abril').replace(
        'May', 'Maio').replace('June', 'Junho').replace(
        'July', 'Julho').replace('August', 'Agosto').replace(
        'September', 'Setembro').replace('October', 'Outubro').replace(
        'November', 'Novembro').replace('December', 'Dezembro')

    cidade_foro = os.getenv('CIDADE_FORO', 'Rio de Janeiro/RJ')
    data_local = f"{cidade_foro}, {hoje}"

    # Buscar numero sequencial do contrato
    empresa = dados.get('qual_empresa', dados.get('empresa', ''))
    if numero_contrato:
        print(f"   Numero do contrato (mantido do original): {numero_contrato}")
    else:
        numero_contrato = buscar_proximo_contrato(
            drive_service, nome_cliente, empresa, dados.get('area', ''))
        print(f"   Numero do contrato: {numero_contrato}")

    # Tratar endereco: remover prefixo de logradouro (Rua, Av, Avenida, etc.)
    # pois o template ja contem "Rua {{Endereco}}" / "residente ... a Rua {{Endereco}}"
    import re
    endereco_raw = dados.get('endereco', '')
    endereco_limpo = re.sub(r'^(Rua|Av\.?|Avenida|Alameda|Travessa|Estrada|Rodovia|R\.)\s+', '', endereco_raw, flags=re.IGNORECASE).strip()

    # Mapeamento das chaves dos templates para os dados extraidos
    mapa_chaves = {
        '{{Nome do cliente}}': dados.get('nome', ''),
        '{{Nome completo}}': dados.get('nome', ''),
        '{{CPF do cliente}}': dados.get('cpf', ''),
        '{{CPF}}': dados.get('cpf', ''),
        '{{RG do cliente}}': dados.get('rg', ''),
        '{{RG}}': dados.get('rg', ''),
        '{{Nacionalidade do cliente}}': dados.get('nacionalidade', ''),
        '{{Nacionalidade}}': dados.get('nacionalidade', ''),
        '{{Estado civil do cliente}}': dados.get('estado_civil', ''),
        '{{Estado Civil}}': dados.get('estado_civil', ''),
        '{{Profissão do cliente}}': dados.get('profissao', ''),
        '{{Profissão}}': dados.get('profissao', ''),
        '{{ENDEREÇO DO CLIENTE}}': endereco_limpo,
        '{{Endereço}}': endereco_limpo,
        '{{Bairro}}': dados.get('bairro', ''),
        '{{Cidade Estado}}': dados.get('cidade_estado', ''),
        '{{CEP}}': dados.get('cep', ''),
        '{{telefone do cliente}}': dados.get('telefone', ''),
        '{{e-mail do cliente}}': dados.get('email', ''),
        '{{NOME DA AÇÃO}}': dados.get('tipo_acao', ''),
        '{{NOME DA EMPRESA}}': dados.get('qual_empresa', ''),
        '{{nome da empresa}}': dados.get('qual_empresa', ''),
        '{{Data e local de hoje}}': data_local,
        '{{data e cidade}}': data_local,
        '{{ Número sequencial de contrato  EX: CT. N°.182/2024}}': numero_contrato,
    }

    docs_gerados = []

    for doc_nome, config in templates.items():
        print(f"   Gerando: {nome_cliente} - {doc_nome}...")

        try:
            nome_arquivo = f"{nome_cliente} - {doc_nome}"
            copia = drive_service.files().copy(
                fileId=config['template_id'],
                body={
                    'name': nome_arquivo,
                    'mimeType': 'application/vnd.google-apps.document',
                    'parents': [config['pasta_id']]
                }
            ).execute()

            doc_id = copia['id']

            # Preencher as chaves
            requests = []
            for chave, valor in mapa_chaves.items():
                if valor:
                    requests.append({
                        'replaceAllText': {
                            'containsText': {'text': chave, 'matchCase': False},
                            'replaceText': valor
                        }
                    })
                elif chave in CAMPOS_OPCIONAIS:
                    # opcional sem dado: tira o marcador e a virgula que sobraria
                    requests.extend(_apagar_campo_opcional(chave))

            if requests:
                docs_service.documents().batchUpdate(
                    documentId=doc_id, body={'requests': requests}).execute()

            # Confere o texto REAL do documento pronto (modelo editado a mao
            # pode ter ganhado campo que o codigo nao conhece).
            faltando = conferir_preenchimento(drive_service, doc_id)
            faltando += conferir_recados(drive_service, doc_id)
            doc = {'nome': nome_arquivo, 'id': doc_id, 'faltando': faltando}
            if faltando:
                doc['bloqueado'] = any(c in CAMPOS_ESSENCIAIS or str(c).startswith('[')
                                       for c in faltando)
                print(f"   ATENCAO: {nome_arquivo} ficou com campo em aberto: "
                      f"{', '.join(faltando)}")
            docs_gerados.append(doc)
            print(f"   Pronto: {nome_arquivo}")

        except HttpError as error:
            print(f"   ERRO ao gerar {doc_nome}: {error}")

    return docs_gerados


def preencher_documento(docs_service, document_id: str, dados: dict):
    """
    Edita um documento Google via Requests de BatchUpdate substituindo os placeholders
    {{CHAVE}} com os valores recém extraídos pela IA no dicionário.
    """
    print("Inserindo Fatos e Detalhes no novo documento gerado...")

    requests = []

    # Mapeamento do dicionário da IA com as Tags reais
    # Note que se a IA botou "FATOS" e "NOME_CLIENTE", vamos buscar "{{FATOS}}" no doc.
    for chave, valor in dados.items():
        if not isinstance(valor, str):
            # Se vier uma lista/dicionário maluco, converte
            valor = str(valor)

        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': f"{{{{{chave}}}}}",
                    'matchCase': True
                },
                'replaceText': valor
            }
        })

    try:
        resultado = docs_service.documents().batchUpdate(
            documentId=document_id, body={'requests': requests}).execute()
        print("Documento finalizado com Sucesso!!")

    except HttpError as error:
        print(f"ERRO DE API DOCS: Houve um erro ao formatar o texto do arquivo.")
        print(f"Detalhes: {error}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# TRAVA ANTI-MODELO
#
# Contrato, procuracao e declaracao sem o preambulo preenchido nao valem como
# titulo. Campo ESSENCIAL em aberto = o documento NAO vai para assinatura
# (zapsign_integration.enviar_para_zapsign pula o item com 'bloqueado').
# Campo OPCIONAL em aberto = o documento sai, mas o marcador some do texto
# junto com a pontuacao orfa, para o preambulo continuar legivel.
# ---------------------------------------------------------------------------

CAMPOS_ESSENCIAIS = {
    '{{Nome do cliente}}', '{{Nome completo}}',
    '{{CPF do cliente}}', '{{CPF}}',
    '{{RG do cliente}}', '{{RG}}',
    '{{ENDEREÇO DO CLIENTE}}', '{{Endereço}}',
    '{{Bairro}}', '{{Cidade Estado}}', '{{CEP}}',
    '{{telefone do cliente}}',
    '{{NOME DA AÇÃO}}',
    '{{NOME DA EMPRESA}}', '{{nome da empresa}}',
    '{{Nacionalidade do cliente}}', '{{Nacionalidade}}',
    '{{Profissão do cliente}}', '{{Profissão}}',
    '{{Data e local de hoje}}', '{{data e cidade}}',
    '{{ Número sequencial de contrato  EX: CT. N°.182/2024}}',
}

# So podem faltar sem barrar os campos que, no modelo, ficam ISOLADOS ENTRE
# VIRGULAS: da para tira-los sem quebrar a frase. Campo com texto-guia antes
# ("carteira de identidade de n° {{RG}}") NAO entra aqui - apagar so o
# marcador costuraria a frase errada.
CAMPOS_OPCIONAIS = {
    '{{Estado civil do cliente}}', '{{Estado Civil}}',
    '{{e-mail do cliente}}',
}


def _apagar_campo_opcional(chave):
    """Pedidos de batchUpdate que tiram o marcador E a pontuacao em volta.

    O preambulo e uma frase com virgulas ("brasileira, {{Estado civil}},
    pensionista"); trocar so o marcador por vazio deixaria ", ," no texto
    assinado. A ordem importa: as variantes com pontuacao vao primeiro.
    """
    return [
        {'replaceAllText': {'containsText': {'text': ', %s,' % chave, 'matchCase': False},
                            'replaceText': ','}},
        {'replaceAllText': {'containsText': {'text': ', %s' % chave, 'matchCase': False},
                            'replaceText': ''}},
        {'replaceAllText': {'containsText': {'text': '%s, ' % chave, 'matchCase': False},
                            'replaceText': ''}},
        {'replaceAllText': {'containsText': {'text': chave, 'matchCase': False},
                            'replaceText': ''}},
    ]


# Recado da automacao/IA que NUNCA pode aparecer no documento do cliente: o
# marcador foi substituido, mas por um texto que era para a equipe ler.
_RECADO_NO_DOCUMENTO = (
    "nao informado na transcricao", "não informado na transcrição",
    "nao informados na transcricao", "não informados na transcrição",
    "nao informada na transcricao", "não informada na transcrição",
    "nao identificada", "não identificada",
    "nao identificado", "não identificado",
    "necessario confirmar", "necessário confirmar",
    "a confirmar com o cliente", "verificar com o cliente",
    "grafia incerta", "ilegivel", "ilegível",
    "sobrenome nao informado", "sobrenome não informado",
)


def _texto_do_doc(drive_service, doc_id):
    """Texto puro do Google Doc (export text/plain). None se falhar."""
    try:
        texto = drive_service.files().export(
            fileId=doc_id, mimeType='text/plain').execute()
        if isinstance(texto, bytes):
            texto = texto.decode('utf-8', 'replace')
        return texto
    except Exception as e:
        print("   Aviso: nao consegui ler o documento %s para conferir: %s" % (doc_id, e))
        return None


def conferir_recados(drive_service, doc_id):
    """Recado da automacao dentro do documento pronto. Devolve achados no
    formato '[recado da automacao no documento: "..."]' (sempre barram)."""
    texto = _texto_do_doc(drive_service, doc_id)
    if texto is None:
        return []
    baixo = texto.lower()
    achados = []
    for marca in _RECADO_NO_DOCUMENTO:
        i = baixo.find(marca)
        if i >= 0:
            trecho = " ".join(texto[max(0, i - 60):i + len(marca) + 40].split())
            achados.append('[recado da automacao no documento: "%s"]' % trecho)
    return list(dict.fromkeys(achados))


def conferir_preenchimento(drive_service, doc_id):
    """Le o documento PRONTO e devolve os marcadores {{...}} que sobraram, mais
    as frases que ficaram sem o dado ("CPF sob nº ,").

    Le o texto de verdade, exportado do Drive, em vez de confiar na lista de
    campos mandada preencher: modelo alterado a mao pode ter campo novo.
    """
    import re as _re
    texto = _texto_do_doc(drive_service, doc_id)
    if texto is None:
        return []
    sobraram = list(dict.fromkeys(_re.findall(r'\{\{[^}]{0,120}\}\}', texto)))

    # FRASE COSTURADA ERRADO: o marcador sumiu mas o rotulo ficou pendurado.
    for costura in _re.findall(
            r'(?:de n[º°o]\.?|CPF sob n[º°o]\.?|RG\.?|Cep\.?|CEP:?|'
            r'Bairro:?|Cidade:?)\s*[,;]', texto):
        if not _re.search(r'\d', costura):
            sobraram.append('[frase sem o dado: "%s"]' % costura.strip())
            break
    return sobraram


def documentos_prontos_para_assinatura(docs_gerados):
    """(liberados, barrados). Barrado = campo essencial em aberto OU achado de
    texto (entre colchetes: frase sem o dado, recado da automacao)."""
    liberados, barrados = [], []
    for d in docs_gerados:
        graves = [c for c in d.get('faltando', [])
                  if c in CAMPOS_ESSENCIAIS or str(c).startswith('[')]
        (barrados if graves else liberados).append(d)
    return liberados, barrados


if __name__ == '__main__':
    # Login (uma vez, abre o navegador) + teste de conexao.
    #   python INTEGRACOES/google_integration.py
    # Refazer quando a lista SCOPES mudar: apague config/token.json antes.
    drive, _ = autenticar_google()
    usuario = drive.about().get(fields='user(emailAddress)').execute()['user']
    print('Drive OK - conta:', usuario['emailAddress'])
    print('Envio pelo Gmail:', 'liberado' if gmail_disponivel() else 'SEM permissao gmail.send')
