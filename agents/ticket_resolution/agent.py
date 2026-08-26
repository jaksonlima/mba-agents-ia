from google.adk import Workflow
from google.adk.workflow import START

from agents.ticket_resolution.nodes import triage_ticket_node
root_agent = Workflow(
    name="ticket_resolution",
    description="descricao do agente",
    edges=[
        (START, triage_ticket_node),
    ]
)
