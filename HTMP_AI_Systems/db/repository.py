"""
db/repository.py — Repository Pattern: tách biệt logic SQL khỏi logic nghiệp vụ

Các class:
  - CameraRepository:       CRUD + đồng bộ camera từ .env
  - ZoneRepository:         Quản lý các vùng nhận diện ROI
  - EventRepository:        Ghi nhận sự kiện, truy vấn lịch sử, thống kê
  - SystemHealthRepository: Lưu trữ thông số sức khỏe hệ thống
"""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from db.connection import get_session
from db.models import Camera, Zone, Event, SystemHealth
from core.constants import DB_TABLE_EVENTS, DEFAULT_HISTORY_LIMIT

logger = logging.getLogger("Database.Repository")


class CameraRepository:
    """Repository quản lý bảng cameras"""

    def get_all(self, active_only=True) -> list:
        try:
            with get_session() as session:
                query = session.query(Camera)
                if active_only:
                    query = query.filter(Camera.is_active == True)
                cameras = query.all()
                return [cam.to_dict() for cam in cameras]
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách camera: {e}")
            return []

    def get_by_id(self, camera_id: int):
        try:
            with get_session() as session:
                camera = session.query(Camera).filter(Camera.id == camera_id).first()
                return camera.to_dict() if camera else None
        except Exception as e:
            logger.error(f"Lỗi lấy camera ID {camera_id}: {e}")
            return None

    def sync(self, name: str, url: str) -> bool:
        """Đồng bộ camera từ config - Nhận diện qua Tên để giữ ID không đổi khi đổi luồng video"""
        try:
            with get_session() as session:
                # 1. Tìm xem camera với Tên này đã tồn tại chưa (Ưu tiên Tên để bảo vệ ID và dữ liệu lịch sử)
                existing = session.query(Camera).filter(Camera.name == name).first()
                if existing:
                    # Nếu tồn tại, cập nhật URL mới (Ví dụ đổi từ 102 sang 101)
                    if existing.url != url:
                        existing.url = url
                        logger.info(f"🔄 Camera '{name}' đã được cập nhật URL mới: {url}")
                else:
                    # Nếu chưa có, tạo mới hoàn toàn
                    new_camera = Camera(name=name, url=url)
                    session.add(new_camera)
                    logger.info(f"➕ Thêm mới Camera: {name}")
                return True
        except Exception as e:
            logger.error(f"Lỗi đồng bộ camera: {e}")
            return False

    def delete_orphaned(self, active_configs: list) -> bool:
        """Xóa các camera không còn trong danh sách cấu hình .env (hỗ trợ cả active_urls hoặc active_configs)"""
        if not active_configs:
            return False
        try:
            with get_session() as session:
                all_db_cameras = session.query(Camera).all()
                if not all_db_cameras:
                    return True
                
                # Xác định kiểu của active_configs
                first_item = active_configs[0]
                
                if isinstance(first_item, (list, tuple)):
                    # Danh sách chứa (name, url) hoặc tương đương
                    active_pairs = set((cfg[0], cfg[1]) for cfg in active_configs)
                    orphaned_count = 0
                    for cam in all_db_cameras:
                        if (cam.name, cam.url) not in active_pairs:
                            if cam.is_active:
                                cam.is_active = False
                                orphaned_count += 1
                        else:
                            if not cam.is_active:
                                cam.is_active = True
                    if orphaned_count > 0:
                        logger.info(f"Đã chuyển {orphaned_count} camera cũ (không trùng Tên và URL trong .env) sang trạng thái ngưng hoạt động.")
                
                elif isinstance(first_item, dict):
                    # Danh sách chứa dict {"name": ..., "url": ...}
                    active_pairs = set((cfg.get("name"), cfg.get("url")) for cfg in active_configs)
                    orphaned_count = 0
                    for cam in all_db_cameras:
                        if (cam.name, cam.url) not in active_pairs:
                            if cam.is_active:
                                cam.is_active = False
                                orphaned_count += 1
                        else:
                            if not cam.is_active:
                                cam.is_active = True
                    if orphaned_count > 0:
                        logger.info(f"Đã chuyển {orphaned_count} camera cũ (không trùng Tên và URL trong .env) sang trạng thái ngưng hoạt động.")
                
                else:
                    # Cũ: danh sách chứa active_urls (chuỗi)
                    active_urls = set(active_configs)
                    orphaned_count = 0
                    for cam in all_db_cameras:
                        if cam.url not in active_urls:
                            if cam.is_active:
                                cam.is_active = False
                                orphaned_count += 1
                        else:
                            if not cam.is_active:
                                cam.is_active = True
                    if orphaned_count > 0:
                        logger.info(f"Đã chuyển {orphaned_count} camera cũ (không trùng URL trong .env) sang trạng thái ngưng hoạt động.")
                
                return True
        except Exception as e:
            logger.error(f"Lỗi khi dọn dẹp camera: {e}")
            return False


