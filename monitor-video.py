"""
monitor-video.py – Reconhecimento Facial em Tempo Real (GPU Acelerado)
======================================================================
Captura o vídeo da câmera e detecta/reconhece rostos usando:
  • Detecção  : OpenCV DNN (SSD + ResNet-10) com aceleração GPU via OpenCL
  • Fallback  : Haar Cascade (caso o modelo DNN não esteja disponível)
  • Reconhec. : face_recognition (opcional, instale se quiser identificar pessoas)

Dependências mínimas:
    pip install opencv-python

Para reconhecimento de identidade (opcional):
    pip install face_recognition

Como cadastrar rostos conhecidos:
    Coloque imagens (JPG/PNG) na pasta  ./faces_conhecidas/
    com o nome da pessoa como nome do arquivo.
    Ex.: ./faces_conhecidas/joao.jpg  → será exibido "joao" na tela.

Teclas durante a execução:
    Q  – sair
    C  – capturar frame atual e salvar em ./capturas/
    F  – alternar exibição de FPS
    G  – alternar GPU / CPU
"""

import cv2
import os
import sys
import time
import datetime
import urllib.request
import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# Tenta importar face_recognition (opcional)
# ──────────────────────────────────────────────────────────────────────────────
try:
    import face_recognition  # type: ignore
    FACE_RECOGNITION_DISPONIVEL = True
except (ImportError, Exception):
    FACE_RECOGNITION_DISPONIVEL = False

# ──────────────────────────────────────────────────────────────────────────────
# Configurações
# ──────────────────────────────────────────────────────────────────────────────
INDICE_CAMERA       = 0           # 0 = câmera padrão; troque por 1, 2... se necessário
PASTA_FACES         = "faces_conhecidas"
PASTA_CAPTURAS      = "capturas"
PASTA_MODELOS       = "modelos"
CONFIANCA_MIN       = 0.5         # limiar de confiança do DNN (0.0 - 1.0)
COR_ROSTO           = (0, 255, 0)      # verde – rosto desconhecido / só detectado
COR_CONHECIDO       = (0, 200, 255)    # amarelo – rosto reconhecido
COR_TEXTO           = (255, 255, 255)  # branco
TOLERANCIA_FR       = 0.55        # limiar face_recognition (menor = mais rigoroso)

# URLs do modelo DNN (SSD + ResNet-10 para detecção facial)
DNN_PROTOTXT_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
DNN_CAFFEMODEL_URL = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
DNN_PROTOTXT_FILE   = "deploy.prototxt"
DNN_CAFFEMODEL_FILE = "res10_300x300_ssd_iter_140000.caffemodel"


# ──────────────────────────────────────────────────────────────────────────────
# Utilitários
# ──────────────────────────────────────────────────────────────────────────────

def garantir_pasta(pasta: str) -> None:
    os.makedirs(pasta, exist_ok=True)


def baixar_arquivo(url: str, destino: str) -> bool:
    """Baixa um arquivo se não existir. Retorna True se disponível."""
    if os.path.isfile(destino):
        return True
    print(f"  ⬇ Baixando {os.path.basename(destino)}...")
    try:
        urllib.request.urlretrieve(url, destino)
        print(f"  ✔ Concluído: {os.path.basename(destino)}")
        return True
    except Exception as e:
        print(f"  ✘ Falha ao baixar: {e}")
        return False


def carregar_detector_dnn(pasta_modelos: str):
    """
    Carrega o modelo DNN (SSD + ResNet-10) para detecção facial.
    Retorna a rede (cv2.dnn.Net) ou None se indisponível.
    """
    garantir_pasta(pasta_modelos)
    prototxt  = os.path.join(pasta_modelos, DNN_PROTOTXT_FILE)
    caffemodel = os.path.join(pasta_modelos, DNN_CAFFEMODEL_FILE)

    if not baixar_arquivo(DNN_PROTOTXT_URL, prototxt):
        return None
    if not baixar_arquivo(DNN_CAFFEMODEL_URL, caffemodel):
        return None

    try:
        net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
        return net
    except Exception as e:
        print(f"  ✘ Erro ao carregar modelo DNN: {e}")
        return None


def configurar_backend_gpu(net: cv2.dnn.Net) -> str:
    """
    Tenta configurar o melhor backend de GPU disponível.
    Retorna o nome do backend selecionado.
    """
    # 1) Tenta CUDA (se OpenCV foi compilado com CUDA)
    try:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        # Testa com um blob dummy para verificar se funciona
        blob_teste = cv2.dnn.blobFromImage(
            np.zeros((300, 300, 3), dtype=np.uint8), 1.0, (300, 300)
        )
        net.setInput(blob_teste)
        net.forward()
        return "CUDA (GPU NVIDIA)"
    except Exception:
        pass

    # 2) Tenta OpenCL (disponível no seu OpenCV via NVD3D11)
    try:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)
        blob_teste = cv2.dnn.blobFromImage(
            np.zeros((300, 300, 3), dtype=np.uint8), 1.0, (300, 300)
        )
        net.setInput(blob_teste)
        net.forward()
        return "OpenCL (GPU via DirectX)"
    except Exception:
        pass

    # 3) Fallback: CPU
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    return "CPU"


