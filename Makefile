.PHONY: run test test-direct mock-n8n help

# Default target
help:
	@echo "Available commands:"
	@echo "  make run         - Run the FastAPI server"
	@echo "  make test        - Run the API tests"
	@echo "  make test-direct - Run direct tests bypassing the API"
	@echo "  make mock-n8n    - Run the mock n8n server"

# Run the FastAPI server
run:
	python -m uvicorn main:app --reload

# Run the API tests
test:
	python -m pytest tests/

# Run the direct test
test-direct:
	python test_order_direct.py

# Run the mock n8n server
mock-n8n:
	python mock_n8n_server.py 