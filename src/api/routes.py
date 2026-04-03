from flask import Blueprint, jsonify, send_from_directory, request
import os
import json
from src.core.database import DatabaseManager

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/history')
def get_history():
    db = DatabaseManager()
    camera_id = request.args.get('camera_id', type=int)
    # Nếu có camera_id thì lọc, không thì lấy tất cả
    history = db.get_recent_violations(camera_id=camera_id, limit=50)
    return jsonify(history)

@api_bp.route('/violations/<path:filename>')
def get_violation_image(filename):
    return send_from_directory('data/violations', filename)

@api_bp.route('/api/config_roi', methods=['POST'])
def save_roi_config():
    try:
        data = request.json
        camera_id = data.get('camera_id')
        points = data.get('points', [])
        
        if not camera_id:
            return jsonify({"status": "error", "message": "Thiếu camera_id"}), 400
        if len(points) < 3:
            return jsonify({"status": "error", "message": "Cần ít nhất 3 điểm"}), 400
            
        config = {"roi_points": points}
        # Lưu cấu hình riêng cho từng camera
        filename = f"data/roi_config_{camera_id}.json"
        with open(filename, 'w') as f:
            json.dump(config, f)
        
        return jsonify({"status": "success", "file": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/api/cameras')
def list_cameras():
    db = DatabaseManager()
    return jsonify(db.get_cameras())

@api_bp.route('/api/analytics')
def get_analytics():
    db = DatabaseManager()
    camera_id = request.args.get('camera_id', type=int)
    return jsonify(db.get_analytics(camera_id))

@api_bp.route('/api/health')
def health():
    return jsonify({"status": "ok"})
