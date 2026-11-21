# 🎥 Monitor de Reconhecimento Facial — `monitor-video.py`

Script Python para detecção e reconhecimento facial em tempo real usando a câmera do computador, integrado ao projeto **CorePulseMonitor**.

---

## 📦 Dependências

### Obrigatórias

| Pacote | Uso |
|---|---|
| `opencv-python` | Captura de vídeo e detecção de rostos |
| `numpy` | Operações matriciais (instalado junto com o OpenCV) |

### Opcionais

| Pacote | Uso |
|---|---|
| `face_recognition` | Identificação de pessoas cadastradas |

---

## ⚙️ Instalação

### 1. Ativar o ambiente virtual do projeto

```powershell
cd d:\git\repos\CorePulseMonitor
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependências obrigatórias

```powershell
pip install opencv-python
```

### 3. Instalar identificação de pessoas (opcional)

```powershell
pip install face_recognition
```

> [!WARNING]
> No **Windows**, o pacote `face_recognition` depende do `dlib`, que requer compilação nativa.
> Certifique-se de ter o **Visual C++ Build Tools** instalado antes de prosseguir.
> Alternativa: use o pacote pré-compilado `pip install face_recognition-whl` ou execute via **WSL**.

---

## ▶️ Como executar

```powershell
.\.venv\Scripts\python.exe monitor-video.py
```

---

## 🎮 Teclas durante a execução

| Tecla | Ação |
|---|---|
| `Q` ou `Esc` | Encerrar o programa |
| `C` | Capturar o frame atual e salvar em `./capturas/` |
| `F` | Alternar exibição do contador de FPS |

---

## 🧠 Como funciona

### Modos de operação

```
Sem face_recognition          Com face_recognition
─────────────────────         ──────────────────────────────────
Detecção de rostos            Detecção + Identificação de pessoas
Retângulo verde               Retângulo amarelo (pessoa conhecida)
Exibe contador de rostos      Exibe nome cadastrado no rótulo
Nenhuma instalação extra      Requer dlib + imagens cadastradas
```

### Pipeline de processamento

```
Camera → Frame BGR → Escala de Cinza → Haar Cascade → Retângulos
                   ↘ RGB (opcional) → face_recognition → Nome da pessoa
```

---

## 👤 Cadastrar pessoas para identificação

> [!NOTE]
> Esta funcionalidade só está disponível com o pacote `face_recognition` instalado.

1. Crie a pasta `faces_conhecidas/` na raiz do projeto (criada automaticamente na primeira execução).
2. Adicione fotos no formato `.jpg`, `.jpeg`, `.png`, `.bmp` ou `.webp`.
3. **O nome do arquivo se torna o rótulo exibido na tela.**

**Exemplo de estrutura:**

```
CorePulseMonitor/
└── faces_conhecidas/
    ├── joao.jpg
    ├── maria.png
    └── carlos.jpeg
```

> [!TIP]
> Use fotos com boa iluminação e apenas **um rosto por imagem** para melhor precisão.
> Quanto mais fotos por pessoa, maior a acurácia do reconhecimento.

---

## 🗂️ Estrutura de pastas gerada

```
CorePulseMonitor/
├── monitor-video.py       ← Script principal
├── faces_conhecidas/      ← Fotos para cadastro (criada automaticamente)
└── capturas/              ← Frames salvos com a tecla C (criada automaticamente)
```

---

## ⚙️ Configurações avançadas

As configurações ficam no topo do arquivo `monitor-video.py` e podem ser ajustadas conforme necessário:

| Variável | Padrão | Descrição |
|---|---|---|
| `INDICE_CAMERA` | `0` | Índice da câmera (0 = padrão; 1, 2... para câmeras externas) |
| `ESCALA_DETECCAO` | `1.1` | `scaleFactor` do Haar Cascade (menor = mais detecções, mais lento) |
| `VIZINHOS_MIN` | `5` | `minNeighbors` (maior = menos falsos positivos) |
| `TAMANHO_MIN_ROSTO` | `(60, 60)` | Tamanho mínimo de rosto detectado (px) |
| `TOLERANCIA_FR` | `0.55` | Limiar de similaridade para identificação (menor = mais rigoroso) |

---

## 🛠️ Solução de problemas

| Sintoma | Possível causa | Solução |
|---|---|---|
| `Erro: câmera não encontrada` | Câmera em uso ou índice errado | Feche outros apps; tente `INDICE_CAMERA = 1` |
| Muitos falsos positivos | `VIZINHOS_MIN` muito baixo | Aumente para `7` ou `8` |
| Reconhecimento impreciso | Foto de baixa qualidade | Use foto com boa iluminação e rosto centralizado |
| `face_recognition` não instala | Falta do `dlib` / Build Tools | Instale Visual C++ Build Tools ou use WSL |
| FPS muito baixo | Resolução alta + CPU lenta | Reduza a resolução no `cap.set(...)` para `640x480` |

---

## 📄 Licença

Parte do projeto **CorePulseMonitor**.
