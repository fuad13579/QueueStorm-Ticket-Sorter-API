from fastapi import FastAPI

from app.classifier import classify_ticket
from app.schemas import TicketRequest, TicketResponse

# Create the FastAPI application that serves the health check and ticket-sorting routes.
app = FastAPI(title="QueueStorm Ticket Sorter API")


@app.get("/health")
def health() -> dict:
# Return a simple status payload so monitors can confirm the service is alive.
    return {"status": "ok"}


@app.post("/sort-ticket", response_model=TicketResponse)
def sort_ticket(ticket: TicketRequest) -> TicketResponse:
# Accept one ticket, classify it with the rule engine, and return the structured result.
    result = classify_ticket(ticket_id=ticket.ticket_id, message=ticket.message)
    return TicketResponse(**result)