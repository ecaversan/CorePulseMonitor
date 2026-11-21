"""
monitor-cpu.py – Monitor de CPU com Interface Gráfica
=====================================================
Dashboard visual em tempo real usando tkinter (sem dependências extras).

Funcionalidades:
  • Medidor circular (gauge) de uso da CPU
  • Barras de uso por núcleo
  • Gráfico de histórico dos últimos 60 segundos
  • Frequência, temperatura e consumo estimado
  • Indicadores com código de cores (verde / amarelo / vermelho)

Dependências:
    pip install psutil
"""

import tkinter as tk
from tkinter import font as tkfont
import math
import time
import os
import psutil

# ──────────────────────────────────────────────────────────────────────────────
# Configurações
# ──────────────────────────────────────────────────────────────────────────────
TDP_BASE       = 65.0        # TDP base da CPU para estimativa de consumo (Watts)
INTERVALO_MS   = 1000        # Intervalo de atualização em milissegundos
HISTORICO_MAX  = 60          # Segundos de histórico no gráfico
NUM_NUCLEOS    = psutil.cpu_count(logical=True)

# Paleta de cores
COR_FUNDO       = "#1a1a2e"
COR_PAINEL      = "#16213e"
COR_BORDA       = "#0f3460"
COR_TEXTO       = "#e0e0e0"
COR_TITULO      = "#00d4ff"
COR_SUBTITULO   = "#7ec8e3"
COR_VERDE       = "#00e676"
COR_AMARELO     = "#ffea00"
COR_VERMELHO    = "#ff1744"
COR_GRADE       = "#1e3a5f"
COR_GRAFICO_BG  = "#0d1b2a"
COR_LINHA_GRAF  = "#00d4ff"
COR_PREENCHE    = "#00d4ff"


# ──────────────────────────────────────────────────────────────────────────────
# Funções auxiliares
# ──────────────────────────────────────────────────────────────────────────────

def cor_por_nivel(valor: float) -> str:
    """Retorna cor baseada no nível de uso (0-100)."""
    if valor < 50:
        return COR_VERDE
    elif valor < 80:
        return COR_AMARELO
    return COR_VERMELHO


def ler_temperatura() -> float | None:
    """Tenta ler sensores de temperatura (Linux/macOS)."""
    if hasattr(psutil, "sensors_temperatures"):
        temps = psutil.sensors_temperatures()
        if temps:
            for nome in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
                if nome in temps and temps[nome]:
                    return temps[nome][0].current
            primeiro = next(iter(temps.values()))
            if primeiro:
                return primeiro[0].current
    return None


def estimar_consumo_watts(uso_percent: float, tdp_base: float = TDP_BASE) -> float:
    """Estima o consumo em Watts com base na curva de carga."""
    idle_watts = tdp_base * 0.15
    return idle_watts + (tdp_base - idle_watts) * ((uso_percent / 100.0) ** 1.15)


# ──────────────────────────────────────────────────────────────────────────────
# Widget: Medidor Circular (Gauge)
# ──────────────────────────────────────────────────────────────────────────────

class GaugeCPU(tk.Canvas):
    """Medidor circular animado para uso total da CPU."""

    def __init__(self, master, tamanho=220, **kwargs):
        super().__init__(master, width=tamanho, height=tamanho,
                         bg=COR_PAINEL, highlightthickness=0, **kwargs)
        self.tamanho = tamanho
        self.valor = 0.0
        self._desenhar(0)

    def atualizar(self, valor: float):
        self.valor = valor
        self.delete("all")
        self._desenhar(valor)

    def _desenhar(self, valor: float):
        cx, cy = self.tamanho / 2, self.tamanho / 2
        raio = self.tamanho / 2 - 20
        espessura = 14

        # Arco de fundo (trilha)
        self.create_arc(
            cx - raio, cy - raio, cx + raio, cy + raio,
            start=225, extent=-270, style="arc",
            outline=COR_BORDA, width=espessura
        )

        # Arco de valor
        angulo = (valor / 100.0) * 270
        cor = cor_por_nivel(valor)
        if angulo > 0:
            self.create_arc(
                cx - raio, cy - raio, cx + raio, cy + raio,
                start=225, extent=-angulo, style="arc",
                outline=cor, width=espessura
            )

        # Texto central
        self.create_text(cx, cy - 10, text=f"{valor:.1f}%",
                         fill=cor, font=("Consolas", 28, "bold"))
        self.create_text(cx, cy + 22, text="Uso da CPU",
                         fill=COR_SUBTITULO, font=("Segoe UI", 10))

        # Marcas do arco (0, 25, 50, 75, 100)
        raio_marca = raio + 10
        for pct in (0, 25, 50, 75, 100):
            ang_rad = math.radians(225 - (pct / 100) * 270)
            mx = cx + raio_marca * math.cos(ang_rad)
            my = cy - raio_marca * math.sin(ang_rad)
            self.create_text(mx, my, text=str(pct),
                             fill=COR_TEXTO, font=("Consolas", 7))


