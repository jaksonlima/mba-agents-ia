from google.adk.workflow import node
from google.adk import Context, Event
from google.adk.events import EventActions

from agents.ticket_resolution.agents.attendant.agent import AttendantOutput
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
        return Event(actions=EventActions(route="refuse"))

    ctx.state["ticket_message"] = ticket.message
    ctx.state["classification_justification"] = classification.justification 
    ctx.state["customer_id"] = ticket.customer_id 

    return Event(actions=EventActions(route="attendant"))

@node 
async def refuse_ticket_node(ticket_id: str):
    ticket = await repo.get_ticket(ticket_id)
    
    if not ticket:
         return Event(message=f"Ticket {ticket_id} não encontrado.")  # type: ignore

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


@node 
async def finish_ticket_node(ticket_id: str, node_input: AttendantOutput):
    ticket = await repo.get_ticket(ticket_id)
    
    if not ticket:
         return Event(message=f"Ticket {ticket_id} não encontrado.")  # type: ignore

    message = node_input.message
    ticket.status = TicketStatus.RESOLVED if node_input.status == "success" else TicketStatus.FAILED

    await repo.update_ticket(ticket)
    return Event(message=message)