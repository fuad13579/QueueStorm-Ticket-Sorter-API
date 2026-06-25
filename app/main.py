from fastapi import FastAPI

from app.classifier import classify_ticket
from app.schemas import TicketRequest, TicketResponse

app = FastAPI(title="QueueStorm Ticket Sorter API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/sort-ticket", response_model=TicketResponse)
def sort_ticket(ticket: TicketRequest) -> TicketResponse:
    result = classify_ticket(ticket_id=ticket.ticket_id, message=ticket.message)
    return TicketResponse(**result)