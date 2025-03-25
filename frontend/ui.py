import gradio as gr
from src.chatbot import PregnancyChatbot

# Inicializa el chatbot
chatbot = PregnancyChatbot()

def chat_interface(user_input, history):
    response = chatbot.send_message(user_input)
    history = history or []
    history.append((user_input, response))
    return history, history

with gr.Blocks() as iface:
    gr.Markdown("### 🌸 Pregnancy Chatbot 🌸")
    chatbot_ui = gr.Chatbot()
    user_input = gr.Textbox(placeholder="Escribe tu pregunta sobre el embarazo aquí...")
    submit_button = gr.Button("Enviar")

    submit_button.click(chat_interface, [user_input, chatbot_ui], [chatbot_ui, chatbot_ui])

# Lanza la interfaz
if __name__ == "__main__":
    iface.launch()