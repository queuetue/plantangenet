# WebSocket Bidirectional Comdec

A bidirectional WebSocket comdec for real-time streaming and backchannel communication between Plantangenet compositors and frontend clients (like React apps).

## Features

- **Bidirectional Communication**: Sends compositor frames to clients AND receives messages/events from clients
- **NATS-style Messages**: Structured JSON messages with type, data, metadata envelope
- **Topic Subscriptions**: Clients can subscribe/unsubscribe to specific message types
- **Real-time Streaming**: Low-latency WebSocket connections with automatic ping/keepalive
- **Session Context**: Each client gets a unique stream ID and can maintain session state
- **Error Handling**: Robust error handling with automatic client cleanup

## Message Format

All messages follow a NATS-style envelope format:

```json
{
  "type": "message_type",
  "data": { ... },
  "metadata": { ... },
  "timestamp": 1234567890.123,
  "stream_id": "client_uuid"
}
```

## Usage

### Backend (Compositor)

```python
from plantangenet.comdec.websocket import WebSocketBidirectionalComdec
from plantangenet.compositor.fb_types import SoftwareFBCompositor

# Message handler for incoming events from frontend
async def handle_frontend_message(message, stream):
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "player_action":
        action = data.get("action")
        # Apply action to game state
        game.move_player(action)
        
        # Send confirmation back
        await stream.send_message("action_confirmed", {
            "action": action,
            "success": True
        })

# Create comdec with message handler
comdec = WebSocketBidirectionalComdec(
    port=8765,
    message_handler=handle_frontend_message
)

# Attach to compositor
compositor = SoftwareFBCompositor(width=200, height=200)
compositor.add_comdec(comdec)

# Initialize server
await comdec.initialize()

# Send frames (compositor → frontend)
await compositor.broadcast_frame(frame_data, metadata)

# Broadcast to specific topic
await comdec.broadcast_to_topic("chat", "message", {
    "user": "alice",
    "text": "Hello world!"
})
```

### Frontend (React/JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8765');

// Send player action (frontend → backend)
ws.send(JSON.stringify({
    type: "player_action",
    data: { action: "move_left", player_id: "alice" }
}));

// Subscribe to game events
ws.send(JSON.stringify({
    type: "subscribe",
    data: { topics: ["game_events", "chat"] }
}));

// Handle incoming messages (backend → frontend)
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    if (message.type === "frame_data") {
        // Update game display
        updateGameVisuals(message.data);
    } else if (message.type === "chat_message") {
        // Display chat
        addChatMessage(message.data);
    }
};
```

## Built-in Message Types

### Client to Server
- `subscribe`: Subscribe to message topics
- `unsubscribe`: Unsubscribe from topics
- `ping`: Ping server (responds with `pong`)
- Custom types handled by your message handler

### Server to Client
- `connected`: Sent when client connects
- `subscribed`/`unsubscribed`: Subscription confirmations
- `pong`: Response to ping
- `frame_array`: Numpy array frames
- `frame_data`: Dictionary frames
- `error`: Error messages
- Custom types sent by your application

## Demo

Run the demo to see it in action:

```bash
# Start the demo server
python examples/demo_websocket_bidirectional.py

# Open the HTML client
open examples/websocket_demo_client.html
```

The demo includes:
- Real-time game state streaming
- Interactive paddle controls
- Chat system with topic subscriptions
- Frame streaming (visual and data)

## Integration with React

For React integration, create a WebSocket context:

```jsx
import React, { createContext, useContext, useEffect, useState } from 'react';

const WebSocketContext = createContext();

export function WebSocketProvider({ children }) {
    const [ws, setWs] = useState(null);
    const [gameState, setGameState] = useState({});
    
    useEffect(() => {
        const websocket = new WebSocket('ws://localhost:8765');
        
        websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            if (message.type === 'game_state') {
                setGameState(message.data);
            }
        };
        
        setWs(websocket);
        return () => websocket.close();
    }, []);
    
    const sendAction = (action) => {
        if (ws) {
            ws.send(JSON.stringify({
                type: 'player_action',
                data: { action, player_id: 'react_player' }
            }));
        }
    };
    
    return (
        <WebSocketContext.Provider value={{ gameState, sendAction }}>
            {children}
        </WebSocketContext.Provider>
    );
}

export const useWebSocket = () => useContext(WebSocketContext);
```

## Architecture

The WebSocket comdec extends the existing comdec pattern:

1. **Extends BaseComdec**: Follows the same interface as other comdecs
2. **Integrates with Compositors**: Receives frames via `consume()` method
3. **Runs WebSocket Server**: Background thread serves WebSocket connections
4. **Manages Clients**: Tracks active connections and subscriptions
5. **Routes Messages**: Forwards incoming messages to your handler
6. **Handles Cleanup**: Automatically removes dead connections

## Testing

Run the tests:

```bash
pytest python/tests/test_websocket_comdec.py -v
```

## Requirements

- `websockets` library (added to requirements.txt)
- Python 3.8+
- Plantangenet comdec system
