import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_france import FranceTaxBenefitSystem

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

tax_benefit_system = FranceTaxBenefitSystem()


def walDecompositionLeafs(node):
    children = node.get("children")
    if children:
        for child in children:
            yield from walDecompositionLeafs(child)
        # Note: Ignore nodes that are the total of their children.
    else:
        yield node


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    decomposition = None
    period = None
    simulation = None
    situation = None
    while True:
        data = await websocket.receive_json()
        calculate = False
        for key, value in data.items():
            if key == "calculate":
                calculate = True
            if key == "decomposition":
                print("Received decomposition.")
                decomposition = value
                continue
            if key == "period":
                print("Received period.")
                period = value
                continue
            if key == "situation":
                print("Received situation.")
                situation = value
                simulation_builder = SimulationBuilder()
                simulation = simulation_builder.build_from_entities(tax_benefit_system, situation)
                continue

        if not calculate:
            continue
        print("Calculating…")

        errors = {}
        if decomposition is None:
            errors["decomposition"] = "Missing value"
        if period is None:
            errors["period"] = "Missing value"
        if situation is None or simulation is None:
            errors["situation"] = "Missing value"
        if len(errors) > 0:
            await websocket.send_json(dict(errors=errors))
            continue

        for node in walDecompositionLeafs(decomposition):
            value = simulation.calculate_add(node["code"], period)
            print(f"Calculated {node['code']}: {value}")
            await websocket.send_json(dict(code=node["code"], value=value.tolist()))
            await asyncio.sleep(0)
