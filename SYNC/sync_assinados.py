"""
Sincronizador ZapSign -> Google Drive
Verifica documentos assinados no ZapSign e salva na pasta do cliente no Drive.
Rodar 3x ao dia via cron/launchd (macOS/Linux) - ver sync_assinados.sh.

Alves Carneiro Advocacia e Consultoria Jurídica.

Cuidados (vindos da operacao real da base de origem):
  - a pasta do cliente so e aceita por NOME EXATO (normalizado, sem acento).
    'name contains' achava pasta de homonimo/parente ("MARIA" casava "MARIA
    JOSE..."), e gravar contrato na pasta do cliente errado e pior do que nao
    arquivar. Mais de uma pasta com o mesmo nome = nao arquiva, avisa.
  - o log de ja sincronizados fica AO LADO do script (antes era caminho
    relativo: rodado de outra pasta, se perdia e reenviava tudo);
  - antes de subir, confere se o arquivo ja esta na pasta (nada de duplicata).

USO:
  python SYNC/sync_assinados.py                arquiva (comportamento de sempre)
  python SYNC/sync_assinados.py --simular      so mostra o que faria
  python SYNC/sync_assinados.py --dias 30      so os assinados nos ultimos 30 dias
"""
import argparse
import os
import re
import sys
import json
import unicodedata
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

AQUI = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(AQUI, '..', 'config', '.env'))

# Arquivo para rastrear docs ja sincronizados (caminho absoluto, ao lado do script)
SYNC_LOG = os.path.join(AQUI, "sync_assinados_log.json")
MAX_PAGINAS = 40


def carregar_log():
    try:
        with open(SYNC_LOG, 'r', encoding='utf-8') as f:
            log = json.load(f)
        log.setdefault("sincronizados", [])
        return log
    except (OSError, ValueError):
        return {"sincronizados": []}


def salvar_log(log):
    with open(SYNC_LOG, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def _norm(nome):
    """Maiusculo, sem acento e sem pontuacao - para comparar nomes de pasta."""
    s = unicodedata.normalize('NFKD', str(nome or '')).encode('ascii', 'ignore').decode().upper()
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())


def _q(valor):
    """Escapa valor para dentro de aspas simples numa query do Drive."""
    return str(valor).replace('\\', '\\\\').replace("'", "\\'")


def autenticar_drive():
    token_path = os.path.join(AQUI, '..', 'config', 'token.json')
    creds = Credentials.from_authorized_user_file(token_path, [
        'https://www.googleapis.com/auth/drive'
    ])
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'w') as f:
                f.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


def buscar_pasta_cliente(drive, nome_cliente):
    """Busca a pasta do cliente em RECLAMANTE pelo nome EXATO (normalizado).

    Retorna (pasta_id, motivo). pasta_id None quando nao ha pasta segura.
    """
    # ID da pasta RECLAMANTE no Drive do escritorio -> definir em config/.env
    pasta_reclamante = os.getenv("GOOGLE_PASTA_RECLAMANTE", "")
    if not pasta_reclamante:
        return None, "GOOGLE_PASTA_RECLAMANTE nao configurado"

    alvo = _norm(nome_cliente)
    iguais, page_token = [], None
    while True:
        results = drive.files().list(
            q=(f"'{_q(pasta_reclamante)}' in parents and "
               "mimeType='application/vnd.google-apps.folder' and trashed=false"),
            fields='nextPageToken, files(id, name)', pageSize=1000,
            pageToken=page_token).execute()
        iguais += [f for f in results.get('files', []) if _norm(f['name']) == alvo]
        page_token = results.get('nextPageToken')
        if not page_token:
            break

    if len(iguais) == 1:
        return iguais[0]['id'], "pasta pelo nome exato"
    if len(iguais) > 1:
        return None, "mais de uma pasta com esse nome - conferir a mao"
    return None, "nenhuma pasta com o nome exato"


def buscar_subpasta_documentos(drive, pasta_cliente_id):
    """Busca a subpasta DOCUMENTOS DO CLIENTE."""
    results = drive.files().list(
        q=f"'{pasta_cliente_id}' in parents and mimeType='application/vnd.google-apps.folder' and name='DOCUMENTOS DO CLIENTE' and trashed=false",
        fields='files(id)').execute()

    if results.get('files'):
        return results['files'][0]['id']
    return pasta_cliente_id


def ja_esta_na_pasta(drive, pasta_id, nome_arquivo):
    """True se ja existe arquivo com o mesmo nome (normalizado) na pasta."""
    results = drive.files().list(
        q=f"'{pasta_id}' in parents and trashed=false",
        fields='files(name)', pageSize=1000).execute()
    alvo = _norm(nome_arquivo)
    return any(_norm(f['name']) == alvo for f in results.get('files', []))


def _dentro_da_janela(doc, corte):
    """Sem janela (corte None) tudo entra. Data ilegivel tambem entra."""
    if corte is None:
        return True
    quando = str(doc.get('last_update_at') or doc.get('created_at') or '')[:10]
    try:
        return datetime.strptime(quando, '%Y-%m-%d') >= corte
    except ValueError:
        return True


