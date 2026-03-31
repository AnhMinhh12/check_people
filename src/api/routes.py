import cv2
import time
from flask import Blueprint, render_template, Response, request, jsonify, send_from_directory
import os

def create_api_blueprint(ai_worker, db_manager, violations_dir):
    api_bp = Blueprint('api', __name__)

    def gen_frames():
        while True:
            frame = ai_worker.get_latest_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.04)

    @api_bp.route('/')
    def index():
        return render_template('index.html')

    @api_bp.route('/video_feed')
    def video_feed():
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @api_bp.route('/api/history')
    def get_history():
        history = db_manager.get_history()
        return jsonify(history)

    @api_bp.route('/api/config_roi', methods=['POST'])
    def update_roi():
        data = request.json
        points = data.get("points", [])
        if len(points) >= 3:
            if ai_worker.engine.reload_roi(points):
                return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Polygon cần tối thiểu 3 điểm"}), 400

    @api_bp.route('/violations/<filename>')
    def get_violation_image(filename):
        return send_from_directory(violations_dir, filename)

    return api_bp
