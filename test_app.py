import chainlit as cl

@cl.on_chat_start
async def start():
    await cl.Message(content="¡Hola! Si puedes ver esto, Chainlit está funcionando correctamente.").send()
