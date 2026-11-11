"""
Equipe / usuarios do escritorio - Alves Carneiro Advocacia e Consultoria Jurídica.

Centraliza os IDs de usuario do ADVBOX e os papeis funcionais.
NUNCA hardcode IDs no codigo das automacoes: leia sempre deste arquivo.

ADVBOX confirmado em uso (03/09/2026). Os IDs reais estao em config/.env:
  240863 = FABIANA SILVA ALVES CARNEIRO   295602 = LIVIA PAULA
Enquanto uma variavel estiver vazia, o papel retorna None e as automacoes que
dependem dele ficam inativas/seguras.
"""
import os

# IDs de usuario no ADVBOX (preenchidos via config/.env).
# Podem vir do .env (recomendado) ou ser definidos direto aqui.
USUARIOS_ADVBOX = {
    # Dra. Fabiana Silva Alves Carneiro, OAB/RJ 188.762 (ADVBOX id 240863).
    "RESPONSAVEL": os.getenv("ADVBOX_USER_RESPONSAVEL") or None,
    "OPERACIONAL": os.getenv("ADVBOX_USER_OPERACIONAL") or None,   # quem recebe tarefas operacionais
    "FINANCEIRO": os.getenv("ADVBOX_USER_FINANCEIRO") or None,     # quem lanca transacoes financeiras
}

# Papel usado no campo 'from' das tarefas (/posts).
USUARIO_PADRAO_TAREFAS = "RESPONSAVEL"


def id_usuario(papel):
    """Retorna o ID ADVBOX do papel informado (ou None se nao configurado)."""
    valor = USUARIOS_ADVBOX.get(papel)
    if valor in (None, ""):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return valor
