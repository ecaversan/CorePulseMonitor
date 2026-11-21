# ⚡ CorePulseMonitor

Conjunto de ferramentas para monitoramento de hardware e visão computacional em tempo real desenvolvido em Python.

---

## 🚀 Módulos do Projeto

### 1. 🖥️ Monitor de CPU (`monitor-cpu.py`)
Interface gráfica moderna (construída com `tkinter`) para acompanhamento em tempo real:
- **Gauge circular animado:** indicador visual de uso da CPU (com alerta de cores: verde / amarelo / vermelho).
- **Cards com métricas:** frequência atual (GHz), temperatura estimada/sensores (°C), consumo em Watts estimado e contagem de núcleos/threads.
- **Gráfico de histórico:** curva de uso dos últimos 60 segundos com preenchimento gradiente.
- **Uso por núcleo:** barras individuais para cada thread lógica do processador.

### 2. 🎥 Reconhecimento Facial com GPU (`monitor-video.py`)
Reconhecimento e detecção facial em tempo real pela webcam com suporte a aceleração por hardware:
- **Detector DNN (SSD + ResNet-10):** rede neural de alta precisão com score de confiança por detecção.
- **Aceleração por GPU:** suporte a OpenCL / DirectX (compatível com GPUs dedicadas como NVIDIA RTX) com chaveamento em tempo real (tecla `G`).
- **Identificação facial opcional:** integração com `face_recognition` para reconhecer pessoas cadastradas na pasta `faces_conhecidas/`.
- **Captura rápida de frames:** tecla `C` para salvar fotos na pasta `capturas/`.

---

## 📦 Instalação e Preparação

Clone o repositório:
```bash
git clone https://github.com/ecaversan/CorePulseMonitor.git
cd CorePulseMonitor
```

Crie e ative o ambiente virtual:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:
```bash
pip install -r requirements.txt
```

*(Opcional)* Para identificação facial por nome:
```bash
pip install "setuptools<70"
pip install face-recognition
```

---

## ▶️ Como Usar

### Executar o Monitor de CPU:
```powershell
python monitor-cpu.py
```

### Executar o Reconhecimento Facial:
```powershell
python monitor-video.py
```

**Atalhos do monitor de vídeo:**
| Tecla | Ação |
|---|---|
| `Q` ou `Esc` | Sair do monitor |
| `C` | Capturar foto e salvar em `./capturas/` |
| `F` | Alternar exibição de FPS |
| `G` | Alternar entre GPU e CPU |

---

## 📄 Mais Detalhes

Para instruções detalhadas sobre o modelo facial, cadastro de pessoas e resolução de problemas, consulte [FACIAL_RECOGNITION.md](FACIAL_RECOGNITION.md).