class ZoneRepository:
    """Repository quản lý bảng zones (ROI)"""

    def get_by_camera(self, camera_id: int) -> list:
        try:
            with get_session() as session:
                zones = session.query(Zone).filter(Zone.camera_id == camera_id, Zone.is_active == True).order_by(Zone.zone_name.asc()).all()
                return [z.to_dict() for z in zones]
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách vùng camera {camera_id}: {e}")
            return []

    def get_all_active(self) -> list:
        """Lấy tất cả các máy (Zone) đang hoạt động trên toàn hệ thống"""
        try:
            with get_session() as session:
                zones = session.query(Zone).filter(Zone.is_active == True).order_by(Zone.zone_name.asc()).all()
                return [z.to_dict() for z in zones]
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách tất cả vùng: {e}")
            return []

    def add(self, camera_id: int, name: str, zone_type: str, roi: list, threshold: int = 0):
        try:
            with get_session() as session:
                new_zone = Zone(
                    camera_id=camera_id,
                    zone_name=name,
                    type=zone_type,
                    roi_polygon=roi,
                    threshold_seconds=threshold
                )
                session.add(new_zone)
                return True
        except Exception as e:
            logger.error(f"Lỗi thêm vùng: {e}")
            return False

    def update_camera_zones(self, camera_id: int, zones_data: list):
        """Đồng bộ vùng ROI từ Web UI vào DB (Upsert logic - Tránh lỗi IntegrityError)"""
        try:
            with get_session() as session:
                # 1. Chuyển tất cả vùng hiện tại của camera này thành inactive
                session.query(Zone).filter(Zone.camera_id == camera_id).update({"is_active": False})
                
                # 2. Xử lý từng vùng mới từ UI
                for z in zones_data:
                    name = z.get('name')
                    # Tìm xem vùng này đã tồn tại trong DB chưa (kể cả đã inactive)
                    existing = session.query(Zone).filter(
                        Zone.camera_id == camera_id, 
                        Zone.zone_name == name
                    ).first()
                    
                    if existing:
                        # Cập nhật tọa độ và kích hoạt lại
                        existing.roi_polygon = z.get('points')
                        existing.is_active = True
                        existing.type = z.get('type', 'person_detection')
                    else:
                        # Tạo mới hoàn toàn
                        new_zone = Zone(
                            camera_id=camera_id,
                            zone_name=name,
                            roi_polygon=z.get('points'),
                            type=z.get('type', 'person_detection'),
                            is_active=True
                        )
                        session.add(new_zone)
                
                session.commit()
                logger.info(f"✅ Đã đồng bộ {len(zones_data)} vùng ROI cho Camera {camera_id}")
        except Exception as e:
            logger.error(f"Lỗi đồng bộ vùng camera {camera_id}: {e}")
            return False