# ──────────────────────────────────────────────────────────────────────────────
# Widget: Barras por Núcleo
# ──────────────────────────────────────────────────────────────────────────────

class BarrasNucleos(tk.Canvas):
    """Barras horizontais de uso por núcleo."""

    def __init__(self, master, num_nucleos, largura=280, **kwargs):
        altura_barra = 16
        espacamento = 4
        altura_total = num_nucleos * (altura_barra + espacamento) + 30
        super().__init__(master, width=largura, height=altura_total,
                         bg=COR_PAINEL, highlightthickness=0, **kwargs)
        self.largura = largura
        self.num_nucleos = num_nucleos
        self.altura_barra = altura_barra
        self.espacamento = espacamento

    def atualizar(self, valores: list[float]):
        self.delete("all")
        self.create_text(self.largura / 2, 12, text="Uso por Núcleo",
                         fill=COR_SUBTITULO, font=("Segoe UI", 10, "bold"))

        margem_esq = 55
        margem_dir = 10
        larg_max = self.largura - margem_esq - margem_dir

        for i, val in enumerate(valores):
            y = 28 + i * (self.altura_barra + self.espacamento)
            cor = cor_por_nivel(val)

            # Rótulo
            self.create_text(margem_esq - 8, y + self.altura_barra / 2,
                             text=f"CPU {i:>2d}", anchor="e",
                             fill=COR_TEXTO, font=("Consolas", 8))

            # Fundo da barra
            self.create_rectangle(margem_esq, y,
                                  margem_esq + larg_max, y + self.altura_barra,
                                  fill=COR_BORDA, outline="")

            # Barra de preenchimento
            larg = (val / 100.0) * larg_max
            if larg > 0:
                self.create_rectangle(margem_esq, y,
                                      margem_esq + larg, y + self.altura_barra,
                                      fill=cor, outline="")

            # Percentual
            self.create_text(margem_esq + larg_max + 5, y + self.altura_barra / 2,
                             text=f"{val:.0f}%", anchor="w",
                             fill=cor, font=("Consolas", 7))


# ──────────────────────────────────────────────────────────────────────────────
# Widget: Gráfico de Histórico
# ──────────────────────────────────────────────────────────────────────────────

