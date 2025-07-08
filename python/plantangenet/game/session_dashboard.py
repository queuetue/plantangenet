"""
Generic FastAPI session and agent dashboard for Plantangenet games.
"""
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Any, Optional
import io
from PIL import Image
import numpy as np


class SessionDashboardServer:
    """Reusable FastAPI server for Plantangenet session/agent status and dashboard."""

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
        self.current_activity = None
        self.templates = Jinja2Templates(
            directory="/home/srussell/Development/groovebox/python/plantangenet/game/templates")
        self.setup_routes()

    def _get_current_game_for_player(self, player_id: str):
        """Get the current game object for a player, or None if not in a game."""
        if not self.current_activity:
            return None
        if hasattr(self.current_activity, 'members') and player_id in self.current_activity.members:
            return self.current_activity
        return None

    def _get_dashboard_objects(self):
        s = self.session
        compositor = None
        if s and hasattr(s, 'compositors') and isinstance(s.compositors, dict):
            compositor = next(iter(s.compositors.values()), None)
        widget_objects = compositor.widgets if (
            compositor and hasattr(compositor, 'widgets')) else {}
        dashboard_registry = getattr(s, '_component_registry', None)
        registry_objects = {}
        if dashboard_registry and hasattr(dashboard_registry, 'all_components'):
            for obj in dashboard_registry.all_components():
                obj_id = getattr(obj, 'id', None) or getattr(obj, 'name', None)
                if obj_id:
                    registry_objects[obj_id] = obj
        objects = []
        seen_ids = set()
        # Add the main game object if available
        game_obj = getattr(s, 'game', None)
        if game_obj is not None:
            game_id = getattr(game_obj, 'game_id', None) or getattr(
                game_obj, 'id', None) or 'game'
            if game_id not in seen_ids:
                obj_dict = {
                    'id': game_id,
                    'type': game_obj.__class__.__name__,
                    'icon': '🎮'
                }
                # Add omni fields if available
                if hasattr(game_obj, 'persisted_fields') or hasattr(game_obj, 'observed_fields'):
                    fields = {}
                    for name, desc in getattr(game_obj, 'persisted_fields', {}).items():
                        fields[name] = getattr(game_obj, name, None)
                    for name, desc in getattr(game_obj, 'observed_fields', {}).items():
                        fields[name] = getattr(game_obj, name, None)
                    obj_dict['fields'] = fields
                objects.append(obj_dict)
                seen_ids.add(game_id)
        for object_id, widget in widget_objects.items():
            if str(object_id).startswith("_"):
                continue
            obj = None
            agents = getattr(s, 'agents', {})
            if isinstance(agents, dict):
                obj = agents.get(object_id)
            else:
                for a in agents:
                    if getattr(a, 'id', None) == object_id:
                        obj = a
                        break
            if obj is None:
                obj = registry_objects.get(object_id)
            if obj is None:
                activities = getattr(s, 'activities', {})
                if isinstance(activities, dict):
                    obj = activities.get(object_id)
                else:
                    for a in activities:
                        if getattr(a, 'id', None) == object_id:
                            obj = a
                            break
            if obj is not None and object_id not in seen_ids:
                obj_type = obj.__class__.__name__
                icon = "🤖" if obj_type and "Player" in obj_type else "📊" if obj_type and "Stats" in obj_type else "⚙️"
                obj_dict = {
                    'id': object_id,
                    'type': obj_type,
                    'icon': icon
                }
                # Add omni fields if available
                if hasattr(obj, 'persisted_fields') or hasattr(obj, 'observed_fields'):
                    fields = {}
                    for name, desc in getattr(obj, 'persisted_fields', {}).items():
                        fields[name] = getattr(obj, name, None)
                    for name, desc in getattr(obj, 'observed_fields', {}).items():
                        fields[name] = getattr(obj, name, None)
                    obj_dict['fields'] = fields
                objects.append(obj_dict)
                seen_ids.add(object_id)
        # --- PATCH: Add all objects from session.dashboard_objects if present ---
        dashboard_objects_dict = getattr(s, 'dashboard_objects', {})
        for obj_id, obj in dashboard_objects_dict.items():
            if obj_id and obj_id not in seen_ids:
                obj_type = obj.__class__.__name__
                icon = "🤖" if obj_type and "Player" in obj_type else "📊" if obj_type and "Stats" in obj_type else "⚙️"
                obj_dict = {
                    'id': obj_id,
                    'type': obj_type,
                    'icon': icon
                }
                if hasattr(obj, 'persisted_fields') or hasattr(obj, 'observed_fields'):
                    fields = {}
                    for name, desc in getattr(obj, 'persisted_fields', {}).items():
                        fields[name] = getattr(obj, name, None)
                    for name, desc in getattr(obj, 'observed_fields', {}).items():
                        fields[name] = getattr(obj, name, None)
                    obj_dict['fields'] = fields
                objects.append(obj_dict)
                seen_ids.add(obj_id)
        # --- END PATCH ---
        # --- PATCH: Add all objects from the component registry if not already present ---
        if dashboard_registry and hasattr(dashboard_registry, 'all_components'):
            for obj in dashboard_registry.all_components():
                obj_id = getattr(obj, 'id', None) or getattr(obj, 'name', None)
                if obj_id and obj_id not in seen_ids:
                    obj_type = obj.__class__.__name__
                    icon = "🤖" if obj_type and "Player" in obj_type else "📊" if obj_type and "Stats" in obj_type else "⚙️"
                    obj_dict = {
                        'id': obj_id,
                        'type': obj_type,
                        'icon': icon
                    }
                    if hasattr(obj, 'persisted_fields') or hasattr(obj, 'observed_fields'):
                        fields = {}
                        for name, desc in getattr(obj, 'persisted_fields', {}).items():
                            fields[name] = getattr(obj, name, None)
                        for name, desc in getattr(obj, 'observed_fields', {}).items():
                            fields[name] = getattr(obj, name, None)
                        obj_dict['fields'] = fields
                    objects.append(obj_dict)
                    seen_ids.add(obj_id)
        # --- END PATCH ---
        return objects

    def setup_routes(self):
        @self.app.get("/api/session", response_class=JSONResponse)
        async def get_session_status():
            if not self.session:
                raise HTTPException(
                    status_code=404, detail="No active session")
            return self._session_status()

        @self.app.get("/session", response_class=HTMLResponse)
        async def get_session_dashboard(request: Request):
            s = self.session
            session_id = getattr(s, 'id', 'unknown') if s else 'unknown'
            compositors = []
            for comp_id, comp in getattr(s, 'compositors', {}).items():
                compositors.append({
                    'id': comp_id,
                    'type': comp.__class__.__name__,
                    'active': getattr(comp, 'active', False)
                })
            activity = None
            if self.current_activity:
                state = self.current_activity.get_game_state() if hasattr(
                    self.current_activity, 'get_game_state') else {}
                activity = {
                    'game_id': state.get('game_id', 'Unknown'),
                    'state': state.get('state', 'Unknown'),
                    'current_turn': state.get('current_turn', 'None'),
                    'frames_elapsed': state.get('frames_elapsed', 0),
                    'board': state.get('board', {})
                }
            return self.templates.TemplateResponse("session_dashboard.html", {
                "request": request,
                "session_id": session_id,
                "dashboard_objects": self._get_dashboard_objects(),
                "compositors": compositors,
                "activity": activity
            })

        @self.app.get("/api/activity", response_class=JSONResponse)
        async def get_current_activity():
            if not self.current_activity:
                raise HTTPException(
                    status_code=404, detail="No active activity")
            return self.current_activity.get_game_state() if hasattr(self.current_activity, 'get_game_state') else {}

        @self.app.get("/stream/{object_id}")
        async def get_asset_stream(object_id: str, request: Request, asset: Optional[str] = None):
            """Serve a live MJPEG stream for a specific object."""
            # Only allow asset serving for valid dashboard objects
            valid_ids = set(obj['id'] for obj in self._get_dashboard_objects())
            if object_id not in valid_ids:
                raise HTTPException(status_code=404, detail="Object not found")

            # Find the object
            agent = None
            if self.session:
                agents = getattr(self.session, 'agents', {})
                if isinstance(agents, dict):
                    agent = agents.get(object_id)
                else:
                    for a in agents:
                        if getattr(a, 'id', None) == object_id:
                            agent = a
                            break
            # Try registry if not found in agents
            if agent is None and self.session:
                dashboard_registry = getattr(
                    self.session, '_component_registry', None)
                if dashboard_registry and hasattr(dashboard_registry, 'all_components'):
                    for obj in dashboard_registry.all_components():
                        obj_id = getattr(obj, 'id', None) or getattr(
                            obj, 'name', None)
                        if obj_id == object_id:
                            agent = obj
                            break
            # Try game object
            if agent is None and self.session:
                game_obj = getattr(self.session, 'game', None)
                if game_obj is not None:
                    game_obj_id = getattr(game_obj, 'game_id', None) or getattr(
                        game_obj, 'id', None)
                    if game_obj_id == object_id:
                        agent = game_obj

            if agent is None or not hasattr(agent, '__render__'):
                raise HTTPException(
                    status_code=404, detail="Object not found or not renderable")

            async def generate_frames():
                import time
                while True:
                    try:
                        # Generate frame
                        asset_type = asset or 'default'
                        # Pass current game context for players
                        render_kwargs = {}
                        if hasattr(agent, 'player_id'):
                            render_kwargs['current_game'] = self._get_current_game_for_player(
                                agent.player_id)
                        img = agent.__render__(
                            asset=asset_type, **render_kwargs)
                        if img is not None:
                            if isinstance(img, np.ndarray):
                                from PIL import Image
                                img = Image.fromarray(
                                    img.astype('uint8'), 'RGB')

                            # Convert to JPEG bytes
                            buf = io.BytesIO()
                            img.save(buf, format="JPEG", quality=80)
                            frame_data = buf.getvalue()

                            # MJPEG frame format
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n'
                                   b'Content-Length: ' + str(len(frame_data)).encode() + b'\r\n\r\n' +
                                   frame_data + b'\r\n')
                        await asyncio.sleep(1/15)  # 15 FPS
                    except Exception as e:
                        print(f"Stream error for {object_id}: {e}")
                        break

            return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

        @self.app.get("/asset/{object_id}")
        async def get_asset(object_id: str, request: Request, asset: Optional[str] = None):
            # Only allow asset serving for valid dashboard objects (agents, registered components, game, etc.)
            valid_ids = set(obj['id'] for obj in self._get_dashboard_objects())
            if object_id not in valid_ids:
                raise HTTPException(status_code=404, detail="Object not found")
            # Only allow asset=None, 'widget', or 'default'. Reject any other param or unknown query params.
            allowed_params = {'asset'}
            extra_params = set(request.query_params.keys()) - allowed_params
            if extra_params:
                raise HTTPException(
                    status_code=400, detail=f"Unknown query parameter(s): {extra_params}")
            if asset not in (None, 'widget', 'default'):
                raise HTTPException(
                    status_code=400, detail=f"Unknown asset: {asset}")
            # If asset == 'widget', try to render the actual object through the widget system
            if asset == 'widget':
                # First try to find the actual object and render it
                agent = None
                if self.session:
                    agents = getattr(self.session, 'agents', {})
                    if isinstance(agents, dict):
                        agent = agents.get(object_id)
                    else:
                        for a in agents:
                            if getattr(a, 'id', None) == object_id:
                                agent = a
                                break
                # Try registry if not found in agents
                if agent is None and self.session:
                    dashboard_registry = getattr(
                        self.session, '_component_registry', None)
                    if dashboard_registry and hasattr(dashboard_registry, 'all_components'):
                        for obj in dashboard_registry.all_components():
                            obj_id = getattr(obj, 'id', None) or getattr(
                                obj, 'name', None)
                            if obj_id == object_id:
                                agent = obj
                                break
                # Try game object
                if agent is None and self.session:
                    game_obj = getattr(self.session, 'game', None)
                    if game_obj is not None:
                        game_obj_id = getattr(game_obj, 'game_id', None) or getattr(
                            game_obj, 'id', None)
                        if game_obj_id == object_id:
                            agent = game_obj

                # If we found the object, try to render it as a widget
                if agent is not None and hasattr(agent, '__render__'):
                    # Pass current game context for players
                    render_kwargs = {}
                    if hasattr(agent, 'player_id'):
                        render_kwargs['current_game'] = self._get_current_game_for_player(
                            agent.player_id)
                    asset_img = agent.__render__(
                        asset='widget', **render_kwargs)
                    if asset_img is not None:
                        if isinstance(asset_img, np.ndarray):
                            img = Image.fromarray(
                                asset_img.astype('uint8'), 'RGB')
                        else:
                            img = asset_img
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        return StreamingResponse(buf, media_type="image/png")

                # Fallback to compositor widget (solid color)
                compositor = None
                if self.session:
                    compositors = getattr(self.session, 'compositors', {})
                    if isinstance(compositors, dict):
                        compositor = next(iter(compositors.values()), None)
                if compositor and hasattr(compositor, 'widgets'):
                    widget = compositor.widgets.get(object_id)
                    if widget is not None:
                        arr = np.zeros(
                            (widget.height, widget.width, 3), dtype=np.uint8)
                        arr[:, :] = widget.color if hasattr(
                            widget, 'color') else (128, 128, 128)
                        img = Image.fromarray(arr.astype('uint8'), 'RGB')
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        return StreamingResponse(buf, media_type="image/png")
                raise HTTPException(
                    status_code=404, detail="Widget asset not found")
            # Try to get the agent's default asset first
            agent = None
            if self.session:
                agents = getattr(self.session, 'agents', {})
                if isinstance(agents, dict):
                    agent = agents.get(object_id)
                else:
                    for a in agents:
                        if getattr(a, 'id', None) == object_id:
                            agent = a
                            break
            # Try to get from registry if not found in agents
            if agent is None and self.session:
                dashboard_registry = getattr(
                    self.session, '_component_registry', None)
                if dashboard_registry and hasattr(dashboard_registry, 'all_components'):
                    for obj in dashboard_registry.all_components():
                        obj_id = getattr(obj, 'id', None) or getattr(
                            obj, 'name', None)
                        if obj_id == object_id:
                            agent = obj
                            break
            # Try to get the game object if not found in agents or registry
            if agent is None and self.session:
                game_obj = getattr(self.session, 'game', None)
                if game_obj is not None:
                    # Check both game_id and id attributes
                    game_obj_id = getattr(game_obj, 'game_id', None) or getattr(
                        game_obj, 'id', None)
                    if game_obj_id == object_id:
                        agent = game_obj
            # If asset == 'default', only try __render__ with asset='default'
            if asset == 'default':
                asset_img = None
                if agent is not None:
                    if hasattr(agent, '__render__'):
                        # Pass current game context for players
                        render_kwargs = {}
                        if hasattr(agent, 'player_id'):
                            render_kwargs['current_game'] = self._get_current_game_for_player(
                                agent.player_id)
                        asset_img = agent.__render__(
                            asset='default', **render_kwargs)
                    else:
                        raise HTTPException(
                            status_code=404, detail="Object does not implement __render__()")
                if asset_img is not None:
                    if isinstance(asset_img, np.ndarray):
                        img = Image.fromarray(asset_img.astype('uint8'), 'RGB')
                    else:
                        img = asset_img
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    return StreamingResponse(buf, media_type="image/png")
                raise HTTPException(
                    status_code=404, detail="Default asset not found")
            # Default: try __render__ with asset='default', then widget asset as fallback
            if agent is not None:
                asset_img = None
                if hasattr(agent, '__render__'):
                    # Pass current game context for players
                    render_kwargs = {}
                    if hasattr(agent, 'player_id'):
                        render_kwargs['current_game'] = self._get_current_game_for_player(
                            agent.player_id)
                    asset_img = agent.__render__(
                        asset='default', **render_kwargs)
                else:
                    asset_img = None
                if asset_img is not None:
                    if isinstance(asset_img, np.ndarray):
                        img = Image.fromarray(asset_img.astype('uint8'), 'RGB')
                    else:
                        img = asset_img
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    return StreamingResponse(buf, media_type="image/png")
            compositor = None
            widget_keys = []
            if self.session:
                compositors = getattr(self.session, 'compositors', {})
                if isinstance(compositors, dict):
                    compositor = next(iter(compositors.values()), None)
            if compositor and hasattr(compositor, 'widgets'):
                widget_keys = list(compositor.widgets.keys())
                # print(
                #     f"[DEBUG] Asset request for {object_id}. Available widget keys: {widget_keys}")
                widget = compositor.widgets.get(object_id)
                if widget is not None:
                    arr = np.zeros(
                        (widget.height, widget.width, 3), dtype=np.uint8)
                    arr[:, :] = widget.color if hasattr(
                        widget, 'color') else (128, 128, 128)
                    img = Image.fromarray(arr.astype('uint8'), 'RGB')
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    return StreamingResponse(buf, media_type="image/png")
            print(
                f"[DEBUG] Asset not found for {object_id}. Available widget keys: {widget_keys if compositor else 'No compositor'}")
            raise HTTPException(status_code=404, detail="Asset not found")

    def set_session(self, session: Any):
        self.session = session

    def set_current_activity(self, activity: Any):
        self.current_activity = activity

    def _session_status(self):
        s = self.session
        status = {
            "session_id": getattr(s, 'id', None),
            "agents": {},
            "activities": {},
            "compositors": {},
            # Return dashboard_objects as a list for frontend compatibility
            "dashboard_objects": self._get_dashboard_objects(),
            "current_activity": None
        }
        # Handle agents as dict or list
        agents = getattr(s, 'agents', {})
        if isinstance(agents, dict):
            agent_iter = agents.items()
        else:
            agent_iter = ((getattr(a, 'id', str(i)), a)
                          for i, a in enumerate(agents))
        for agent_id, agent in agent_iter:
            status["agents"][agent_id] = {
                "id": getattr(agent, 'id', agent_id),
                "name": getattr(agent, 'name', agent_id),
                "type": agent.__class__.__name__,
                "status": getattr(agent, 'status', lambda: {})(),
                "capabilities": getattr(agent, 'capabilities', {}),
                "disposition": getattr(agent, 'disposition', 'unknown')
            }
        # Handle activities as dict or list
        activities = getattr(s, 'activities', {})
        if isinstance(activities, dict):
            act_iter = activities.items()
        else:
            act_iter = ((getattr(a, 'id', str(i)), a)
                        for i, a in enumerate(activities))
        for act_id, act in act_iter:
            status["activities"][act_id] = {
                "id": act_id,
                "type": act.__class__.__name__,
                "members": list(getattr(act, 'members', [])),
                "available": getattr(act, '_available', lambda: False)(),
                "full": getattr(act, '_is_activity_full', lambda: False)()
            }
        for comp_id, comp in getattr(s, 'compositors', {}).items():
            status["compositors"][comp_id] = {
                "id": comp_id,
                "type": comp.__class__.__name__,
                "active": getattr(comp, 'active', False)
            }
        # dashboard_objects is now always a list (see above)
        if self.current_activity:
            status["current_activity"] = self.current_activity.get_game_state(
            ) if hasattr(self.current_activity, 'get_game_state') else {}
        return status

    async def start_server(self):
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
