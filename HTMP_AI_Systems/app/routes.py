"""
app/routes.py — REST API endpoints cho Dashboard

Kiến trúc HTMP_AI_Systems:
  - Sử dụng Repository Pattern (db.repository) thay cho truy vấn SQL trực tiếp
"""
from flask import Blueprint, jsonify, send_from_directory, request
import json
import os
from db.repository import CameraRepository, EventRepository, ZoneRepository
from core.config import settings

api_bp = Blueprint('api', __name__)

# Repositories
_cam_repo = CameraRepository()
_event_repo = EventRepository()
_zone_repo = ZoneRepository()


@api_bp.route('/api/history')
def get_history():
    camera_id = request.args.get('camera_id', type=int)
    zone_id = request.args.get('zone_id', type=int)
    history = _event_repo.get_recent(camera_id=camera_id, zone_id=zone_id, limit=150)
    return jsonify(history)


@api_bp.route('/violations/<path:filename>')
def get_violation_image(filename):
    return send_from_directory(settings.VIOLATIONS_DIR, filename)


@api_bp.route('/api/config_roi', methods=['POST'])
def save_roi_config():
    try:
        data = request.json
        camera_id = data.get('camera_id')
        zones = data.get('zones', [])

        if not camera_id:
            return jsonify({"status": "error", "message": "Thiếu camera_id"}), 400
        
        # Cho phép zones rỗng để xóa bỏ giám sát
        # if not zones:
        #     return jsonify({"status": "error", "message": "Cần ít nhất 1 vùng hợp lệ"}), 400

        config = {
            "roi_points": zones[0]["points"] if zones else [], # Tương thích ngược
            "roi_zones": zones
        }
        filename = os.path.join(settings.DATA_DIR, f"roi_config_{camera_id}.json")
        with open(filename, 'w') as f:
            json.dump(config, f)

        # 2. Đồng bộ vào Database
        _zone_repo.update_camera_zones(camera_id, zones)

        # 3. Ép AI Worker nạp lại ngay lập tức (Không đợi 10 phút)
        from app.main import manager
        if manager:
            manager.reload_worker(camera_id)

        return jsonify({"status": "success", "file": filename, "db_sync": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/api/cameras')
def list_cameras():
    return jsonify(_cam_repo.get_all())


@api_bp.route('/api/zones')
def list_zones():
    return jsonify(_zone_repo.get_all_active())


@api_bp.route('/api/analytics')
def get_analytics():
    camera_id = request.args.get('camera_id', type=int)
    zone_id = request.args.get('zone_id', type=int)
    date = request.args.get('date', type=str)
    return jsonify(_event_repo.get_analytics(camera_id, date, zone_id))


@api_bp.route('/api/machine_stats')
def get_machine_stats():
    date = request.args.get('date', type=str)
    return jsonify(_event_repo.get_machine_error_stats(date))


@api_bp.route('/api/health')
def health():
    return jsonify({"status": "ok"})
