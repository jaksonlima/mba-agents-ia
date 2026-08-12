from db.engine import async_session
from db.models import TicketModel


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