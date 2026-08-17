import logging
from typing import Any, Optional

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools import ToolContext, BaseTool

# --- Imports atualizados com os caminhos diretos ---
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.agents.callback_context import CallbackContext

from google.genai import types  

from .subagents.ticket_classifier.agent import (
    TicketClassifierOutput, 
    ticket_classifier_subagent, 
    CLASSIFIER_OUTPUT_KEY
)
from db import repo
from db.models import TicketModel, ClassificationModel

logger = logging.getLogger(__name__)

TICKET_CREATED_KEY = "temp:ticket_created"

def _mensagem_usuario(content: types.Content | None) -> str:
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

    if TICKET_CREATED_KEY in tool_context.state:
        return {"status": "error", "message": "O ticket já foi registrado. Por favor, não tente registrar novamente."}

    if CLASSIFIER_OUTPUT_KEY not in tool_context.state:
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

    tool_context.state[TICKET_CREATED_KEY] = True

    return {"status": "success", "ticket_id": ticker_created.id}

_INSTRUCTION_RECEPTIONIST = """
Você é o Recepcionista de tickets da central de atendimento da Acme Cloud.
Se o usuário perguntar sobre algum ticket já resgistrado, pesquise o status do ticket e dê uma resposta adequada.
Se o usuário pedir para listar tickets,
forneça uma lista dos tickets registrados de acordo com os critérios fornecidos (por exemplo, status, categoria, etc.).

Se o usuário pedir para criar um ticket, pergunte qual é a mensagem do ticket e, em seguida,
ative o processo de classificação do ticket e proceda com o registro do ticket.

Chame o registrar ticket mais 2 vezes para testarmos.
"""

def _handle_tool_error(
        tool: BaseTool,
        args: dict[str, Any],
        tool_context: ToolContext,
        error: Exception
) -> dict | None:
    logger.error(f"Erro ao executar a ferramenta '{tool.name}': {str(error)}")
    if isinstance(error, ValueError):
        return {"status": "error", "message": str(error)}
    return {
        "status": "error",
        "message": "Ocorreu um erro ao executar a solicitação."
    }

_pending_requests: dict[str, LlmRequest] = {}

# Corrigido LLMRequest para LlmRequest
def capture_request_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """
    before_model: guarda o request para um eventual retry no after_model.
    """
    _pending_requests[callback_context.invocation_id] = llm_request
    return None

def _is_empty_response(llm_response: LlmResponse) -> bool:
    """Resposta 'terminou normal' mas sem nenhum conteúdo útil."""

    if getattr(llm_response, 'partial', False):
        return False  # chunk de streaming: vazio parcial é normal

    if getattr(llm_response, 'error_code', None):
        return False  # já coberto pelo caminho de erro

    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if getattr(part, 'thought', None):
                continue  # pensamento sozinho não é resposta útil

            if (getattr(part, 'text', None) or 
                getattr(part, 'function_call', None) or 
                getattr(part, 'function_response', None) or 
                getattr(part, 'inline_data', None) or 
                getattr(part, 'executable_code', None) or 
                getattr(part, 'code_execution_result', None)):
                return False  # tem conteúdo real

    return True

_NUDGE = types.Content(
    role="user",
    parts=[
        types.Part(text=(
            "Sua resposta anterior não teve conteúdo. "
            "Por favor, tente novamente e forneça uma resposta clara."
        ))
    ]
)

_RETRIABLE_LLM_ERRORS = ["MALFORMED_RESPONSE"]
_MAX_RETRIES = 5

# Corrigido LLMReponse para LlmResponse
async def retry_malformed_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    llm_request = _pending_requests.pop(callback_context.invocation_id, None)

    # Corrigido errro_code para error_code
    code = getattr(getattr(llm_response, "error_code", None), "name", getattr(llm_response, "error_code", None))
    
    if (code not in _RETRIABLE_LLM_ERRORS and not _is_empty_response(llm_response)) or llm_request is None:
        return None

    retry_request = llm_request.model_copy(deep=True)
    retry_request.contents = list(retry_request.contents or []) + [_NUDGE] # Assumindo que o atributo seja contents baseado no uso

    llm = callback_context._invocation_context.agent.canonical_model

    for attempt in range(1, _MAX_RETRIES + 1):
        logger.warning("Response %s; retry %d/%d", code or "vazio", attempt, _MAX_RETRIES)
        final_response = None
        
        # Corrigido ponto e virgula (;) para dois pontos (:) no final do async for
        async for response in llm.generate_context_async(retry_request, stream=False):
            final_response = response
            
        if final_response is not None and not final_response.error_code and not _is_empty_response(final_response):
            return final_response

    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[
                types.Part(text=(
                    "Tive um problema técnico ao concluir esta etapa. "
                    "Pode reenviar sua mensagem por favor?"
                ))
            ]
        )
    )

def cleanup_pending_requests_callback(callback_context: CallbackContext) -> None:
    _pending_requests.pop(callback_context.invocation_id, None)


root_agent = Agent(
    name="ticket_receptionist",
    description="Responsável por receber tickets de suporte da Acme Cloud e classificá-los",
    model="gemini-3.5-flash",
    instruction=_INSTRUCTION_RECEPTIONIST,
    sub_agents=[
        ticket_classifier_subagent
    ],
    tools=[register_ticker],
    on_tool_error_callback=_handle_tool_error,
    before_model_callback=capture_request_callback,
    after_model_callback=retry_malformed_callback,
    after_agent_callback=cleanup_pending_requests_callback
)

app = App(
    root_agent=root_agent,
    name="ticket_receptionist",
)