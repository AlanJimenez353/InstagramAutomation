import os
import sys
import uuid
import textwrap
import requests
from dotenv import load_dotenv
from datetime import datetime
from pydub import AudioSegment
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

# Cargar las variables de entorno desde el archivo .env
load_dotenv(dotenv_path=r'C:\Users\Alan\Documents\CodeProjects\InstagramReels\.env')

# Configuraciones generales cargadas desde el archivo .env
IMAGE_FOLDER = os.getenv('IMAGE_FOLDER')
NEWS_VIDEO_OUTPUT = os.getenv('NEWS_VIDEO_OUTPUT')
FONT_PATH = os.getenv('FONT_PATH')
IMAGE_SIZE = (int(os.getenv('IMAGE_SIZE_WIDTH')), int(os.getenv('IMAGE_SIZE_HEIGHT')))
AUDIO_FOLDER = os.getenv('AUDIO_FOLDER')
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')
client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)

# Lista de noticias


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

def split_text(text, num_parts):
    wrapped_text = textwrap.wrap(text, width=40)
    chunk_size = max(1, len(wrapped_text) // num_parts)
    return ["\n".join(wrapped_text[i:i + chunk_size]) for i in range(0, len(wrapped_text), chunk_size)]

def generate_image_with_text(image_path, text):
    base_image = Image.open(image_path).convert("RGBA").resize(IMAGE_SIZE)
    txt = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    
    draw = ImageDraw.Draw(txt)
    font = ImageFont.truetype(FONT_PATH, 30)
    
    # Position the text at the bottom of the image
    margin = 10
    lines = text.split('\n')
    total_height = sum([draw.textbbox((0, 0), line, font=font)[3] for line in lines])
    y = base_image.height - total_height - margin

    for line in lines:
        width, height = draw.textbbox((0, 0), line, font=font)[2:]
        x = (base_image.width - width) / 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += height

    combined = Image.alpha_composite(base_image, txt)
    return combined.convert("RGB")

    
def generate_audio_eleven_labs(text, voice_id, audio_filename):
    # Hacer la llamada a la API usando el cliente
    response = client.text_to_speech.convert(
        voice_id=voice_id,
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2",  # Ajusta el model_id según necesites
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # Guardar el archivo de audio
    save_file_path = os.path.join(AUDIO_FOLDER, f"{audio_filename}.mp3")
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")
    return save_file_path

def create_news_clip(news, news_index, images):
    clips = []
    text_chunks = split_text(news, len(images))
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")  # Fecha y hora actual para el nombre del archivo

    for idx, (image, text_chunk) in enumerate(zip(images, text_chunks)):
        img_with_text = generate_image_with_text(image, text_chunk)
        img_with_text_path = image.replace(".jpg", f"_with_text_{idx}.jpg")
        img_with_text.save(img_with_text_path)

        audio_filename = f"audio_{news_index}_{idx}_{date_str}"
        audio_path = generate_audio_eleven_labs(text_chunk, "onwK4e9ZLuTAKqWW03F9", audio_filename)
        if audio_path is None:
            print(f"Audio generation failed for text chunk {idx}. Skipping this clip.")
            continue

        audio_clip = AudioFileClip(audio_path)
        clip = ImageClip(img_with_text_path).set_duration(audio_clip.duration).set_audio(audio_clip)
        clips.append(clip)
    return clips

def create_complete_video(news_list):
    final_clips = []
    for index, news in enumerate(news_list, start=1):
        print(f"Procesando la noticia {index}")
        images = find_image_paths(index)
        if images:
            # Añadir el index como segundo argumento
            news_clip = create_news_clip(news, index, images)
            final_clips.extend(news_clip)
        else:
            print(f"No se encontraron imágenes para la noticia {index}")
    
    if final_clips:
        video = concatenate_videoclips(final_clips, method="compose")
        video.write_videofile(NEWS_VIDEO_OUTPUT, fps=24)
        print("Video creado con éxito.")
    else:
        print("No se pudieron crear los clips de video.")


def main(news_list):
    if not news_list:
        print("No se proporcionaron noticias para procesar.")
        sys.exit(1)
    create_complete_video(news_list)

if __name__ == "__main__":
    # Ejemplo de cómo podrías configurar las noticias al momento de ejecutar el script
    # Podrías obtener esto de un archivo, una base de datos, una API, etc.
    noticias = [
    "Inflación y Política Económica: La inflación mensual en Argentina ha disminuido a un 4.2%, el nivel más bajo desde enero de 2022. Este descenso se marca como el quinto mes consecutivo de desaceleración",
    "Conservación Ambiental: Científicos y ambientalistas argentinos devolvieron al mar a un grupo de pingüinos magallánicos que habían sido rescatados y tratados por malnutrición e hipotermia​",
]
    main(noticias)


#    "Relaciones Internacionales y Medio Ambiente: Argentina se comprometió a retirar unos paneles solares instalados por error en territorio chileno tras una advertencia del presidente de Chile, Gabriel Boric. Este incidente ha generado tensiones diplomáticas entre los dos países​",
#    "Adquisición Militar: Argentina ha realizado su mayor adquisición de aeronaves militares en décadas, comprando 24 jets F-16 de Dinamarca. Esta compra es un paso significativo en los esfuerzos del país por modernizar sus capacidades de defensa",
#    "Reformas Gubernamentales: En un esfuerzo por modernizar la economía y reducir el tamaño del estado, el gobierno argentino sigue adelante con sus planes para privatizar Aerolíneas Argentinas y otras firmas estatales. Esta medida forma parte de un paquete de reformas promovido por el presidente Javier Milei, destinado a fomentar la austeridad y la eficiencia en la administración pública"
