# def main():
#     print("Hello from desenvolvimento-agentes-ia!")

# if __name__ == "__main__":
#     main()

from google.adk import Agent
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
    tools=[list_fatura]
    )