def configurar_backend_cpu(net: cv2.dnn.Net) -> str:
    """Força execução na CPU."""
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    return "CPU"


def detectar_rostos_dnn(net: cv2.dnn.Net, frame, confianca_min: float = CONFIANCA_MIN):
    """
    Detecta rostos usando o modelo DNN.
    Retorna lista de (x, y, w, h, confiança).
    """
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(
        frame, 1.0, (300, 300),
        (104.0, 177.0, 123.0),  # mean subtraction
        swapRB=False, crop=False
    )
    net.setInput(blob)
    deteccoes = net.forward()

    rostos = []
    for i in range(deteccoes.shape[2]):
        confianca = deteccoes[0, 0, i, 2]
        if confianca < confianca_min:
            continue
        x1 = max(0, int(deteccoes[0, 0, i, 3] * w))
        y1 = max(0, int(deteccoes[0, 0, i, 4] * h))
        x2 = min(w, int(deteccoes[0, 0, i, 5] * w))
        y2 = min(h, int(deteccoes[0, 0, i, 6] * h))
        rostos.append((x1, y1, x2 - x1, y2 - y1, float(confianca)))
    return rostos


def carregar_faces_conhecidas(pasta: str):
    """
    Lê imagens de ./faces_conhecidas/ e extrai encodings (exige face_recognition).
    Retorna (nomes, encodings).
    """
    nomes, encodings = [], []
    if not FACE_RECOGNITION_DISPONIVEL:
        return nomes, encodings
    if not os.path.isdir(pasta):
        return nomes, encodings

    extensoes = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    for arquivo in os.listdir(pasta):
        if not arquivo.lower().endswith(extensoes):
            continue
        caminho = os.path.join(pasta, arquivo)
        imagem  = face_recognition.load_image_file(caminho)
        lista   = face_recognition.face_encodings(imagem)
        if lista:
            encodings.append(lista[0])
            nomes.append(os.path.splitext(arquivo)[0])
            print(f"  ✔ Rosto cadastrado: {nomes[-1]}")
        else:
            print(f"  ✘ Nenhum rosto encontrado em: {arquivo}")
    return nomes, encodings


def identificar_rosto(encoding, nomes_conhecidos, encodings_conhecidos):
    """Retorna o nome mais provável ou 'Desconhecido'."""
    if not encodings_conhecidos:
        return "Desconhecido"
    distancias = face_recognition.face_distance(encodings_conhecidos, encoding)
    idx_min    = int(np.argmin(distancias))
    if distancias[idx_min] < TOLERANCIA_FR:
        return nomes_conhecidos[idx_min]
    return "Desconhecido"


