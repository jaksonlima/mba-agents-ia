import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

logger = logging.getLogger(__name__)

_DEFAULT_RETRIABLE_ERRORS = ("MALFORMED_FUNCTION_CALL", "MALFORMED_RESPONSE")

_DEFAULT_NUDGE = (
    "Sua resposta anterior não teve conteúdo válido. "
    "Por favor, tente novamente e forneça uma resposta clara."
)

_DEFAULT_FALLBACK = (
    "Tive um problema técnico ao concluir esta etapa. "
    "Pode reenviar sua mensagem por favor?"
)


class RetryMalformedResponsePlugin(BasePlugin):
    """Reexecuta a chamada ao modelo quando a resposta vem malformada ou vazia.

    Guarda o LlmRequest no before_model_callback e, se o after_model_callback
    receber uma resposta inutilizável, refaz a geração com um nudge anexado.
    """

    def __init__(
        self,
        name: str = "retry_malformed_response",
        max_retries: int = 5,
        retriable_errors: tuple[str, ...] = _DEFAULT_RETRIABLE_ERRORS,
        nudge_text: str = _DEFAULT_NUDGE,
        fallback_text: str = _DEFAULT_FALLBACK,
    ):
        super().__init__(name=name)
        self.max_retries = max_retries
        self.retriable_errors = retriable_errors
        self.nudge = types.Content(role="user", parts=[types.Part(text=nudge_text)])
        self.fallback_text = fallback_text
        self._pending_requests: dict[str, LlmRequest] = {}

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        self._pending_requests[callback_context.invocation_id] = llm_request
        return None

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        llm_request = self._pending_requests.pop(callback_context.invocation_id, None)
        if llm_request is None:
            return None

        code = self._error_code(llm_response)
        if code not in self.retriable_errors and not self._is_empty_response(llm_response):
            return None

        retry_request = llm_request.model_copy(deep=True)
        retry_request.contents = list(retry_request.contents or []) + [self.nudge]

        llm = callback_context._invocation_context.agent.canonical_model

        for attempt in range(1, self.max_retries + 1):
            logger.warning(
                "Resposta %s; retry %d/%d", code or "vazia", attempt, self.max_retries
            )
            final_response = None
            async for response in llm.generate_content_async(retry_request, stream=False):
                final_response = response

            if (
                final_response is not None
                and not final_response.error_code
                and not self._is_empty_response(final_response)
            ):
                return final_response

        return LlmResponse(
            content=types.Content(
                role="model", parts=[types.Part(text=self.fallback_text)]
            )
        )

    async def after_agent_callback(self, *, agent, callback_context: CallbackContext):
        self._pending_requests.pop(callback_context.invocation_id, None)
        return None

    @staticmethod
    def _error_code(llm_response: LlmResponse) -> Optional[str]:
        code = getattr(llm_response, "error_code", None)
        return getattr(code, "name", code)

    @staticmethod
    def _is_empty_response(llm_response: LlmResponse) -> bool:
        """Resposta 'terminou normal' mas sem nenhum conteúdo útil."""
        if getattr(llm_response, "partial", False):
            return False  # chunk de streaming: vazio parcial é normal

        if getattr(llm_response, "error_code", None):
            return False  # já coberto pelo caminho de erro

        if llm_response.content and llm_response.content.parts:
            for part in llm_response.content.parts:
                if getattr(part, "thought", None):
                    continue  # pensamento sozinho não é resposta útil

                if (
                    getattr(part, "text", None)
                    or getattr(part, "function_call", None)
                    or getattr(part, "function_response", None)
                    or getattr(part, "inline_data", None)
                    or getattr(part, "executable_code", None)
                    or getattr(part, "code_execution_result", None)
                ):
                    return False

        return True
