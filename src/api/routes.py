from flask import Blueprint, jsonify, send_from_directory
import os

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/history')
def get_history():
    from src.core.database import DatabaseManager
    db = DatabaseManager()
    history = db.get_recent_violations(50)
    return jsonify(history)

@api_bp.route('/violations/<path:filename>')
def get_violation_image(filename):
    return send_from_directory('violations', filename)

@api_bp.route('/api/config_roi', methods=['POST'])
def save_roi_config():
    from flask import request
    import json
    try:
        data = request.json
        points = data.get('points', [])
        if len(points) < 3:
            return jsonify({"status": "error", "message": "Cần ít nhất 3 điểm"}), 400
            
        config = {"roi_points": points}
        with open('roi_config.json', 'w') as f:
            json.dump(config, f)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@api_bp.route('/api/health')
def health():
    return jsonify({"status": "ok"})