class EventRepository:
    """Repository quản lý bảng events (Phân tích & Thống kê)"""

    def add(self, camera_id: int, zone_id: int = None, event_type: str = "violation", 
            filename: str = None, duration: float = 0.0, machines: str = None) -> int:
        """Ghi nhận sự kiện mới và trả về ID"""
        try:
            with get_session() as session:
                event = Event(
                    camera_id=camera_id,
                    zone_id=zone_id,
                    event_type=event_type,
                    start_time=datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None), 
                    snapshot_path=filename,
                    duration=duration,
                    machines_involved=machines
                )
                session.add(event)
                session.flush() # Để lấy ID trước khi commit
                event_id = event.id
            return event_id
        except Exception as e:
            logger.error(f"Lỗi ghi nhận sự kiện: {e}")
            return None

    def finish_event(self, event_id: int, duration: float) -> bool:
        """Cập nhật thời gian kết thúc và tổng thời gian vi phạm"""
        try:
            with get_session() as session:
                event = session.query(Event).filter(Event.id == event_id).first()
                if event:
                    event.end_time = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
                    event.duration = duration
                    return True
                return False
        except Exception as e:
            logger.error(f"Lỗi kết thúc sự kiện {event_id}: {e}")
            return False

    def check_connection(self) -> bool:
        """Kiểm tra kết nối DB còn sống không"""
        try:
            with get_session() as session:
                session.execute(func.now())
                return True
        except:
            return False

    def get_recent(self, camera_id: int = None, zone_id: int = None, limit: int = 50) -> list:
        try:
            with get_session() as session:
                query = session.query(Event).options(
                    joinedload(Event.camera),
                    joinedload(Event.zone)
                )
                # Chỉ lọc theo Camera nếu KHÔNG chọn Máy cụ thể (để xem lịch sử xuyên suốt các cam khi chọn máy)
                if camera_id and not zone_id:
                    query = query.filter(Event.camera_id == camera_id)
                if zone_id:
                    # Lấy tên máy từ ID được chọn để tìm tất cả lịch sử trùng tên (Merge dữ liệu)
                    target_zone = session.query(Zone).filter(Zone.id == zone_id).first()
                    if target_zone:
                        # Dùng LIKE để bắt được cả trường hợp vi phạm nhiều máy (DUC-0001, DUC-0002)
                        search_pattern = f"%{target_zone.zone_name.upper()}%"
                        query = query.filter(func.upper(Event.machines_involved).like(search_pattern))
                    else:
                        query = query.filter(Event.zone_id == zone_id)
                
                events = query.order_by(Event.start_time.desc()).limit(limit or DEFAULT_HISTORY_LIMIT).all()
                return [e.to_dict() for e in events]
        except Exception as e:
            logger.error(f"Lỗi lấy lịch sử sự kiện: {e}")
            return []

    def get_analytics(self, camera_id: int = None, target_date: str = None, zone_id: int = None) -> dict:
        """Thống kê sự kiện (MySQL compatible)"""
        try:
            with get_session() as session:
                if not target_date:
                    target_date = datetime.now().strftime("%Y-%m-%d")
                
                # 1. Tổng hợp cơ bản trong ngày
                base_query = session.query(
                    func.count(Event.id).label("total"),
                    func.coalesce(func.sum(Event.duration), 0).label("total_duration"),
                    func.coalesce(func.avg(Event.duration), 0).label("avg_duration")
                ).filter(func.date(Event.start_time) == target_date)
                
                # Chỉ lọc theo Camera nếu KHÔNG chọn Máy cụ thể
                if camera_id and not zone_id:
                    base_query = base_query.filter(Event.camera_id == camera_id)
                
                # --- PHÁ VỠ GIỚI HẠN ID: Lọc theo Tên máy để lấy lại dữ liệu cũ ---
                current_zone_name = None
                if zone_id:
                    z = session.query(Zone).filter(Zone.id == zone_id).first()
                    if z:
                        current_zone_name = z.zone_name
                        # Chuẩn hóa tên tìm kiếm: Bỏ dấu để khớp cả cũ và mới
                        def clean_name(s):
                            import re
                            s = s.lower()
                            s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
                            s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
                            s = re.sub(r'[ìíịỉĩ]', 'i', s)
                            s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
                            s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
                            s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
                            s = re.sub(r'đ', 'd', s)
                            return s.upper()

                        search_term = clean_name(z.zone_name)
                        search_pattern = f"%{search_term}%"
                        base_query = base_query.filter(func.upper(Event.machines_involved).like(search_pattern))
                    else:
                        base_query = base_query.filter(Event.zone_id == zone_id)
                
                totals = base_query.one()

                # 2. Tìm giờ cao điểm (MySQL specific: HOUR())
                peak_query = session.query(
                    func.hour(Event.start_time).label("hour"),
                    func.count(Event.id).label("count")
                ).filter(func.date(Event.start_time) == target_date)
                
                if camera_id and not zone_id:
                    peak_query = peak_query.filter(Event.camera_id == camera_id)
                if current_zone_name:
                    search_pattern = f"%{current_zone_name.upper()}%"
                    peak_query = peak_query.filter(func.upper(Event.machines_involved).like(search_pattern))
                elif zone_id:
                    peak_query = peak_query.filter(Event.zone_id == zone_id)
                
                peak_res = peak_query.group_by("hour").order_by(func.count(Event.id).desc()).first()
                peak_hour = f"{peak_res.hour}:00" if peak_res else "N/A"

                # 3. Thống kê biểu đồ 7 ngày gần nhất
                from datetime import timedelta
                seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                
                daily_query = session.query(
                    func.date(Event.start_time).label("date"),
                    func.count(Event.id).label("count")
                ).filter(func.date(Event.start_time) >= seven_days_ago)
                
                if camera_id and not zone_id:
                    daily_query = daily_query.filter(Event.camera_id == camera_id)
                if current_zone_name:
                    search_pattern = f"%{current_zone_name.upper()}%"
                    daily_query = daily_query.filter(func.upper(Event.machines_involved).like(search_pattern))
                elif zone_id:
                    daily_query = daily_query.filter(Event.zone_id == zone_id)
                
                daily_res = daily_query.group_by("date").order_by("date").all()
                daily_stats = [{"date": str(r.date), "count": r.count} for r in daily_res]

                # 4. Tính toán Safety Rate thực tế (Uptime % - Machine-Aware)
                vntime = timezone(timedelta(hours=7))
                now = datetime.now(vntime).replace(tzinfo=None)
                is_today = (target_date == now.strftime("%Y-%m-%d"))
                
                total_monitored_sec = (now.hour * 3600) + (now.minute * 60) + now.second if is_today else 86400
                
                # --- ĐỒNG BỘ: Tính tổng số Zones đang giám sát để làm mẫu số (Denominator) ---
                if zone_id:
                    zone_count = 1
                else:
                    zone_q = session.query(func.count(Zone.id)).filter(Zone.is_active == True)
                    if camera_id:
                        zone_q = zone_q.filter(Zone.camera_id == camera_id)
                    zone_count = zone_q.scalar() or 1
                
                total_capacity_sec = total_monitored_sec * zone_count
                absent_sec = totals.total_duration
                
                safety_rate = max(0, min(100, round(((total_capacity_sec - absent_sec) / total_capacity_sec) * 100, 1)))
                
                # Tên hiển thị của máy nếu đang lọc theo zone
                current_zone_name = None
                if zone_id:
                    z = session.query(Zone).filter(Zone.id == zone_id).first()
                    if z: current_zone_name = z.zone_name

                return {
                    "total_violations": totals.total,
                    "total_duration_minutes": round(totals.total_duration / 60, 1),
                    "avg_duration_seconds": round(totals.avg_duration, 1),
                    "peak_hour": peak_hour,
                    "daily_stats": daily_stats,
                    "safety_rate": safety_rate,
                    "zone_name": current_zone_name
                }
        except Exception as e:
            logger.error(f"Lỗi Analytics MySQL: {e}")
            return {
                "total_violations": 0, 
                "total_duration_minutes": 0, 
                "avg_duration_seconds": 0,
                "peak_hour": "N/A",
                "daily_stats": [],
                "safety_rate": 100
            }

    def _clean_name(self, s: str) -> str:
        """Hàm chuẩn hóa tên: Bỏ dấu và viết hoa để so sánh chính xác"""
        import re
        if not s: return ""
        s = s.lower()
        s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
        s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
        s = re.sub(r'[ìíịỉĩ]', 'i', s)
        s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
        s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
        s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
        s = re.sub(r'đ', 'd', s)
        return s.strip().upper()

    def get_machine_error_stats(self, target_date: str) -> dict:
        """Lấy thống kê lỗi (Đã chuẩn hóa bỏ dấu để khớp lịch sử)"""
        try:
            with get_session() as session:
                if not target_date:
                    target_date = datetime.now().strftime("%Y-%m-%d")

                # 1. Lấy danh sách máy (Zone) đang hoạt động
                active_zones = session.query(Zone).join(
                    Camera, Zone.camera_id == Camera.id
                ).filter(
                    Camera.is_active == True,
                    Zone.is_active == True
                ).all()

                # 2. Lấy tất cả sự kiện trong ngày
                events = session.query(Event.machines_involved).join(
                    Camera, Event.camera_id == Camera.id
                ).filter(
                    Camera.is_active == True,
                    func.date(Event.start_time) == target_date
                ).all()

                # Gom lỗi theo tên đã chuẩn hóa (Bỏ dấu)
                history_counts = {}
                for e in events:
                    if not e.machines_involved: continue
                    # Tách và chuẩn hóa từng tên máy
                    names = [self._clean_name(m) for m in e.machines_involved.split(',')]
                    for n in names:
                        if n:
                            history_counts[n] = history_counts.get(n, 0) + 1

                # 3. CHỈ HIỂN THỊ CÁC MÁY ĐANG HOẠT ĐỘNG
                result = []
                total_errors = 0
                for z in active_zones:
                    # So sánh bằng tên đã chuẩn hóa
                    clean_z_name = self._clean_name(z.zone_name)
                    count = history_counts.get(clean_z_name, 0)
                    total_errors += count
                    result.append({
                        "name": z.zone_name, # Hiển thị tên gốc User gõ
                        "count": count
                    })
                
                result.sort(key=lambda x: x["count"], reverse=True)
                return {"total_today": total_errors, "machines": result}
        except Exception as e:
            logger.error(f"Lỗi lấy thống kê máy: {e}")
            return {"total_today": 0, "machines": []}
        except Exception as e:
            logger.error(f"Lỗi lấy thống kê máy: {e}")
            return {"total_today": 0, "machines": []}


class SystemHealthRepository:
    """Repository quản lý sức khỏe hệ thống"""

    def update(self, node_name: str, gpu_load: int, fps: float):
        try:
            with get_session() as session:
                health = session.query(SystemHealth).filter(SystemHealth.node_name == node_name).first()
                if health:
                    health.gpu_load = gpu_load
                    health.fps_current = fps
                    health.last_heartbeat = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
                else:
                    health = SystemHealth(
                        node_name=node_name, 
                        gpu_load=gpu_load, 
                        fps_current=fps,
                        last_heartbeat=datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
                    )
                    session.add(health)
            return True
        except Exception as e:
            logger.error(f"Lỗi cập nhật sức khỏe: {e}")
            return False