class GraficoHistorico(tk.Canvas):
    """Gráfico de linha do uso da CPU nos últimos N segundos."""

    def __init__(self, master, largura=560, altura=160, max_pontos=HISTORICO_MAX, **kwargs):
        super().__init__(master, width=largura, height=altura,
                         bg=COR_GRAFICO_BG, highlightthickness=1,
                         highlightbackground=COR_BORDA, **kwargs)
        self.largura = largura
        self.altura = altura
        self.max_pontos = max_pontos
        self.historico: list[float] = []
        self.margem = {"esq": 40, "dir": 10, "top": 25, "bot": 20}

    def adicionar(self, valor: float):
        self.historico.append(valor)
        if len(self.historico) > self.max_pontos:
            self.historico.pop(0)
        self._redesenhar()

    def _redesenhar(self):
        self.delete("all")
        m = self.margem
        area_w = self.largura - m["esq"] - m["dir"]
        area_h = self.altura - m["top"] - m["bot"]

        # Título
        self.create_text(self.largura / 2, 12, text=f"Histórico ({self.max_pontos}s)",
                         fill=COR_SUBTITULO, font=("Segoe UI", 9, "bold"))

        # Linhas de grade horizontais (0%, 25%, 50%, 75%, 100%)
        for pct in (0, 25, 50, 75, 100):
            y = m["top"] + area_h - (pct / 100) * area_h
            self.create_line(m["esq"], y, self.largura - m["dir"], y,
                             fill=COR_GRADE, dash=(2, 4))
            self.create_text(m["esq"] - 5, y, text=f"{pct}%", anchor="e",
                             fill=COR_TEXTO, font=("Consolas", 7))

        if len(self.historico) < 2:
            return

        # Pontos do gráfico
        pontos = []
        n = len(self.historico)
        for i, v in enumerate(self.historico):
            x = m["esq"] + (i / (self.max_pontos - 1)) * area_w
            y = m["top"] + area_h - (v / 100) * area_h
            pontos.append((x, y))

        # Preenchimento (área sob a curva)
        poly = list(pontos)
        poly.append((pontos[-1][0], m["top"] + area_h))
        poly.append((pontos[0][0], m["top"] + area_h))
        coords = [c for p in poly for c in p]
        self.create_polygon(coords, fill=COR_PREENCHE, stipple="gray25", outline="")

        # Linha
        line_coords = [c for p in pontos for c in p]
        self.create_line(line_coords, fill=COR_LINHA_GRAF, width=2, smooth=True)


# ──────────────────────────────────────────────────────────────────────────────
# Widget: Card de Informação
# ──────────────────────────────────────────────────────────────────────────────

class InfoCard(tk.Frame):
    """Card com ícone, rótulo e valor."""

    def __init__(self, master, icone: str, rotulo: str, **kwargs):
        super().__init__(master, bg=COR_PAINEL, padx=12, pady=8, **kwargs)
        self.configure(highlightbackground=COR_BORDA, highlightthickness=1)

        tk.Label(self, text=icone, bg=COR_PAINEL,
                 fg=COR_TITULO, font=("Segoe UI Emoji", 18)).pack(side="top")
        tk.Label(self, text=rotulo, bg=COR_PAINEL,
                 fg=COR_SUBTITULO, font=("Segoe UI", 9)).pack(side="top")
        self.lbl_valor = tk.Label(self, text="---", bg=COR_PAINEL,
                                  fg=COR_TEXTO, font=("Consolas", 16, "bold"))
        self.lbl_valor.pack(side="top")

    def atualizar(self, texto: str, cor: str = COR_TEXTO):
        self.lbl_valor.config(text=texto, fg=cor)


# ──────────────────────────────────────────────────────────────────────────────
# App Principal
# ──────────────────────────────────────────────────────────────────────────────

