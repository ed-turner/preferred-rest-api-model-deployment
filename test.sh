
docker-compose up -d

sleep 10

curl http://0.0.0.0:8001/model/status

echo ""

curl -X POST http://127.0.0.1:8000/model/add/?model_name='lassolog'&model_uri='http://lassolog:5002/invocations'

curl -X POST http://127.0.0.1:8001/model/change/?model_name="lassolog"

echo ""

curl http://0.0.0.0:8000/model/status

echo ""

curl -X POST http://0.0.0.0:8000/model/change?model_name="lassolog"

curl -d '{"model_name":"lassolog", "model_uri":"http://lassolog:5002/invocations"}' -H "Content-Type: application/json" -X POST http://0.0.0.0:8000/model/add

echo ""

for i in 1 2 3 4 5 6 7 8 9 10
do
   curl -H "Content-Type: application/json" -d '{"apr": 100.0, "lender_id": 1000, "lead_id": "004cfd11-4d3f-4ba2-ad7d-0c0bb215e1f6", "offer_id": 101}' -X POST http://0.0.0.0:8000/model/inference
   sleep 5
done


echo ""

docker-compose down
