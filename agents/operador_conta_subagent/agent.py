# def main():
#     print("Hello from desenvolvimento-agentes-ia!")

# if __name__ == "__main__":
#     main()

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

def list_fatura(client_id: str):
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

    assinatura = ASSINATURAS.pop(client_id)
    if assinatura is not None:
        assinatura["status"] = "cancelada"

    return {"status": "cancelada", "client_id": client_id}

root_agent = Agent(
    name="operador_conta",
    instruction="""
    Voce é um atendente de conta interatico do ACME.
    Você çé responsável por:
     - Informar ao cliente sobre sua assinatura: o plano, status e renovação.
     - Tirar dúvidas sobre o serviço as faturas do cliente.
     - Cancelar a assinatura do cliente, se solicitado.
    O usuario precisa fornecer o ID do cliente para que você possa buscar as informaçoes corretas. 
    """,
    model="gemini-3.1-flash-lite",
    # model=LiteLlm(model="antropics/claude-sonnet-4-6"),
    tools=[list_fatura, cancelar_assinatura]
    )

