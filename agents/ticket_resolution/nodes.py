from google.adk.workflow import node
from google.adk import Context, Event

from db import repo
from db.models import TicketCategory, TicketStatus


@node
async def triage_ticket_node(ctx: Context):
    ticket_id = ctx.state.get("ticket_id")

    ticket = await repo.get_ticket(ticket_id)

    if not ticket:
        return Event(message=f"Ticket {ticket_id} não encontrado.")  # type: ignore

    classification = ticket.classification

    if classification.category == TicketCategory.OUT_OF_SCOPE:
        message = (
            "Olá! Este canal é exclusivo para suporte da Acme Cloud (faturamento, "
            "bugs, recursos e configuração da plataforma). Não identificamos um "
            "pedido de suporte na sua mensagem. Se precisar de ajuda com a "
            "plataforma, descreva o problema e abriremos um novo atendimento."
        )
        ticket.response = message
        ticket.status = TicketStatus.RESOLVED

        await repo.update_ticket(ticket)
        return Event(message=message)
