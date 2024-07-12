import os
import sys
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
import requests

# Cargar las variables de entorno desde el archivo .env
load_dotenv(dotenv_path=r'C:\Users\Alan\Documents\CodeProjects\InstagramReels\.env')

# Variables OpenAI
api_key = os.getenv("OPENAI_API_KEY")
openai = OpenAI(api_key=api_key) # Inicializa el cliente de OpenAI con API key

# Configuraciones generales cargadas desde el archivo .env
IMAGE_FOLDER = os.getenv('IMAGE_FOLDER')
NEWS_VIDEO_OUTPUT = os.getenv('NEWS_VIDEO_OUTPUT')
FONT_PATH = os.getenv('FONT_PATH')
IMAGE_SIZE = (int(os.getenv('IMAGE_SIZE_WIDTH')), int(os.getenv('IMAGE_SIZE_HEIGHT')))
AUDIO_FOLDER = os.getenv('AUDIO_FOLDER')
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')
client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)

if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

def find_image_paths(news_id): 
    image_paths = []
    i = 1
    while True:
        image_path = os.path.join(IMAGE_FOLDER, f"Dato{news_id}_{i}.jpg")
        if not os.path.isfile(image_path):
            break
        image_paths.append(image_path)
        i += 1
    print(f"Se encontraron {len(image_paths)} imágenes para la noticia {news_id}")
    return image_paths

def split_text_at_commas(text):
    segments = text.split(',')  # Ajusta para asegurar que cada segmento termina en una coma
    segments = [segment.strip() + ',' for segment in segments if segment.strip()]
    if segments[-1].endswith(','):
        segments[-1] = segments[-1][:-1]  # Remueve la última coma si no es necesaria
    return segments

def generate_audio_eleven_labs(text, voice_id, audio_filename):
    if not audio_filename.endswith(".mp3"):
        audio_filename += ".mp3"

    response = client.text_to_speech.convert(
        voice_id=voice_id,
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
        ),
    )
    save_file_path = os.path.join(AUDIO_FOLDER, audio_filename)
    with open(save_file_path, "wb") as f:
        for chunk in response:
            f.write(chunk)
    print(f"{save_file_path}: A new audio file was saved successfully!")
    return save_file_path

