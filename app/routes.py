"""
app/routes.py — REST API endpoints cho Dashboard

Kiến trúc HTMP_AI_Systems:
  - Sử dụng Repository Pattern (db.repository) thay cho truy vấn SQL trực tiếp
"""
from flask import Blueprint, jsonify, send_from_directory, request
import json
from db.repository import CameraRepository, ViolationRepository
from core.config import settings

api_bp = Blueprint('api', __name__)

# Repositories
_cam_repo = CameraRepository()
_vio_repo = ViolationRepository()


@api_bp.route('/api/history')
def get_history():
    camera_id = request.args.get('camera_id', type=int)
    history = _vio_repo.get_recent(camera_id=camera_id, limit=50)
    return jsonify(history)


@api_bp.route('/violations/<path:filename>')
def get_violation_image(filename):
    return send_from_directory(settings.VIOLATIONS_DIR, filename)


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
        filename = f"data/roi_config_{camera_id}.json"
        with open(filename, 'w') as f:
            json.dump(config, f)

        return jsonify({"status": "success", "file": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/api/cameras')
def list_cameras():
    return jsonify(_cam_repo.get_all())


@api_bp.route('/api/analytics')
def get_analytics():
    camera_id = request.args.get('camera_id', type=int)
    return jsonify(_vio_repo.get_analytics(camera_id))


@api_bp.route('/api/health')
def health():
    return jsonify({"status": "ok"})
