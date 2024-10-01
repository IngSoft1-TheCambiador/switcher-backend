# Switcher ~ Backend ~ The cambiador

This repository holds the backend code of our *Switcher* implementation. To
install all requirements, run `pip install -r requirements.txt`. *Use a virtual
environment, always*.

Assuming the requirements are installed, the server can be lifted calling
`uvicorn main:app`. The expected output is:

```bash
 uvicorn src.main:app
INFO:     Started server process [23706]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

To run a test, first run the server and only then the testing script.