def desenhar_info_tela(frame, fps: float, n_rostos: int,
                       mostrar_fps: bool, backend: str, usando_dnn: bool) -> None:
    """Sobrepõe informações de status no canto superior esquerdo."""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (320, 92), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    agora = datetime.datetime.now().strftime("%H:%M:%S")
    detector_txt = "DNN (SSD+ResNet)" if usando_dnn else "Haar Cascade"
    cv2.putText(frame, f"Hora : {agora}",          (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.50, COR_TEXTO, 1)
    cv2.putText(frame, f"Rostos: {n_rostos}",      (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.50, COR_TEXTO, 1)
    cv2.putText(frame, f"Motor: {detector_txt}",   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 200, 255), 1)
    cv2.putText(frame, f"Backend: {backend}",      (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 200), 1)
    if mostrar_fps:
        cv2.putText(frame, f"FPS: {fps:.1f}", (w - 120, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COR_TEXTO, 1)


def salvar_captura(frame, pasta: str) -> str:
    garantir_pasta(pasta)
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(pasta, f"captura_{ts}.jpg")
    cv2.imwrite(path, frame)
    return path


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline principal
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    garantir_pasta(PASTA_FACES)
    garantir_pasta(PASTA_CAPTURAS)

    print("\n=== CorePulseMonitor – Reconhecimento Facial (GPU) ===\n")

    # ── Carrega detector DNN (com fallback para Haar) ─────────────────────────
    print("Carregando modelo de detecção facial DNN...")
    net = carregar_detector_dnn(PASTA_MODELOS)
    usando_dnn = net is not None

    if usando_dnn:
        print("Configurando aceleração por GPU...")
        backend_nome = configurar_backend_gpu(net)
        usar_gpu = "GPU" in backend_nome or "OpenCL" in backend_nome
        print(f"  ✔ Backend selecionado: {backend_nome}\n")
    else:
        print("  ⚠ Modelo DNN indisponível. Usando Haar Cascade (somente CPU).\n")
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        detector_haar = cv2.CascadeClassifier(cascade_path)
        if detector_haar.empty():
            sys.exit("Erro: não foi possível carregar o Haar Cascade.")
        backend_nome = "CPU (Haar Cascade)"
        usar_gpu = False

    # ── Carrega faces conhecidas (opcional) ───────────────────────────────────
    if FACE_RECOGNITION_DISPONIVEL:
        print(f"Carregando faces de '{PASTA_FACES}/'...")
        nomes_conhecidos, encodings_conhecidos = carregar_faces_conhecidas(PASTA_FACES)
        print(f"Total cadastrado: {len(nomes_conhecidos)} rosto(s)\n")
    else:
        nomes_conhecidos, encodings_conhecidos = [], []
        print("Modo: apenas detecção (instale 'face_recognition' para identificação)\n")

    # ── Abre a câmera ─────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(INDICE_CAMERA, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(INDICE_CAMERA)
    if not cap.isOpened():
        sys.exit(f"Erro: câmera {INDICE_CAMERA} não encontrada.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Câmera iniciada. Teclas: [Q] Sair  [C] Capturar  [F] FPS  [G] GPU/CPU\n")

    # ── Variáveis de estado ───────────────────────────────────────────────────
    mostrar_fps   = True
    t_prev        = time.perf_counter()
    fps           = 0.0
    cache_nomes: list = []
    frame_count   = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Aviso: frame inválido recebido.")
                time.sleep(0.05)
                continue

            frame_count += 1

            # ── Detecta rostos ────────────────────────────────────────────────
            if usando_dnn:
                deteccoes = detectar_rostos_dnn(net, frame, CONFIANCA_MIN)
                rostos = [(x, y, w, h) for (x, y, w, h, _) in deteccoes]
            else:
                cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cinza = cv2.equalizeHist(cinza)
                rostos = list(detector_haar.detectMultiScale(
                    cinza, scaleFactor=1.1, minNeighbors=5,
                    minSize=(60, 60), flags=cv2.CASCADE_SCALE_IMAGE,
                ))

            # ── Reconhecimento (face_recognition, a cada 2 frames) ────────────
            if FACE_RECOGNITION_DISPONIVEL and len(rostos) > 0 and frame_count % 2 == 0:
                rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                locs_fr = [(y, x+w, y+h, x) for (x, y, w, h) in rostos]
                encs    = face_recognition.face_encodings(rgb, locs_fr)
                cache_nomes = [
                    identificar_rosto(e, nomes_conhecidos, encodings_conhecidos)
                    for e in encs
                ]

            # ── Desenha retângulos e rótulos ──────────────────────────────────
            for i, (x, y, w, h) in enumerate(rostos):
                nome = cache_nomes[i] if i < len(cache_nomes) else "Rosto"
                cor  = COR_CONHECIDO if (nome not in ("Rosto", "Desconhecido")) else COR_ROSTO

                # Confiança (somente DNN)
                if usando_dnn and i < len(deteccoes):
                    conf = deteccoes[i][4]
                    label = f"{nome} ({conf:.0%})"
                else:
                    label = nome

                cv2.rectangle(frame, (x, y), (x+w, y+h), cor, 2)

                # Fundo semitransparente para o texto
                label_bg_y = max(y - 30, 0)
                overlay2 = frame.copy()
                cv2.rectangle(overlay2, (x, label_bg_y), (x + w, y), (30, 30, 30), -1)
                cv2.addWeighted(overlay2, 0.5, frame, 0.5, 0, frame)

                cv2.putText(
                    frame, label,
                    (x + 6, y - 8),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, cor, 1,
                )

            # ── HUD de status ─────────────────────────────────────────────────
            t_now = time.perf_counter()
            fps   = 1.0 / max(t_now - t_prev, 1e-6)
            t_prev = t_now
            desenhar_info_tela(frame, fps, len(rostos), mostrar_fps,
                               backend_nome, usando_dnn)

            cv2.imshow("CorePulseMonitor – Reconhecimento Facial", frame)

            # ── Leitura de teclas ─────────────────────────────────────────────
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord("q") or tecla == 27:   # Q ou Esc
                break
            elif tecla == ord("c"):
                path = salvar_captura(frame, PASTA_CAPTURAS)
                print(f"Captura salva: {path}")
            elif tecla == ord("f"):
                mostrar_fps = not mostrar_fps
            elif tecla == ord("g") and usando_dnn:
                # Alterna entre GPU e CPU
                if usar_gpu:
                    backend_nome = configurar_backend_cpu(net)
                    usar_gpu = False
                    print("Alternado para: CPU")
                else:
                    backend_nome = configurar_backend_gpu(net)
                    usar_gpu = "GPU" in backend_nome or "OpenCL" in backend_nome
                    print(f"Alternado para: {backend_nome}")

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\nMonitoramento encerrado.")


if __name__ == "__main__":
    main()
