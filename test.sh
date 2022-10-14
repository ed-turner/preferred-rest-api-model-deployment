
docker-compose up -d

sleep 10

curl http://0.0.0.0:8000/model/status

echo ""

curl -X POST http://0.0.0.0:8000/model/change?model_name="ridge-log"

echo ""

curl http://0.0.0.0:8000/model/status

echo ""

curl -X POST http://0.0.0.0:8000/model/change?model_name="lasso-log"

echo ""

for i in 1 2 3 4 5 6 7 8 9 10
do
   curl -X POST http://0.0.0.0:8000/model/inference -H "Content-Type: application/json" -d '{"apr": 100.0, "lender_id": 1000, "lead_id": "004cfd11-4d3f-4ba2-ad7d-0c0bb215e1f6", "offer_id": 101}'
   sleep $RANDOM % 30
done


echo ""

docker-compose down
