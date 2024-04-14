import base64
import os
import time

from flask import Flask, request
from asyncio import new_event_loop, set_event_loop, sleep
from pyppeteer import launch

app = Flask(__name__)

def _generate_path() -> str:
    """
    Gera o caminho para o arquivo de imagem onde a captura de tela será salva.

    Retorna:
        str: O caminho completo para o arquivo de imagem.
    """
    return os.path.join(os.path.dirname(__file__), 'assets', 'images', f"screen_{round(time.time() * 1000)}.jpeg")

def _image_to_base64(path: str) -> str:
    """
    Converte uma imagem em formato de arquivo para uma string base64.

    Parâmetros:
        path (str): O caminho para o arquivo de imagem.

    Retorna:
        str: Uma string base64 representando a imagem.
    """
    with open(path, 'rb') as image:
        encoded_string = base64.b64encode(image.read()).decode('utf-8')
    return encoded_string

async def _generate_screenshot(
        target_url: str,
        width: int,
        height: int,
        timeout: float,
        path: str
) -> bool:
    """
    Gera uma captura de tela de uma página da web.

    Parâmetros:
        target_url (str): A URL da página da web a ser capturada.
        width (int): A largura da janela do navegador.
        height (int): A altura da janela do navegador.
        timeout (float): O tempo em segundos a aguardar após carregar a página antes de capturar a tela.
        path (str): O caminho completo para o arquivo de imagem onde a captura de tela será salva.

    Retorna:
        bool: True se a captura de tela foi bem-sucedida, False caso contrário.
    """
    try:
        # Inicializa o navegador Pyppeteer
        browser = await launch(
            executablePath='/usr/bin/chromium',
            args=[
                "--no-sandbox",
                "--single-process",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-zygote",
            ],
            userDataDir="/tmp",
            autoClose=False,
            headless=True,
            ignoreHTTPSErrors=True,
            logLevel="ERROR",
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )
        # Abre uma nova página no navegador
        page = await browser.newPage()
        # Define o tamanho da janela do navegador
        await page.setViewport({"width": width, "height": height})
        # Navega até a URL alvo
        await page.goto(target_url)
        # Aguarda um tempo determinado
        await sleep(timeout)
        # Captura uma screenshot da página
        await page.screenshot({"fullPage": False, "path": path, "type": "jpeg"})
        # Fecha o navegador
        await browser.close()
        return True
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return False
    
async def _take_multiple_screenshots(
        target_url: str,
        interval_inside: float,
        width: int,
        height: int,
        timeout: float,
        path: str,
        screenshots: int
) -> None:
    """
    Captura múltiplas screenshots de uma página da web.

    Parâmetros:
        target_url (str): A URL da página da web a ser capturada.
        interval_inside (float): O intervalo de tempo em segundos entre cada captura de tela.
        width (int): A largura da janela do navegador.
        height (int): A altura da janela do navegador.
        timeout (float): O tempo em segundos a aguardar após carregar a página antes de capturar a tela.
        path (str): O caminho completo para o arquivo de imagem onde as capturas de tela serão salvas.
        screenshots (int): O número de capturas de tela a serem feitas.

    Retorna:
        None
    """
    for _ in range(screenshots):
        # Chama o método para gerar uma screenshot
        await _generate_screenshot(
            target_url=target_url,
            width=width,
            height=height,
            timeout=timeout,
            path=path
        )
        # Aguarda um intervalo antes de capturar a próxima screenshot
        await sleep(interval_inside)

@app.route("/", methods=["GET"])
def handle_screenshot_request():
    if request.method == "GET":
        try:
            request_args = request.args
            target_url = request_args.get("targetUrl")
            width = int(request_args.get("Width", 800))
            height = int(request_args.get("Height", 600))
            timeout = float(request_args.get("TimeOut", 5.0))
            interval_inside = float(request_args.get("intervalInside", 1.0))
            interval_outside = int(request_args.get("intervalOutside", 1))
            screenshots = int(request_args.get("screenshot", 1))
        
            if not target_url:
                return {"Message": "Bad Request"}, 400
            
            path = _generate_path()
            loop = new_event_loop()
            set_event_loop(loop)
            for _ in range(interval_outside):
                # Executa o método para capturar múltiplas screenshots
                loop.run_until_complete(_take_multiple_screenshots(target_url, interval_inside, width, height, timeout, path, screenshots))
            # Converte a imagem capturada em base64
            encoded_image = _image_to_base64(path)
            return {"response": encoded_image}, 200

        except ValueError as e:
            return {"Message": f"Bad Request {e}"}, 400
        
if __name__ == "__main__":
    app.run(debug=True)
