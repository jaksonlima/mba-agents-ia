
from google.adk.agents import Agent
from google.adk.apps import App
from agents.ticket_receptionist.subagents.ticket_classifier.agent import ticket_classifier_subagent

_INSTRUCTION_RECEPTIONIST = """
Você é o Recepcionista de tickets da central de atendimento da Acme Cloud.
Se o usuário perguntar sobre algum ticket já resgistrado, pesquise o status do ticket e dé uma resposta adequada.
Se o usuário pedir para listar tickets,
forneça uma lista dos tickets registrados de acordo comos critérios fornecidos. (por exemplo, status, categoria, etc.)
"""

root_agent = Agent(
    name="ticket_receptionist",
    description="Responsável por receber tickets de suporte da Acme Cloud e classificá-los",
    model="gemini-3.5-flash",
    instruction=_INSTRUCTION_RECEPTIONIST,
    sub_agents=[
        ticket_classifier_subagent
    ]
)

app = App(
    root_agent=root_agent,
    name="ticket_receptionist",
)