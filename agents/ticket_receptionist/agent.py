from google.adk.agents import Agent
from google.adk.apps import App
from .subagents.ticket_classifier.agent import (TicketClassifierOutput, ticket_classifier_subagent, CLASSIFIER_OUTPUT_KEY)
from google.adk.tools import ToolContext
from google.genai.types import Content
from db import repo
from db.models import TicketModel, ClassificationModel

def _mensagem_usuario(content: Content | None) -> str:
    if not content or not content.parts:
        return ""
    return "\n".join([part.text for part in content.parts if part.text])

async def register_ticker(tool_context: ToolContext): 
    """
    Registrar um ticket de suporte na central de atendimento da Acme Cloud.
    Args:
        tool_context (ToolContext): Contexto da ferramenta, contém informações do ticket.
    Returns:
        dict: Mensagem de confirmação do registro do ticket.
    """

    if not CLASSIFIER_OUTPUT_KEY in tool_context.state:
        return {"status": "error", "message": "Não foi possível classificar o ticket. Por favor, tente novamente."}

    classification = TicketClassifierOutput.model_validate(tool_context.state[CLASSIFIER_OUTPUT_KEY])

    user_message = _mensagem_usuario(tool_context.user_content)

    if not user_message:
        raise ValueError("A mensagem do usuario está vazia. Não é possível registrar o ticket.")

    ticker_created = await repo.create_ticket(
        TicketModel(
            customer_id=tool_context.user_id,
            message=user_message,
            classification=ClassificationModel(
                **classification.model_dump()
            ),
        )
    )

    return {"status": "success", "ticket_id": ticker_created.id}

_INSTRUCTION_RECEPTIONIST = """
Você é o Recepcionista de tickets da central de atendimento da Acme Cloud.
Se o usuário perguntar sobre algum ticket já resgistrado, pesquise o status do ticket e dé uma resposta adequada.
Se o usuário pedir para listar tickets,
forneça uma lista dos tickets registrados de acordo comos critérios fornecidos. (por exemplo, status, categoria, etc.)

Se o usuario pedir para criar um ticket, pertunte qual é a mensagem do ticket e, em seguida.
ative o processo de classificação do ticket e proceda com registro do ticket.
"""

root_agent = Agent(
    name="ticket_receptionist",
    description="Responsável por receber tickets de suporte da Acme Cloud e classificá-los",
    model="gemini-3.5-flash",
    instruction=_INSTRUCTION_RECEPTIONIST,
    sub_agents=[
        ticket_classifier_subagent
    ],
    tools=[register_ticker]
)

app = App(
    root_agent=root_agent,
    name="ticket_receptionist",
)