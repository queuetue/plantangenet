"""
FastAPI server for exposing session and agent status endpoints.
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware


class SessionStatusServer:
    """FastAPI server that exposes session and agent status endpoints."""

    def __init__(self, port: int = 8081):
        self.app = FastAPI(title="Plantangenet Session Dashboard")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.port = port
        self.session = None
        self.current_game = None
        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/api/session", response_class=JSONResponse)
        async def get_session_status():
            """Get complete session status as JSON."""
            if not self.session:
                raise HTTPException(
                    status_code=404, detail="No active session")

            status = {
                "session_id": self.session.short_id,
                "agents": {},
                "activities": {},
                "policy": {},
                "compositors": {},
                "current_game": None
            }

            # Get agent status
            for agent_id, agent in self.session.agents.items():
                status["agents"][agent_id] = {
                    "id": agent.short_id,
                    "name": getattr(agent, 'name', agent_id),
                    "type": agent.__class__.__name__,
                    "status": getattr(agent, 'status', lambda: {})(),
                    "capabilities": getattr(agent, 'capabilities', {}),
                    "disposition": getattr(agent, 'disposition', 'unknown')
                }

            # Get activity status
            for activity_id, activity in getattr(self.session, 'activities', {}).items():
                status["activities"][activity_id] = {
                    "id": activity_id,
                    "type": activity.__class__.__name__,
                    "members": list(getattr(activity, 'members', [])),
                    "available": getattr(activity, '_available', lambda: False)(),
                    "full": getattr(activity, '_is_activity_full', lambda: False)()
                }

            # Get compositor status
            for comp_id, comp in self.session.compositors.items():
                status["compositors"][comp_id] = {
                    "id": comp_id,
                    "type": comp.__class__.__name__,
                    "active": getattr(comp, 'active', False)
                }

            # Current game state if available
            if self.current_game:
                status["current_game"] = self.current_game.get_game_state()

            return status

        @self.app.get("/session", response_class=HTMLResponse)
        async def get_session_dashboard():
            """Get HTML session dashboard."""
            return self.generate_session_html()

        @self.app.get("/api/agents", response_class=JSONResponse)
        async def get_agents():
            """Get all agents status."""
            if not self.session:
                raise HTTPException(
                    status_code=404, detail="No active session")

            agents = {}
            for agent_id, agent in self.session.agents.items():
                agents[agent_id] = {
                    "id": agent.short_id,
                    "name": getattr(agent, 'name', agent_id),
                    "type": agent.__class__.__name__,
                    "status": getattr(agent, 'status', lambda: {})(),
                    "disposition": getattr(agent, 'disposition', 'unknown')
                }
            return agents

        @self.app.get("/api/game", response_class=JSONResponse)
        async def get_current_game():
            """Get current game state."""
            if not self.current_game:
                raise HTTPException(status_code=404, detail="No active game")
            return self.current_game.get_game_state()

    def generate_session_html(self) -> str:
        """Generate the HTML dashboard showing session state."""
        if not self.session:
            return "<html><body><h1>No Active Session</h1></body></html>"

        agents_html = ""
        for agent_id, agent in self.session.agents.items():
            agent_type = agent.__class__.__name__
            disposition = getattr(agent, 'disposition', 'unknown')
            status = getattr(agent, 'status', lambda: {})()
            icon = "🤖" if "Player" in agent_type else "📊" if "Stats" in agent_type else "⚙️"
            agents_html += f"""
            <div class=\"agent-card\" data-agent-id=\"{agent_id}\">
                <div class=\"agent-header\">
                    <span class=\"agent-icon\">{icon}</span>
                    <span class=\"agent-name\">{agent_id}</span>
                    <span class=\"agent-type\">{agent_type}</span>
                </div>
                <div class=\"agent-status\">
                    <div class=\"disposition\">{disposition}</div>
                    <div class=\"status\">{status}</div>
                </div>
            </div>
            """

        compositors_html = ""
        for comp_id, comp in self.session.compositors.items():
            comp_type = comp.__class__.__name__
            active = getattr(comp, 'active', False)
            status_class = "active" if active else "inactive"
            compositors_html += f"""
            <div class=\"compositor-card {status_class}\" data-compositor-id=\"{comp_id}\">
                <span class=\"compositor-name\">{comp_id}</span>
                <span class=\"compositor-type\">{comp_type}</span>
                <span class=\"compositor-status\">{'🟢' if active else '🔴'}</span>
            </div>
            """

        game_html = ""
        if self.current_game:
            game_state = self.current_game.get_game_state()
            game_html = f"""
            <div class=\"game-panel\" id=\"game-panel\">
                <h3>Current Game: <span id=\"game-id\">{game_state.get('game_id', 'Unknown')}</span></h3>
                <div class=\"game-info\">
                    <div>State: <span id=\"game-state\">{game_state.get('state', 'Unknown')}</span></div>
                    <div>Turn: <span id=\"game-turn\">{game_state.get('current_turn', 'None')}</span></div>
                    <div>Frames: <span id=\"game-frames\">{game_state.get('frames_elapsed', 0)}</span></div>
                    <div>Score: <span id=\"game-score\">{game_state.get('board', {}).get('score', 0)}</span></div>
                    <div>Lives: <span id=\"game-lives\">{game_state.get('board', {}).get('lives', 0)}</span></div>
                </div>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Plantangenet Session Dashboard</title>
            <style>
                body {{ font-family: 'Courier New', monospace; background: #1a1a2e; color: #eee; margin: 0; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .session-id {{ color: #16213e; font-size: 1.2em; margin-bottom: 20px; }}
                .panel {{ background: #16213e; border-radius: 8px; padding: 20px; margin-bottom: 20px; border: 1px solid #0e3460; }}
                .panel h2 {{ margin-top: 0; color: #eee; border-bottom: 1px solid #0e3460; padding-bottom: 10px; }}
                .agent-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
                .agent-card {{ background: #0e3460; border-radius: 6px; padding: 15px; border: 1px solid #533483; }}
                .agent-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; overflow: hidden; }}
                .agent-icon {{ font-size: 1.5em; overflow: hidden;}}
                .agent-name {{ font-weight: bold; color: #fff; font-size: 0.5em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
                .agent-type {{ color: #bbb; font-size: 0.9em; }}
                .agent-status {{ font-size: 0.8em; color: #ccc; }}
                .disposition {{ color: #f39c12; margin-bottom: 5px; }}
                .compositor-grid {{ display: flex; gap: 15px; flex-wrap: wrap; }}
                .compositor-card {{ background: #0e3460; border-radius: 6px; padding: 10px; display: flex; gap: 10px; align-items: center; }}
                .compositor-card.active {{ border: 2px solid #27ae60; }}
                .compositor-card.inactive {{ border: 2px solid #e74c3c; }}
                .game-panel {{ background: #533483; border-radius: 6px; padding: 15px; }}
                .game-info {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 10px; }}
                .game-info > div {{ background: #1a1a2e; padding: 8px; border-radius: 4px; text-align: center; }}
                .refresh-status {{ position: fixed; top: 10px; right: 10px; color: #27ae60; }}
            </style>
            <script>
                async function refreshData() {{
                    try {{
                        const response = await fetch('/api/session');
                        if (response.ok) {{
                            const data = await response.json();
                            document.querySelector('.refresh-status').textContent = '🟢 Live';
                            // Update agents
                            const agentGrid = document.getElementById('agent-grid');
                            if (agentGrid) {{
                                agentGrid.innerHTML = Object.values(data.agents).map(function(agent) {{
                                    return `
                                    <div class='agent-card' data-agent-id='${{agent.id}}'>
                                        <div class='agent-header'>
                                            <span class='agent-icon'>🤖</span>
                                            <span class='agent-name'>${{agent.name}}</span>
                                            <span class='agent-type'>${{agent.type}}</span>
                                        </div>
                                        <div class='agent-status'>
                                            <div class='disposition'>${{agent.disposition}}</div>
                                            <div class='status'>${{typeof agent.status === 'object' ? JSON.stringify(agent.status) : agent.status}}</div>
                                        </div>
                                    </div>
                                    `;
                                }}).join('');
                            }}
                            // Update compositors
                            const compositorGrid = document.getElementById('compositor-grid');
                            if (compositorGrid) {{
                                compositorGrid.innerHTML = Object.values(data.compositors).map(function(comp) {{
                                    return `
                                    <div class='compositor-card ${{
                                        comp.active ? 'active' : 'inactive'
                                    }}' data-compositor-id='${{comp.id}}'>
                                        <span class='compositor-name'>${{comp.id}}</span>
                                        <span class='compositor-type'>${{comp.type}}</span>
                                        <span class='compositor-status'>${{comp.active ? '🟢' : '🔴'}}</span>
                                    </div>
                                    `;
                                }}).join('');
                            }}
                            // Update game info
                            if (data.current_game) {{
                                document.getElementById('game-id').textContent = data.current_game.game_id;
                                document.getElementById('game-state').textContent = data.current_game.state;
                                document.getElementById('game-turn').textContent = data.current_game.current_turn;
                                document.getElementById('game-frames').textContent = data.current_game.frames_elapsed;
                                document.getElementById('game-score').textContent = data.current_game.board.score;
                                document.getElementById('game-lives').textContent = data.current_game.board.lives;
                            }}
                        }} else {{
                            document.querySelector('.refresh-status').textContent = '🔴 Error';
                        }}
                    }} catch (error) {{
                        document.querySelector('.refresh-status').textContent = '🔴 Offline';
                    }}
                }}
                setInterval(refreshData, 2000);
                document.addEventListener('DOMContentLoaded', refreshData);
            </script>
        </head>
        <body>
            <div class="refresh-status">🟡 Loading...</div>
            <div class="header">
                <h1>🌿 Plantangenet Session Dashboard</h1>
                <div class="session-id">Session: {self.session.short_id}</div>
            </div>
            <div class="panel">
                <h2>🤖 Agents ({len(self.session.agents)})</h2>
                <div class="agent-grid" id="agent-grid">
                    {agents_html}
                </div>
            </div>
            <div class="panel">
                <h2>🎥 Compositors ({len(self.session.compositors)})</h2>
                <div class="compositor-grid" id="compositor-grid">
                    {compositors_html}
                </div>
            </div>
            {(f'<div class="panel"><h2>🎮 Current Activity</h2>{game_html}</div>' if game_html else '')}
        </body>
        </html>
        """

    def set_session(self, session):
        """Set the current session to monitor."""
        self.session = session

    def set_current_game(self, game):
        """Set the current game being played."""
        self.current_game = game

    async def start_server(self):
        """Start the FastAPI server."""
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