def generate_image_with_text(image_path, text):
    base_image = Image.open(image_path).convert("RGBA").resize(IMAGE_SIZE)
    txt = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt)
    
    # Configuración de la fuente
    font_size = 30
    font = ImageFont.truetype(FONT_PATH, font_size)
    max_width = int(base_image.width * 0.8)  # Máximo 80% del ancho de la imagen
    
    # Dividir el texto en líneas ajustadas al ancho máximo
    lines = wrap_text(text, font, max_width, draw)  # Pasa draw aquí
    text_height = font_size * len(lines)

    # Posicionamiento del texto
    text_x = base_image.width // 2
    text_y = base_image.height - text_height - 50  # 50 píxeles del borde inferior
    
    # Dibujar el rectángulo negro semi-transparente
    rectangle_margin = 20
    rectangle_height = text_height + 2 * rectangle_margin
    rectangle_y = text_y - rectangle_margin

    draw.rectangle(
        [(text_x - max_width // 2 - rectangle_margin, rectangle_y),
         (text_x + max_width // 2 + rectangle_margin, rectangle_y + rectangle_height)],
        fill=(0, 0, 0, 127))  # Rectángulo semi-transparente

    # Dibujar el texto línea por línea
    current_y = text_y
    for line in lines:
        line_width = draw.textlength(line, font=font)
        line_x = text_x - line_width // 2
        draw.text((line_x, current_y), line, font=font, fill="white")
        current_y += font_size  # Moverse hacia abajo para la siguiente línea

    # Combinar la imagen base con el texto y el rectángulo
    combined = Image.alpha_composite(base_image, txt)
    return combined.convert("RGB")

def wrap_text(text, font, max_width, draw):
    """Divide el texto en líneas asegurando que no exceda el ancho máximo."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        # Comprueba el ancho del texto provisional
        if draw.textlength(test_line, font=font) > max_width:
            lines.append(' '.join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    
    # Asegúrate de añadir la última línea si hay palabras restantes
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

import openai

def generate_and_save_images(news, images_path, number_of_images=3):
    os.makedirs(images_path, exist_ok=True)
    for i in range(number_of_images):
        # Generar un prompt más detallado para cada noticia
        prompt = f"Crear una imagen que visualice esta noticia: {news}. La imagen debe capturar los elementos claves y el contexto de la noticia de manera artística y relevante."
        try:
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                quality="standard"
            )

            #print("Respuesta completa de la API:")
            #print(response)

            # Asegurarse de que la respuesta contiene datos y acceder correctamente a la URL
            if response.data:
                image_url = response.data[0].url
                print(f"URL de la imagen: {image_url}")
                print("\n" + "-"*80 + "\n")

                filename = f"NewsImage_{uuid.uuid4().hex}.png"
                path_to_save_image = os.path.join(images_path, filename)

                # Descargar y guardar la imagen
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    with open(path_to_save_image, 'wb') as file:
                        file.write(image_response.content)
                    print(f"Imagen descargada y guardada en {path_to_save_image}")
                else:
                    print("Error al descargar la imagen desde:", image_url)
            else:
                print("No se encontraron datos de imagen en la respuesta.")

        except Exception as e:
            print(f"Error generando la imagen: {e}")

def create_complete_video(news_list):
    final_clips = []
    for index, news in enumerate(news_list, start=1):
        images_path = os.path.join(IMAGE_FOLDER, f"News_{index}")
        os.makedirs(images_path, exist_ok=True)
        
        print(f"Generando imágenes para la noticia {index}")
        generate_and_save_images(news, images_path)

        image_files = [os.path.join(images_path, file) for file in os.listdir(images_path)]
        text_chunks = split_text_at_commas(news)

        for image_path, text_chunk in zip(image_files, text_chunks):
            audio_filename = f"audio_{index}_{uuid.uuid4()}.mp3"
            audio_path = generate_audio_eleven_labs(text_chunk, "VR6AewLTigWG4xSOukaG", audio_filename)
            
            img_with_text = generate_image_with_text(image_path, text_chunk)
            img_with_text_path = image_path.replace(".jpg", "_with_text.jpg")
            img_with_text.save(img_with_text_path)
            
            clip = ImageClip(img_with_text_path).set_duration(AudioFileClip(audio_path).duration)
            clip.audio = AudioFileClip(audio_path)
            final_clips.append(clip)

    if final_clips:
        video = concatenate_videoclips(final_clips, method="compose")
        video.write_videofile(NEWS_VIDEO_OUTPUT, fps=24)
        print("Video creado con éxito.")



#------------------------------------------------------------------------------------------------ MAIN ------------------------------------------------------------------------------------------------
def main(news_list):
    if not news_list:
        print("No se proporcionaron noticias para procesar.")
        sys.exit(1)
    create_complete_video(news_list)

if __name__ == "__main__":
    noticias = [
    "Intervención del Ministerio de Trabajo: El Ministerio de Trabajo de Argentina, ha detenido una huelga planeada por los pilotos de aerolíneas, permitiendo que los vuelos operen normalmente mientras continúan las negociaciones salariales.",
    "Viajes Presidenciales: El presidente de Argentina, está actualmente en Estados Unidos asistiendo a una reunión, que reúne a figuras prominentes de los sectores tecnológico y empresarial.",
    "Desarrollos Económicos: Buenos Aires ha sido nombrada la ciudad más habitable de Sudamérica, debido a sus fuertes instituciones educativas, como la Universidad de Buenos Aires y la estabilidad general.",
    ]
    main(noticias)


#    "Relaciones Internacionales y Medio Ambiente: Argentina se comprometió a retirar unos paneles solares instalados por error en territorio chileno tras una advertencia del presidente de Chile, Gabriel Boric. Este incidente ha generado tensiones diplomáticas entre los dos países​",
#    "Adquisición Militar: Argentina ha realizado su mayor adquisición de aeronaves militares en décadas, comprando 24 jets F-16 de Dinamarca. Esta compra es un paso significativo en los esfuerzos del país por modernizar sus capacidades de defensa",
#    "Reformas Gubernamentales: En un esfuerzo por modernizar la economía y reducir el tamaño del estado, el gobierno argentino sigue adelante con sus planes para privatizar Aerolíneas Argentinas y otras firmas estatales. Esta medida forma parte de un paquete de reformas promovido por el presidente Javier Milei, destinado a fomentar la austeridad y la eficiencia en la administración pública"

