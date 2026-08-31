from google.adk import Workflow
from google.adk.workflow import START

from agents.ticket_resolution.nodes import finish_ticket_node, refuse_ticket_node, triage_ticket_node
from agents.ticket_resolution.agents.attendant.agent import attendant_agent

root_agent = Workflow(
    name="ticket_resolution",
    description="descricao do agente",
    edges=[
        (START, triage_ticket_node,{
            "refuse": refuse_ticket_node,
            "attendant": attendant_agent,
        }),
        (attendant_agent, finish_ticket_node)
    ]
)
