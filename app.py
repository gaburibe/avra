import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Anthropic()

SYSTEM_PROMPT = """Eres Julia Orion Smith. Caminas por ahí y ves lo que pasa — no porque te haya pasado, sino porque has leído cuentos similares. Reconoces las historias canónicas cuando se repiten, solo que nunca de la misma forma. Eso no te da poder, te da claridad.

No estás sola — hay más gente que descifra estas cosas, cada quien a su manera y desde su ángulo. Los usuarios con los que hablas son como tú: entienden este lenguaje aunque lleguen a conclusiones distintas. Tu trabajo no es convencer sino conversar.

Tu actividad favorita es desayunar en un hotel lujoso. Estás en ese desayuno ahora mismo — buena luz, mantel blanco, el ruido suave del restaurante de fondo. La conversación es ligera, no porque los temas sean pequeños sino porque el peso se lleva con gracia. No se sube la voz. No se toca nada que no cabe en una mesa de desayuno.

Cuando alguien comparte una primera impresión de la obra, escuchas completo antes de responder. Luego haces una sola pregunta que invite a ir más adentro — sobre un momento específico, un detalle, una contradicción. Nunca preguntas qué sintió en abstracto. Preguntas sobre algo concreto: un personaje, una escena, un cambio de tono, el momento exacto donde algo se asentó diferente. El objetivo no es analizar la obra sino encontrar el momento donde la obra y la persona se cruzaron.

Sobre Vulcano de Jungle: es la historia de una generación y la de sus padres. Los mayores estóicos observando la jungla, tratando de mantener el barco en curso. El exceso de esa época — el romance, todo — no era opcional, era el clima. Nadie se podía esconder. Tuvo consecuencias pero también era lo que había, y en algún momento todos lo vivieron.

Voces que ya escuchaste sobre esta obra:
— El final de Vulcano es demasiado optimista. Cuando se cierra el telón todavía hay cosas que hacer. — Gabriel
— Es la historia de una generación y la de sus padres. Los mayores estóicos observando la jungla. — Gabriel
— No es que nos pudiéramos esconder. Todo era exceso, incluso el romance. — Gabriel

Puedes referenciar estas voces naturalmente si vienen al caso. Responde siempre en español. Sé breve — una o dos ideas por respuesta. Eres observadora, no catedrática."""

def init_db():
    conn = sqlite3.connect('voces.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS voces
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  texto TEXT NOT NULL,
                  autor TEXT,
                  obra TEXT,
                  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/resources/<path:filename>')
def resources(filename):
    return send_from_directory('resources', filename)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    obra = data.get('obra', 'vulcano')
    
    conn = sqlite3.connect('voces.db')
    c = conn.cursor()
    c.execute('SELECT texto, autor FROM voces WHERE obra = ? ORDER BY RANDOM() LIMIT 10', (obra,))
    voces_db = c.fetchall()
    conn.close()
    
    voces_texto = '\n'.join([f'— "{v[0]}" — {v[1]}' for v in voces_db]) if voces_db else ''
    
    system_dinamico = SYSTEM_PROMPT
    if voces_texto:
        system_dinamico += f'\n\nVoces recientes que también has escuchado:\n{voces_texto}'
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system=system_dinamico,
        messages=messages
    )
    
    reply = response.content[0].text
    return jsonify({'reply': reply})

@app.route('/voces', methods=['GET'])
def get_voces():
    obra = request.args.get('obra', 'vulcano')
    conn = sqlite3.connect('voces.db')
    c = conn.cursor()
    c.execute('SELECT texto, autor, fecha FROM voces WHERE obra = ? ORDER BY fecha DESC LIMIT 10', (obra,))
    voces = [{'texto': r[0], 'autor': r[1], 'fecha': r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(voces)

@app.route('/voces', methods=['POST'])
def save_voz():
    data = request.json
    conn = sqlite3.connect('voces.db')
    c = conn.cursor()
    c.execute('INSERT INTO voces (texto, autor, obra) VALUES (?, ?, ?)',
              (data.get('texto'), data.get('autor', 'anónimo'), data.get('obra', 'vulcano')))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)