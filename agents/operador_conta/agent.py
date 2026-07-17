# def main():
#     print("Hello from desenvolvimento-agentes-ia!")

# if __name__ == "__main__":
#     main()

from aiohttp import Payload
from google.adk import Agent
from google.adk.tools import ToolContext
# from google.adk.models.lite_llm import LiteLlm

FATURAS = [
    {
        "id": "1",
        "cliente_id": "123",
        "valor": 100.0,
        "data_vencimento": "2024-06-30",
        "data_emissao": "2024-06-01",
        "status": "pendente",
    },
    {
        "id": "2",
        "cliente_id": "456",
        "valor": 200.0,
        "data_vencimento": "2024-07-30",
        "data_emissao": "2024-07-01",
        "status": "pago",
    },
]

def list_faturas(client_id: str):
    """
    Lista as faturas de um cliente específico com base no ID do cliente.
    Args:
     - client_id (str): O ID do cliente cujas faturas serão listadas.
    Returns:
     - dict: Um dicionário contendo uma lista de faturas do cliente.
    """
    return {"faturas": [fatura for fatura in FATURAS if fatura["cliente_id"] == client_id]}

ASSINATURAS: dict[str, dict] = {
    "cliente_123": {
        "plano": "Pro",
        "status": "ativo",
        "renovacao": "2024-07-15",
    },
}

def cancelar_assinatura(client_id: str, senha: str, tool_context: ToolContext) -> dict:
    """
    Cancela a assinatura de um cliente específico com base no ID do cliente.
    Args:
     - client_id (str): O ID do cliente cuja assinatura será cancelada.
     - senha (str): A senha do cliente para autenticação.
    Returns:
     - dict: Um dicionário indicando o status do cancelamento.
    """

    if tool_context.tool_confirmation is None:
        tool_context.request_confirmation(
            hint="O valor da assinatura é alto. Tem certeza que deseja cancelar a assinatura?",
            payload={
                "client_id": client_id,
                "senha": ""
            }
        )
        return {"status": "aguardando confirmação."}
    
    if not tool_context.tool_confirmation.confirmed:
        return {"status": "nao_cancelada", "message": "Cancelamento não confirmado pelo usuário."}
    
    if senha != "senha_secreta":
        return {"status": "nao_cancelada", "message": "Senha incorreta. Cancelamento não autorizado."}

    assinatura = ASSINATURAS.get(client_id)
    if assinatura is not None:
        assinatura["status"] = "cancelada"

    return {"status": "cancelada", "client_id": client_id}

consultor_faturas_subagent = Agent(
    name="consultor_faturas_subagent",
    instruction="""
    Você é um consultor de faturas do ACME.
    Você é responsável por:
     - Listar as faturas de um cliente específico.
    """,
    model="gemini-3.1-flash-lite",
    tools=[list_faturas]
)

consultor_assinatura_subagent = Agent(
    name="consultor_assinatura_subagent",
    instruction="""
    Você é um consultor de assinaturas do ACME.
    Você é responsável por:
     - Informar ao cliente sobre sua assinatura: o plano, status e renovação.
    """,
    model="gemini-3.1-flash-lite",
    tools=[cancelar_assinatura]
)

root_agent = Agent(
    name="operador_conta_subagent",
    instruction="""
    Voce é um atendente de conta interatico do ACME.
    Você çé responsável por:
    O usuario precisa fornecer o ID do cliente para que você possa buscar as informaçoes corretas. 
    Seja cordial e direto   
     """,
    model="gemini-3.1-flash-lite",
    # model=LiteLlm(model="antropics/claude-sonnet-4-6"),
    # tools=[cancelar_assinatura]
    sub_agents=[consultor_faturas_subagent, consultor_assinatura_subagent]
    )

