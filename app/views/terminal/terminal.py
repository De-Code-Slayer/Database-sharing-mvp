from flask import Blueprint, render_template, request, redirect, url_for, flash, render_template, session, abort
from flask_login import login_required, current_user
from app import socketio
from ..utilities.database import get_database_instance,start_psql_session


import uuid



terminal_bp = Blueprint('terminal', __name__, url_prefix='/terminal')



psql_sessions = {}  # { session_id: process }



@terminal_bp.route("/terminal/<int:db_id>")
@login_required
def terminal(db_id):
    # Verify ownership
    db_instance = get_database_instance(db_id)
    if db_instance.user_id != current_user.id:
        abort(403)  # Forbidden

    # Store db_id in session for SocketIO handlers
    session["db_id"] = db_id
    return render_template("terminal.html", db_id=db_id, name=db_instance.database_name)





@socketio.on("connect")
def handle_connect(auth=None):
    sid = str(uuid.uuid4())
    session["id"] = sid

    db_id = session.get("db_id")
    if not db_id:
        abort(400)

    # Verify ownership again for safety
    db_instance = get_database_instance(db_id)
    if not db_instance or db_instance.user_id != current_user.id:
        abort(403)

    # Start new psql process
    psql = start_psql_session(db_instance)
    psql_sessions[sid] = psql

    # Start background reader
    def read_output():
        for line in iter(psql.stdout.readline, ""):
            socketio.emit("output", {"data": line}, room=request.sid)

    socketio.start_background_task(read_output)


@socketio.on("input")
def handle_input(data):
    sid = session.get("id")
    if sid in psql_sessions:
        psql = psql_sessions[sid]
        psql.stdin.write(data + "\n")
        psql.stdin.flush()


@socketio.on("disconnect")
def handle_disconnect():
    sid = session.get("id")
    if sid in psql_sessions:
        psql_sessions[sid].terminate()
        del psql_sessions[sid]




