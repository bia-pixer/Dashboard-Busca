import json
import time
from datetime import datetime, timedelta
from typing import List, Optional
import streamlit as st

class CookieManager:
    def __init__(self, tempo_bloqueio_minutos: int = 15):
        self.tempo_bloqueio = timedelta(minutes=tempo_bloqueio_minutos)
        self.cookies = self._carregar_cookies_streamlit()
        self.bloqueados = {}

    def _carregar_cookies_streamlit(self) -> List[str]:
        try:
            pool = st.secrets["cookies"]["pool"]
            json_list = json.loads(pool)
            # A lista já é de strings no formato "auth_token=xxx"
            return [list(d.keys())[0] for d in json_list]
        except Exception as e:
            st.error(f"Erro ao carregar cookies do secrets: {e}")
            return []

    def marcar_bloqueado(self, idx: int) -> None:
        self.bloqueados[idx] = datetime.now()

    def desbloquear_expirados(self):
        agora = datetime.now()
        expirados = [idx for idx, t in self.bloqueados.items() if agora - t > self.tempo_bloqueio]
        for idx in expirados:
            del self.bloqueados[idx]

    def proximo_cookie(self) -> Optional[dict]:
        self.desbloquear_expirados()
        for idx, cookie in enumerate(self.cookies):
            if idx not in self.bloqueados:
                return {"cookie": cookie, "indice": idx}
        return None

    def total_disponiveis(self):
        self.desbloquear_expirados()
        return len([i for i in range(len(self.cookies)) if i not in self.bloqueados])

    def total_bloqueados(self):
        self.desbloquear_expirados()
        return len(self.bloqueados)
