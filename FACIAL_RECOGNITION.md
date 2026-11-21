# 🎥 Monitor de Reconhecimento Facial — `monitor-video.py`

Script Python para detecção e reconhecimento facial em tempo real com **aceleração por GPU**, integrado ao projeto **CorePulseMonitor**.

---

## 📦 Dependências

### Obrigatórias

| Pacote | Versão Recomendada | Uso |
|---|---|---|
| `opencv-python` | `4.10.0.84` | Captura de vídeo, inferência da rede neural DNN e renderização |
| `numpy` | `>= 2.0.0` | Operações matriciais e manipulação de tensores |

### Opcionais (Identificação por Nome)

| Pacote | Versão | Uso |
|---|---|---|
| `setuptools` | `< 70.0.0` | Compatibilidade com `pkg_resources` exigida pelos modelos do `face_recognition` |
| `face_recognition` | `>= 1.3.0` | Identificação biométrica de pessoas cadastradas via `dlib` |

---

## ⚙️ Instalação

### 1. Ativar o ambiente virtual do projeto

```powershell
cd d:\git\repos\CorePulseMonitor
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependências obrigatórias

```powershell
pip install opencv-python==4.10.0.84 numpy
```

### 3. Instalar identificação de pessoas (opcional)

```powershell
pip install "setuptools<70"
pip install face_recognition
```

> [!WARNING]
> No **Windows**, o pacote `face_recognition` depende do `dlib`. É necessário ter o **Visual C++ Build Tools** instalado (ou utilizar pacotes pré-compilados como `face_recognition-whl`). O `setuptools<70` é essencial para evitar erros de inicialização dos modelos no Python 3.12+.

---

## ▶️ Como Executar

Com o ambiente ativado:
```powershell
python monitor-video.py
```
*(Ou diretamente pelo executável: `.\.venv\Scripts\python.exe monitor-video.py`)*

> [!NOTE]
> Na primeira execução, o script baixará automaticamente os pesos da rede neural (~10 MB) para a pasta `modelos/`.

---

## 🎮 Teclas de Atalho

| Tecla | Ação |
|---|---|
| `Q` ou `Esc` | Encerrar a aplicação |
| `G` | **Alternar entre GPU e CPU** em tempo real para inferência do modelo |
| `C` | Capturar o frame atual e salvar foto em `./capturas/` |
| `F` | Alternar exibição do contador de FPS |

---

## 🧠 Como Funciona

### Motores de Detecção
1. **DNN (SSD + ResNet-10) [Padrão]:** 
   - Rede neural de alta precisão que detecta faces mesmo em ângulos difíceis ou sob iluminação variável.
   - Suporta aceleração via hardware (**GPU NVIDIA via OpenCL / DirectX NVD3D11** ou CUDA).
   - Exibe a porcentagem de confiança da detecção facial (ex: `98%`).
2. **Haar Cascade [Fallback Automático]:** 
   - Utilizado como plano de contingência caso os arquivos do modelo DNN não possam ser baixados.

### Pipeline de Processamento

```
Webcam (1280x720)
       │
       ▼
Blob DNN (300x300) ──► GPU / OpenCL (SSD + ResNet-10) ──► Caixas Delimitadoras + Confiança
       │
       ▼ (A cada 2 frames se houver rostos e face_recognition ativo)
Extração de Encodings (128D) ──► Comparação com faces conhecidas ──► Nome Identificado
```

---

## 👤 Cadastrar Pessoas para Identificação

> [!NOTE]
> Esta funcionalidade exige o pacote `face_recognition` instalado.

1. Insira imagens (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`) dentro da pasta `faces_conhecidas/`.
2. **O nome do arquivo será usado como o rótulo exibido na tela.**
   * Exemplo: `faces_conhecidas/carlos.jpg` exibirá `carlos (97%)`.

**Estrutura recomendada:**
```
CorePulseMonitor/
└── faces_conhecidas/
    ├── joao.jpg
    ├── maria.png
    └── carlos.jpeg
```

> [!TIP]
> Para maior acurácia, utilize fotos nítidas, com boa iluminação e contendo apenas o rosto da pessoa.

---

## 🗂️ Estrutura de Pastas do Módulo

```
CorePulseMonitor/
├── monitor-video.py       ← Script de monitoramento e visão computacional
├── modelos/               ← Pesos do modelo SSD ResNet (baixados automaticamente)
│   ├── deploy.prototxt
│   └── res10_300x300_ssd_iter_140000.caffemodel
├── faces_conhecidas/      ← Fotos das pessoas cadastradas
└── capturas/              ← Fotos salvas ao pressionar a tecla C
```

---

## ⚙️ Configurações Avançadas

Parâmetros ajustáveis no topo do arquivo [monitor-video.py](file:///d:/git/repos/CorePulseMonitor/monitor-video.py):

| Constante | Padrão | Descrição |
|---|---|---|
| `INDICE_CAMERA` | `0` | Índice do dispositivo de captura (0 = câmera integrada) |
| `CONFIANCA_MIN` | `0.5` | Limiar mínimo de confiança da rede DNN para aceitar um rosto (0.0 a 1.0) |
| `TOLERANCIA_FR` | `0.55` | Distância euclidiana máxima para identificação facial (menor = mais rigoroso) |
| `PASTA_MODELOS` | `"modelos"` | Diretório de armazenamento dos arquivos da rede neural |
| `PASTA_FACES` | `"faces_conhecidas"` | Diretório de origem das fotos cadastradas |
| `PASTA_CAPTURAS` | `"capturas"` | Diretório de destino das fotos salvas via tecla `C` |

---

## 🛠️ Solução de Problemas

| Sintoma | Causa Provável | Solução |
|---|---|---|
| `Erro: câmera 0 não encontrada` | Câmera ocupada ou índice incorreto | Feche outros aplicativos ou mude `INDICE_CAMERA = 1` |
| `face_recognition` com erro de `pkg_resources` | Versão nova do `setuptools` | Execute: `pip install "setuptools<70"` |
| Backend GPU cai em `CPU` | Driver de vídeo desatualizado | Atualize o driver da GPU NVIDIA para suportar OpenCL / Direct3D11 |
| Falha no download do modelo DNN | Bloqueio de rede ou firewall | Baixe manualmente os arquivos das URLs presentes no topo do script para a pasta `modelos/` |
| Falso positivo / detecções indesejadas | Confiança muito permissiva | Aumente `CONFIANCA_MIN` para `0.65` ou `0.7` |

---

## 📄 Licença

Módulo integrante do projeto **CorePulseMonitor**.
