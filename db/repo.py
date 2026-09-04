from db.engine import async_session
from db.models import TicketEscalationModel, TicketModel

async def create_ticket(model: TicketModel) -> TicketModel:
    """Cria e persiste um novo ticket no banco de dados."""
    async with async_session.begin() as session:
        session.add(model)
        await session.flush()
        await session.refresh(model)
        return model


async def update_ticket(model: TicketModel) -> TicketModel:
    """Atualiza o estado de um ticket existente."""
    async with async_session.begin() as session:
        merged_model = await session.merge(model)
        await session.flush()
        await session.refresh(merged_model)
        return merged_model


async def get_ticket(ticket_id: str) -> TicketModel | None:
    """Busca um ticket pelo seu ID."""
    async with async_session.begin() as session:
        return await session.get(TicketModel, ticket_id)

async def create_ticket_escalation(
    ticket_escalation: TicketEscalationModel
) -> TicketEscalationModel:
    async with async_session.begin() as session:
        session.add(ticket_escalation)
        await session.flush()
    return ticket_escalation


async def get_ticket_escalation(
    ticket_id: str
) -> TicketEscalationModel | None:
    async with async_session.begin() as session:
        result = await session.execute(
            select(TicketEscalationModel).where(
                TicketEscalationModel.ticket_id == ticket_id
            )
        )
        return result.scalars().first()