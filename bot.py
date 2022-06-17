#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Primero, se definen unas funciones de callback. Después, esas funciones se le pasan
al Dispatcher y se registran en sus respectivos lugares.
Entonces, el bot se arranca y corre hasta que se presione Ctrl-C en la línea de comandos.
Uso:
Envía /start para iniciar la conversación.
Presiona Ctrl-C en la línea de comandos o envía una señal para parar el proceso del bot.
"""

import logging
import analyze
from csv import DictReader
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Habilitamos logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Creamos los estados del chat
DECISION, MVOZ, AAUDIO, LOCALIZACION, PROCESAR, START = range(6)

# Creamos las variables del usuario
latitud = -1
longitud = -1

# Función que contiene el estado inicial del bot y pasa al siguiente estado
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Hola! Soy un bot que analiza audios buscando sonidos de aves.\n'
        'Envia /salir para cancelar la conversación conmigo.\n'
        'Para empezar necesito que me envíes tu ubicación.\n'
        'Hacerlo me ayudará a determinar mejor los resultados. Si no quieres envíame /saltar'
    )

    return LOCALIZACION

# Función que contiene el estado después de elegir nota de voz del bot y pasa al siguiente estado en funcion de la respuesta
def eaudio(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("%s ha elegido enviarme: %s", user.first_name, update.message.text)
    update.message.reply_text(
        '¡Perfecto! Envíame un mensaje de voz y lo analizo',
        reply_markup=ReplyKeyboardRemove(),
    )

    return MVOZ

# Función que contiene el estado de procesamiento de la nota de voz y pasa al siguiente estado en función de la respuesta
def paudio(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    id_file = update.message.voice.file_id
    user_voz = context.bot.get_file(id_file)
    user_voz.download('./voice.ogg')
    logger.info("%s me ha enviado un mensaje de voz", user.first_name)
    logger.info("El mensaje de voz dura: %s", update.message.voice.duration)
    if update.message.voice.duration >= 3:
        update.message.reply_text(
            '¡Perfecto! Me pongo a analizarlo, dame un momento.',
        )
        analyze.clasifica('./voice.ogg', latitud, longitud)
        with open('result.csv', 'r') as doc:
            csv_reader = DictReader(doc, delimiter=';')
            for row in csv_reader:
                if float(row['Confidence']) > 0.4:
                    update.message.reply_text(
                        'Distingo un ' + row['ScientificName'] + ' con una seguridad de un ' + str(float(row['Confidence']) * 100) + '%',
                    )
                    especie = row['ScientificName']
                    update.message.reply_text(
                        'Si quieres mas información sobre los ' + row[
                            'ScientificName'] + ' puedes seguir el siguiente enlace: ' + 'https://es.wikipedia.org/wiki/' + especie.replace(' ', '_'),
                    )
            update.message.reply_text(
                'Eso fue todo lo que pude distinguir.\n'
                'Gracias por pasar pasar un rato conmigo.\n'
                'Si quieres analizar otro archivo envía /start pero si no, '
                'espero que hayas tenido una buena experiencia y pasa un buen día', reply_markup=ReplyKeyboardRemove()
            )

        return ConversationHandler.END
    else:
        update.message.reply_text(
            'No llega a los 3 segundos. Por favor, envíame uno de al menos 3 segundos para que pueda analizarlo',
        )

        return MVOZ

# Función que contiene el estado después de utilizar el atajo en la nota de voz del bot escribiendo "archivo"
# y pasa al siguiente estado en funcion de la respuesta
def paudioej(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Ha usado el atajo del ejemplo")
    update.message.reply_text('¡Perfecto! Me pongo a analizarlo, dame un momento.',)
    analyze.clasifica('./XC563936Soundscape.mp3', latitud, longitud)
    with open('result.csv', 'r') as doc:
        csv_reader = DictReader(doc, delimiter=';')
        for row in csv_reader:
            if float(row['Confidence']) > 0.4:
                update.message.reply_text('Distingo un ' + row['ScientificName'] + ' con una seguridad de un ' + str(float(row['Confidence']) * 100) + '%',)
                especie = row['ScientificName']
                update.message.reply_text(
                    'Si quieres mas información sobre los ' + row[
                        'ScientificName'] + ' puedes seguir el siguiente enlace: ' + 'https://es.wikipedia.org/wiki/' + especie.replace(' ', '_'),
                )
        update.message.reply_text(
            'Eso fue todo lo que pude distinguir.\n'
            'Gracias por pasar pasar un rato conmigo.\n'
            'Si quieres analizar otro archivo envía /start pero si no, '
            'espero que hayas tenido una buena experiencia y pasa un buen día', reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END

# Función que contiene el estado en el cual el usuario no ha enviado la nota de voz al bot y vuelve a repetir
# el estado anterior
def error_audio(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("%s no me ha enviado el mensaje de voz. Envió otra cosa", user.first_name)
    update.message.reply_text(
        'Habías quedado en enviarme un mensaje de voz.\n'
        'Envíame un mensaje de voz o envíame /salir para cancelar la conversación',
    )

    return MVOZ

# Función que contiene el estado después de elegir el archivo .mp3 del bot y pasa al siguiente estado en funcion de la respuesta
def earchivo(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("%s ha elegido enviarme: %s", user.first_name, update.message.text)
    update.message.reply_text(
        '¡Perfecto! Envíame un archivo de audio en formato mp3 y lo analizo',
    )

    return AAUDIO

# Función que contiene el estado de procesamiento del archivo .mp3 y pasa al siguiente estado en función de la respuesta
def parchivo(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    id_file = update.message.audio.file_id
    user_archivo = context.bot.get_file(id_file)
    user_archivo.download('./voice.mp3')
    logger.info("%s me ha enviado un archivo de audio", user.first_name)
    logger.info("El archivo dura: %s", update.message.audio.duration)
    if update.message.audio.duration >= 3:
        update.message.reply_text(
            '¡Perfecto! Me pongo a analizarlo, dame un momento.',
        )
        """Llamamos al BirdNet con el archivo y la ubicación (por defecto si no la quiso facilitar)"""
        analyze.clasifica('./voice.mp3', latitud, longitud)
        """Leemos el csv resultado"""
        with open('result.csv', 'r') as doc:
            csv_reader = DictReader(doc, delimiter=';')
            for row in csv_reader:
                if float(row['Confidence']) > 0.4:
                    update.message.reply_text(
                        'Distingo un ' + row['ScientificName'] + ' con una seguridad de un ' + str(
                            float(row['Confidence']) * 100) + '%',
                    )
                    especie = row['ScientificName']
                    update.message.reply_text(
                        'Si quieres mas información sobre los ' + row[
                            'ScientificName'] + ' puedes seguir el siguiente enlace: ' + 'https://es.wikipedia.org/wiki/' + especie.replace(
                            ' ', '_'),
                    )
            update.message.reply_text(
                'Eso fue todo lo que pude distinguir.\n'
                'Gracias por pasar pasar un rato conmigo.\n'
                'Si quieres analizar otro archivo envía /start pero si no, '
                'espero que hayas tenido una buena experiencia y pasa un buen día', reply_markup=ReplyKeyboardRemove()
            )

        return ConversationHandler.END
    else:
        update.message.reply_text(
            'No llega a los 3 segundos. Por favor, envíame uno de al menos 3 segundos para que pueda analizarlo',
        )


    return AAUDIO

# Función que contiene el estado después de utilizar el atajo en el archivo .mp3 del bot escribiendo "archivo"
# y pasa al siguiente estado en funcion de la respuesta
def parchivoej(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Ha utilizado el atajo del ejemplo")
    update.message.reply_text('¡Perfecto! Me pongo a analizarlo, dame un momento.',)
    """Llamamos al BirdNet con el archivo y la ubicación (por defecto si no la quiso facilitar)"""
    analyze.clasifica('./XC558716Soundscape.mp3', latitud, longitud)
    """Leemos el csv resultado"""
    with open('result.csv', 'r') as doc:
        csv_reader = DictReader(doc, delimiter=';')
        for row in csv_reader:
            if float(row['Confidence']) > 0.4:
                update.message.reply_text(
                    'Distingo un ' + row['ScientificName'] + ' con una seguridad de un ' + str(
                        float(row['Confidence']) * 100) + '%',
                )
                especie = row['ScientificName']
                update.message.reply_text(
                    'Si quieres mas información sobre los ' + row[
                        'ScientificName'] + ' puedes seguir el siguiente enlace: ' + 'https://es.wikipedia.org/wiki/' + especie.replace(
                        ' ', '_'),
                )
        update.message.reply_text(
            'Eso fue todo lo que pude distinguir.\n'
            'Gracias por pasar pasar un rato conmigo.\n'
            'Si quieres analizar otro archivo envía /start pero si no, '
            'espero que hayas tenido una buena experiencia y pasa un buen día', reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END

# Función que contiene el estado en el cual el usuario no ha enviado el archivo .mp3 al bot y vuelve a repetir
# el estado anterior
def error_archivo(update: Update, context: CallbackContext) -> int:
    """Bucle cuando no envía un archivo como dijo antes."""
    user = update.message.from_user
    logger.info("%s no me ha enviado el archivo de audio. Envió otra cosa", user.first_name)
    update.message.reply_text(
        'Habías quedado en enviarme un archivo de audio en formato mp3.\n'
        'Envíame un archivo de audio o envíame /salir para cancelar la conversación',
    )

    return AAUDIO

# Función que contiene el estado en el cual el usuario no ha enviado ubicción o saltado el paso y vuelve a repetir
# el estado anterior
def error_location(update: Update, context: CallbackContext) -> int:
    """Bucle cuando no envía una ubicacion o lo salta."""
    user = update.message.from_user
    logger.info("%s Ni saltó la ubicación ni la ha enviado", user.first_name)
    update.message.reply_text(
        'Por favor, envíame una ubicación, /saltar para continuar o /salir para cancelar la conversación.',
    )

    return START

# Función que contiene el estado en el cual el usuario ha enviado la ubicación al bot y pasa al siguiente estado
def location(update: Update, context: CallbackContext) -> int:
    """Guarda la ubicación y pide el tipo de archivo a analizar."""
    reply_keyboard = [['Voz', 'Archivo']]
    user = update.message.from_user
    longitud = update.message.location.longitude
    latitud = update.message.location.latitude
    logger.info(
        "Ubicación de %s: %f / %f", user.first_name, latitud, longitud
    )
    update.message.reply_text(
        '¡Gracias! Tener tu ubicación me ayuda a reducir las posibilidades.\n'
        '¿Ahora que vas a enviarme, un mensaje de voz o un archivo de audio en formato mp3?\n '
        'Recuerda que tienen que durar al menos 3 segundos para que pueda reconocerlo.\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Voz o Archivo?'
        ),
    )

    return DECISION
# Función que contiene el estado en el cual el usuario ha saltado el paso de la ubicación al bot y pasa al siguiente estado
def skip_location(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Voz', 'Archivo']]
    user = update.message.from_user
    logger.info("El usuario %s no ha querido facilitar su localización.", user.first_name)
    update.message.reply_text(
        'Bueno, tendré que arreglármelas sin ella.\n'
        'Te recuerdo que esto disminuye los valores de confianza en las respuestas.\n'
        '¿Ahora que vas a enviarme, un mensaje de voz o un archivo de audio en formato mp3?\n'
        'Recuerda que tienen que durar al menos 3 segundos para que pueda reconocerlo.\n',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Voz o Archivo?'
        ),
    )

    return DECISION

# Función que contiene el estado en el cual el usuario cancela la conversación
def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("El usuario %s ha cancelado la conversación.", user.first_name)
    update.message.reply_text(
        'Gracias por pasar pasar un rato conmigo.\n'
        'Espero que hayas tenido una buena experiencia y pasa un buen día', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


# Función que arranca y mantiene el bot
def main() -> None:
    """Arranca el bot."""
    # Crear el updater y pasarle el token del bot.
    updater = Updater("5029909552:AAH0hy82GD_EicAyFBajTmVTg1qy-tJaVJY")

    # Preparar el dispatcher para registrar los handlers
    dispatcher = updater.dispatcher

    # Añadir los conversation handler con los estados necesarios para el funcionamiento del bot
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [MessageHandler(Filters.location, location),
                CommandHandler('saltar', skip_location),
                CommandHandler('salir', cancel),
                MessageHandler(~Filters.location, error_location)],
            LOCALIZACION: [MessageHandler(Filters.location, location),
                CommandHandler('saltar', skip_location),
                CommandHandler('salir', cancel),
                MessageHandler(~Filters.location and ~Filters.regex('^(/saltar)$'), error_location)],
            DECISION: [MessageHandler(Filters.regex('^(Voz)$'), eaudio),
                CommandHandler('salir', cancel),
                MessageHandler(Filters.regex('^(Archivo)$'), earchivo)],
            MVOZ: [MessageHandler(Filters.voice, paudio),
                CommandHandler('salir', cancel),
                MessageHandler(Filters.regex('^(ejemplo)$'), paudioej),
                MessageHandler(~Filters.voice and ~Filters.regex('^(ejemplo)$'), error_audio)],
            AAUDIO: [MessageHandler(Filters.audio, parchivo),
                CommandHandler('salir', cancel),
                MessageHandler(Filters.regex('^(ejemplo)$'), parchivoej),
                MessageHandler(~Filters.audio and ~Filters.regex('^(ejemplo)$'), error_archivo)],
        },
        fallbacks=[CommandHandler('salir', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Arrancar el Bot
    updater.start_polling()

    # El bot estará corriendo hasta que se pulse Ctrl-C o el proceso reciba SIGINT,
    # SIGTERM or SIGABRT. Esto se debe usar, desde que start_polling() es no bloqueante y parará el bot
    updater.idle()


if __name__ == '__main__':
    main()