class MonitorCPUApp:
    """Janela principal do monitor de CPU."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CorePulseMonitor – CPU")
        self.root.configure(bg=COR_FUNDO)
        self.root.resizable(False, False)

        self._criar_widgets()
        self._atualizar()
        self.root.mainloop()

    def _criar_widgets(self):
        r = self.root

        # ── Título ────────────────────────────────────────────────────────────
        frm_titulo = tk.Frame(r, bg=COR_FUNDO, pady=8)
        frm_titulo.pack(fill="x")
        tk.Label(frm_titulo, text="⚡ CORE PULSE MONITOR", bg=COR_FUNDO,
                 fg=COR_TITULO, font=("Segoe UI", 16, "bold")).pack()
        tk.Label(frm_titulo, text="Monitoramento de CPU em Tempo Real", bg=COR_FUNDO,
                 fg=COR_SUBTITULO, font=("Segoe UI", 9)).pack()

        # ── Área superior: Gauge + Cards ──────────────────────────────────────
        frm_top = tk.Frame(r, bg=COR_FUNDO, padx=10)
        frm_top.pack(fill="x")

        # Gauge à esquerda
        frm_gauge = tk.Frame(frm_top, bg=COR_PAINEL, padx=8, pady=8,
                             highlightbackground=COR_BORDA, highlightthickness=1)
        frm_gauge.pack(side="left", padx=(0, 10))
        self.gauge = GaugeCPU(frm_gauge, tamanho=220)
        self.gauge.pack()

        # Cards no centro
        frm_cards = tk.Frame(frm_top, bg=COR_FUNDO)
        frm_cards.pack(side="left", fill="both", expand=True)

        grid_cards = tk.Frame(frm_cards, bg=COR_FUNDO)
        grid_cards.pack(expand=True)

        self.card_freq = InfoCard(grid_cards, "🔄", "Frequência")
        self.card_freq.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.card_temp = InfoCard(grid_cards, "🌡️", "Temperatura")
        self.card_temp.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.card_watts = InfoCard(grid_cards, "⚡", "Consumo Est.")
        self.card_watts.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        self.card_nucleos = InfoCard(grid_cards, "🧮", "Núcleos")
        self.card_nucleos.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self.card_nucleos.atualizar(
            f"{psutil.cpu_count(logical=False)}C / {NUM_NUCLEOS}T"
        )

        # ── Área inferior: Gráfico + Barras ───────────────────────────────────
        frm_bot = tk.Frame(r, bg=COR_FUNDO, padx=10, pady=10)
        frm_bot.pack(fill="x")

        # Gráfico à esquerda
        frm_graf = tk.Frame(frm_bot, bg=COR_PAINEL, padx=6, pady=6,
                            highlightbackground=COR_BORDA, highlightthickness=1)
        frm_graf.pack(side="left", padx=(0, 10))
        self.grafico = GraficoHistorico(frm_graf, largura=340, altura=180)
        self.grafico.pack()

        # Barras à direita
        frm_barras = tk.Frame(frm_bot, bg=COR_PAINEL, padx=6, pady=6,
                              highlightbackground=COR_BORDA, highlightthickness=1)
        frm_barras.pack(side="left", fill="both", expand=True)
        self.barras = BarrasNucleos(frm_barras, NUM_NUCLEOS, largura=260)
        self.barras.pack()

        # ── Rodapé ────────────────────────────────────────────────────────────
        self.lbl_status = tk.Label(r, text="", bg=COR_FUNDO, fg=COR_SUBTITULO,
                                   font=("Consolas", 8), anchor="e", padx=10)
        self.lbl_status.pack(fill="x", pady=(0, 4))

    def _atualizar(self):
        try:
            # Coleta de dados
            uso_total = psutil.cpu_percent(interval=0)
            usos_nucleo = psutil.cpu_percent(interval=0, percpu=True)
            freq = psutil.cpu_freq()
            ghz = (freq.current / 1000.0) if freq else 0.0
            temp = ler_temperatura()
            watts = estimar_consumo_watts(uso_total)

            # Atualiza widgets
            self.gauge.atualizar(uso_total)
            self.grafico.adicionar(uso_total)
            self.barras.atualizar(usos_nucleo)

            self.card_freq.atualizar(f"{ghz:.2f} GHz",
                                     cor_por_nivel(uso_total))

            if temp is not None:
                self.card_temp.atualizar(f"{temp:.1f} °C",
                                         cor_por_nivel(temp))
            else:
                self.card_temp.atualizar("N/D", COR_SUBTITULO)

            self.card_watts.atualizar(f"{watts:.1f} W",
                                      cor_por_nivel(uso_total))

            # Rodapé
            agora = time.strftime("%H:%M:%S")
            self.lbl_status.config(
                text=f"Atualizado: {agora}  |  Intervalo: {INTERVALO_MS}ms"
            )

        except Exception as e:
            self.lbl_status.config(text=f"Erro: {e}", fg=COR_VERMELHO)

        self.root.after(INTERVALO_MS, self._atualizar)


# ──────────────────────────────────────────────────────────────────────────────
# Ponto de entrada
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    MonitorCPUApp()
