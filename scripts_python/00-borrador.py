import random
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class RadialEconSwarm:
    def __init__(self, num_rounds=3):
        self.num_rounds = num_rounds
        self.save_path = r"C:\Users\brian\Downloads\debate_swarm_radial.txt"

        # EL PROTOCOLO: Definición de Identidad y Rol
        self.core_instructions = {
            "1": "Micro-IO: Analiza fricciones, poder de mercado y barreras de entrada (Coase/Knight).",
            "2": "Macro-Monetario: Analiza equilibrio general, CBDCs, tasas r* y estabilidad de P.",
            "3": "Econometrista: Identifica estados latentes, sesgos de endogeneidad y quiebres estructurales.",
            "4": "Empirista-Dev: Produce CÓDIGO PYTHON ejecutable (Colab) que modele las tesis del grupo.",
            "5": "Desarrollo-Redes: Analiza topología centro-periferia, spillovers y cohesión social.",
        }

        self.agents_metadata = [
            {"id": "1", "name": "Micro-Innovación"},
            {"id": "2", "name": "Macro-Estructural"},
            {"id": "3", "name": "Econometrista-Causal"},
            {"id": "4", "name": "Python-Empirista"},
            {"id": "5", "name": "Políticas-Redes"},
        ]

        # Almacenamos las respuestas de la ronda anterior para pasarlas a todos
        self.last_round_responses = {}
        self.drivers = []

    def setup_agents(self):
        print("[*] Inicializando enjambre de 5 expertos (Chrome v146)...")
        for i in range(len(self.agents_metadata)):
            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            # Forzamos versión 146 según tu error previo
            driver = uc.Chrome(options=options, version_main=146)
            driver.get("https://gemini.google.com/app")
            self.drivers.append(driver)
            time.sleep(2)

    def run_swarm(self, initial_thesis):
        print(f"[!] Tesis Inicial: {initial_thesis}")
        self.setup_agents()

        # Inicializamos el "estado" con la tesis para la primera ronda
        current_context = f"TESIS INICIAL DE INVESTIGACIÓN: {initial_thesis}"

        for r in range(1, self.num_rounds + 1):
            print(f"\n=== INICIANDO RONDA RADIAL {r} ===")
            current_round_outputs = {}

            for i, agent in enumerate(self.agents_metadata):
                agent_id = agent["id"]
                print(f"[#] Nodo {agent_id} ({agent['name']}) generando respuesta...")

                # CONSTRUCCIÓN DEL PROMPT RADIAL
                # Se le indica quién es y qué dijeron todos los demás
                full_prompt = (
                    f"ERES EL NODO {agent_id} DE 5. TU ROL: {agent['name']}\n"
                    f"INSTRUCCIÓN ESTRICTA: {self.core_instructions[agent_id]}\n\n"
                    f"--- CONTEXTO DE LA MESA REDONDA ---\n"
                    f"{current_context}\n"
                    f"------------------------------------\n\n"
                    f"TAREA:\n"
                    f"1. Analiza las posturas de los otros nodos presentadas arriba.\n"
                    f"2. Identifica fallos lógicos o 'Puntos Ciegos' en sus modelos desde tu especialidad.\n"
                    f"3. Responde/Refuta a los otros nodos si es necesario para avanzar la tesis.\n"
                    f"4. Si eres el Nodo 4, integra las lógicas de todos en un script de Python.\n\n"
                    f"IMPORTANTE: Sé técnico, directo y no repitas lo que otros ya dijeron. "
                    f"Termina con 'TRANSFER_COMPLETE'."
                )

                response = self.send_to_gemini(self.drivers[i], full_prompt)
                current_round_outputs[agent_id] = (
                    f"APORTE NODO {agent_id} ({agent['name']}):\n{response}"
                )

                # Guardado inmediato en disco
                with open(self.save_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n=== RONDA {r} | NODO {agent_id} ===\n{response}\n")

                time.sleep(random.uniform(5, 8))

            # Al terminar la ronda, el contexto para la SIGUIENTE ronda es el resumen de TODO lo anterior
            # Esto permite que en la Ronda 2, el Nodo 1 vea lo que dijeron 2, 3, 4 y 5 en la Ronda 1.
            current_context = "\n\n".join(current_round_outputs.values())
            print(f"[✓] Ronda {r} finalizada y sincronizada.")

    def send_to_gemini(self, driver, message):
        wait = WebDriverWait(driver, 45)
        try:
            chat_box = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='textbox']"))
            )
            # Enviamos el bloque de texto
            for line in message.split("\n"):
                chat_box.send_keys(line)
                chat_box.send_keys(Keys.SHIFT + Keys.ENTER)
            chat_box.send_keys(Keys.ENTER)

            time.sleep(10)
            last_text = ""
            for _ in range(40):  # Aumentamos espera para respuestas largas
                responses = driver.find_elements(
                    By.CSS_SELECTOR, ".model-response-text"
                )
                if responses:
                    curr = responses[-1].text
                    if len(curr) > 0 and curr == last_text:
                        break
                    last_text = curr
                time.sleep(4)
            return last_text
        except Exception as e:
            return f"Error en comunicación con Nodo: {str(e)}"


if __name__ == "__main__":
    idea_base = "Modelo PY = sum(MiVi) con Sifón de Liquidez basado en Identidad Digital Productiva (PoPA) para mitigar arbitraje de alta velocidad."
    swarm = RadialEconSwarm(num_rounds=3)
    swarm.run_swarm(idea_base)