def sincronizar(simular=False, dias=None):
    print(f"\n=== SYNC ZAPSIGN -> DRIVE | {datetime.now().strftime('%d/%m/%Y %H:%M')}"
          f"{' | SIMULACAO' if simular else ''}"
          f"{f' | ultimos {dias} dias' if dias else ''} ===\n")

    token = os.getenv("ZAPSIGN_API_TOKEN")
    if not token:
        print("ERRO: ZAPSIGN_API_TOKEN nao encontrado")
        return

    headers = {"Authorization": f"Bearer {token}"}
    log = carregar_log()
    feitos = set(log["sincronizados"])
    drive = autenticar_drive()
    corte = datetime.now() - timedelta(days=dias) if dias else None

    # Buscar documentos assinados no ZapSign
    page = 1
    novos = 0
    pulados = []

    while page <= MAX_PAGINAS:
        try:
            resp = requests.get(
                f"https://api.zapsign.com.br/api/v1/docs/?page={page}",
                headers=headers, timeout=30)
        except requests.RequestException as e:
            print(f"Erro de rede na API ZapSign: {e}")
            break

        if resp.status_code != 200:
            print(f"Erro na API ZapSign: {resp.status_code}")
            break

        data = resp.json()
        docs = data.get("results", [])

        if not docs:
            break

        for doc in docs:
            doc_token = doc.get("token", "")
            doc_status = doc.get("status", "")
            doc_nome = doc.get("name", "")
            signed_file = doc.get("signed_file", "")
            folder_path = doc.get("folder_path", "") or ""

            # Pular docs nao assinados, fora da janela ou ja sincronizados
            if doc_status != "signed":
                continue
            if doc_token in feitos:
                continue
            if not signed_file:
                continue
            if not _dentro_da_janela(doc, corte):
                continue

            # Extrair nome do cliente da pasta do ZapSign
            nome_cliente = folder_path.strip("/").strip()
            if not nome_cliente:
                # Tentar extrair do nome do documento
                parts = doc_nome.split(" - ")
                if len(parts) > 0:
                    nome_cliente = parts[0].strip()

            if not nome_cliente:
                print(f"  Pulando {doc_nome} - nao conseguiu identificar cliente")
                continue

            # Buscar pasta do cliente no Drive (nome exato)
            pasta_cliente, motivo = buscar_pasta_cliente(drive, nome_cliente)
            if not pasta_cliente:
                pulados.append(f"{nome_cliente} ({motivo})")
                print(f"  Pulando {doc_nome} - pasta '{nome_cliente}': {motivo}")
                continue

            pasta_docs = buscar_subpasta_documentos(drive, pasta_cliente)
            nome_arquivo = f"{doc_nome} (ASSINADO).pdf"

            if ja_esta_na_pasta(drive, pasta_docs, nome_arquivo):
                print(f"  [ja esta na pasta] {nome_arquivo}")
                if not simular:
                    feitos.add(doc_token)
                continue

            if simular:
                print(f"  [simulacao] {nome_arquivo} -> {nome_cliente}")
                continue

            # Baixar PDF assinado
            print(f"  Baixando: {doc_nome} (assinado)")
            try:
                pdf_resp = requests.get(signed_file, timeout=120)
                if pdf_resp.status_code != 200:
                    print(f"    Erro ao baixar PDF: {pdf_resp.status_code}")
                    continue

                pdf_bytes = pdf_resp.content

                # Upload para o Drive
                media = MediaInMemoryUpload(pdf_bytes, mimetype='application/pdf')

                drive.files().create(
                    body={
                        'name': nome_arquivo,
                        'parents': [pasta_docs]
                    },
                    media_body=media,
                    fields='id'
                ).execute()

                print(f"  Salvo no Drive: {nome_arquivo}")
                feitos.add(doc_token)
                novos += 1

            except Exception as e:
                print(f"    Erro: {str(e)}")

        # Proxima pagina
        if not data.get("next"):
            break
        page += 1

    if not simular:
        log["sincronizados"] = sorted(feitos)
        log["ultima_rodada"] = datetime.now().isoformat(sep=' ', timespec='seconds')
        salvar_log(log)
    print(f"\n=== {novos} documentos sincronizados | sem pasta segura: {len(pulados)} ===\n")
    if pulados:
        print("Nao arquivados (pasta nao confirmada): " + "; ".join(sorted(set(pulados))[:15]))


def main():
    ap = argparse.ArgumentParser(description="Sincroniza assinados ZapSign -> Drive")
    ap.add_argument('--simular', action='store_true', help='so mostra o que faria')
    ap.add_argument('--dias', type=int, default=None,
                    help='so os documentos atualizados nos ultimos N dias')
    a = ap.parse_args()
    sincronizar(simular=a.simular, dias=a.dias)


if __name__ == "__main__":
    main()
