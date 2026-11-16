# API examples

Start the service with `uvicorn app.main:app --reload`.

```bash
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/api/dashboard/student?user_ref=STU-0817"
curl "http://127.0.0.1:8000/api/ai/features?role=student&pillar=Agentic%20AI"
curl -X POST http://127.0.0.1:8000/api/ai/answer -H "Content-Type: application/json" -d '{"role":"student","question":"What is my next class?","provider":"deterministic"}'
curl -X POST http://127.0.0.1:8000/api/requests/preview -H "Content-Type: application/json" -d '{"role":"parent","user_ref":"PAR-0817","request_type":"payment_guidance","details":"Prepare fee balance guidance."}'
```

Every AI answer includes its detected intent, grounded source records, next action, provider mode, and safety boundary. Request previews are never submitted.
