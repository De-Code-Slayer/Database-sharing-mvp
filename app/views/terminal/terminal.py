from flask import Blueprint, render_template, request, redirect, url_for, flash, render_template, session, abort
from flask_login import login_required, current_user
from app import socketio
from ..utilities.database import get_database_instance,start_psql_session


import uuid



terminal_bp = Blueprint('terminal', __name__, url_prefix='/terminal', subdomain="dashboard")



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
    # Use the SocketIO-provided sid
    sid = request.sid  

    db_id = session.get("db_id")
    if not db_id:
        return False  # abort(400) aborting the connection

    # Verify ownership again
    db_instance = get_database_instance(db_id)
    if not db_instance or db_instance.user_id != current_user.id:
        return False

    # Start new psql process
    psql = start_psql_session(db_instance)
    psql_sessions[sid] = psql

    # Start background reader
    def read_output(sid):
        for line in iter(psql.stdout.readline, ""):
            socketio.emit("output", {"data": line}, room=sid)

    socketio.start_background_task(read_output, sid)


@socketio.on("input")
def handle_input(data):
    sid = request.sid
    if sid in psql_sessions:
        psql = psql_sessions[sid]
        psql.stdin.write(data + "\n")
        psql.stdin.flush()


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    if sid in psql_sessions:
        psql_sessions[sid].terminate()
        del psql_sessions[sid]



