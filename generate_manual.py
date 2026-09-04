import os
import sys
import io
from fpdf import FPDF
from datetime import datetime

# Fix UnicodeEncodeError on Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class SentinelManualPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(15, 20, 15)
        self.set_auto_page_break(auto=True, margin=20)
        
        # Mau sac chu dao (Brand Palette)
        self.c_primary = (26, 54, 93)      # Dark Navy Blue #1A365D (Tieu de chinh, Header)
        self.c_secondary = (49, 130, 206)  # Cyan Blue #3182CE (Sub-header, Accent)
        self.c_accent = (229, 62, 62)      # Crimson Red #E53E3E (Canh bao, Chu y)
        self.c_text_dark = (45, 55, 72)    # Off-Black #2D3748 (Chu thuong)
        self.c_bg_light = (247, 250, 252)  # Light Grey #F7FAFC (Table header / Box background)
        self.c_border = (226, 232, 240)    # Border Grey #E2E8F0 (Khung/Vien)
        
        # Font name registered
        self.font_name = "Arial"

    def register_fonts(self):
        # Dang ky font Arial he thong ho tro tieng Viet
        font_dir = r"C:\Windows\Fonts"
        self.add_font(self.font_name, "", os.path.join(font_dir, "arial.ttf"))
        self.add_font(self.font_name, "B", os.path.join(font_dir, "arialbd.ttf"))
        self.add_font(self.font_name, "I", os.path.join(font_dir, "ariali.ttf"))
        self.add_font(self.font_name, "BI", os.path.join(font_dir, "arialbi.ttf"))

    def header(self):
        if self.page_no() == 1:
            return  # Khong ve header o trang bia
            
        # Thiet ke Header nang dong
        self.set_font(self.font_name, "B", 8)
        self.set_text_color(*self.c_primary)
        self.cell(0, 5, "SENTINEL WARDEN AI — HƯỚNG DẪN SỬ DỤNG HỆ THỐNG", 0, 0, "L")
        
        self.set_font(self.font_name, "", 8)
        self.set_text_color(115, 126, 143)
        self.cell(0, 5, "Phiên bản V5.6 Enterprise", 0, 1, "R")
        
        # Duong ke phan tach header
        self.set_draw_color(*self.c_border)
        self.set_line_width(0.3)
        self.line(15, 26, 195, 26)
        self.ln(6)

    def footer(self):
        if self.page_no() == 1:
            return  # Khong ve footer o trang bia
            
        # Duong ke phan tach footer
        self.set_draw_color(*self.c_border)
        self.set_line_width(0.3)
        self.line(15, 282, 195, 282)
        
        self.set_y(-12)
        self.set_font(self.font_name, "I", 8)
        self.set_text_color(115, 126, 143)
        self.cell(0, 5, "© 2026 Sentinel Warden AI. Bảo lưu mọi quyền.", 0, 0, "L")
        self.cell(0, 5, f"Trang {self.page_no()}/{{nb}}", 0, 1, "R")

    def cover_page(self):
        self.add_page()
        
        # Vien ngoai sang trong
        self.set_draw_color(*self.c_primary)
        self.set_line_width(1)
        self.rect(8, 8, 194, 281)
        
        self.set_draw_color(*self.c_secondary)
        self.set_line_width(0.3)
        self.rect(9.5, 9.5, 191, 278)
        
        # Khoi mau top
        self.set_fill_color(*self.c_primary)
        self.rect(8, 8, 194, 60, "F")
        
        # Text trong khoi top
        self.set_y(22)
        self.set_font(self.font_name, "B", 26)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "SENTINEL WARDEN AI", 0, 1, "C")
        
        self.set_font(self.font_name, "I", 11)
        self.set_text_color(190, 215, 240)
        self.cell(0, 8, "Hệ Thống Giám Sát An Toàn Lao Động Tích Hợp Trí Tuệ Nhân Tạo", 0, 1, "C")
        
        # Hinh anh trang tri giua trang bia
        self.set_y(100)
        # Ve logo gia lap hoac khoi trang tri hien dai
        self.set_fill_color(240, 244, 248)
        self.rect(40, 85, 130, 80, "F")
        self.set_draw_color(*self.c_secondary)
        self.set_line_width(0.5)
        self.rect(40, 85, 130, 80, "D")
        
        # Chu ben trong khoi trang tri
        self.set_y(105)
        self.set_font(self.font_name, "B", 18)
        self.set_text_color(*self.c_primary)
        self.cell(0, 10, "TÀI LIỆU HƯỚNG DẪN", 0, 1, "C")
        self.set_font(self.font_name, "B", 14)
        self.cell(0, 8, "QUẢN TRỊ VIÊN & NGƯỜI VẬN HÀNH", 0, 1, "C")
        
        self.set_y(130)
        self.set_font(self.font_name, "", 9)
        self.set_text_color(*self.c_text_dark)
        self.cell(0, 5, "- Giám sát an toàn theo thời gian thực (Real-time Live Monitor) -", 0, 1, "C")
        self.cell(0, 5, "- Nhận diện vi phạm vùng nguy hiểm (Safety ROI Polygon) -", 0, 1, "C")
        self.cell(0, 5, "- Tích hợp báo cáo tự động, Email Cảnh báo & ERP Sync -", 0, 1, "C")
        
        # Thong tin ben duoi
        self.set_y(210)
        self.set_font(self.font_name, "B", 12)
        self.set_text_color(*self.c_primary)
        self.cell(0, 6, "PHIÊN BẢN HỆ THỐNG: V5.6 ENTERPRISE", 0, 1, "C")
        
        self.set_draw_color(*self.c_secondary)
        self.line(70, 218, 140, 218)
        
        self.set_y(225)
        self.set_font(self.font_name, "", 10)
        self.set_text_color(*self.c_text_dark)
        
        # Tao bang thong tin nho
        info_x = 55
        self.set_x(info_x)
        self.cell(40, 6, "Đối tượng áp dụng:", 0, 0)
        self.set_font(self.font_name, "B", 10)
        self.cell(60, 6, "Nhà máy & Xưởng sản xuất công nghiệp", 0, 1)
        
        self.set_font(self.font_name, "", 10)
        self.set_x(info_x)
        self.cell(40, 6, "Thời gian biên soạn:", 0, 0)
        self.set_font(self.font_name, "B", 10)
        self.cell(60, 6, datetime.now().strftime("Tháng %m năm %Y"), 0, 1)
        
        self.set_font(self.font_name, "", 10)
        self.set_x(info_x)
        self.cell(40, 6, "Tài liệu lưu hành:", 0, 0)
        self.set_font(self.font_name, "B", 10)
        self.cell(60, 6, "Nội bộ Enterprise", 0, 1)

    def draw_section_title(self, title_text):
        self.ln(6)
        # Lay vi tri y de ve line dung lam left accent
        y = self.get_y()
        self.set_fill_color(*self.c_secondary)
        self.rect(15, y, 2.5, 7, "F")
        
        self.set_x(20)
        self.set_font(self.font_name, "B", 13)
        self.set_text_color(*self.c_primary)
        self.cell(0, 7, title_text, 0, 1, "L")
        self.ln(2)
        
    def draw_subsection_title(self, title_text):
        self.ln(2)
        self.set_font(self.font_name, "B", 10.5)
        self.set_text_color(*self.c_secondary)
        self.cell(0, 6, title_text, 0, 1, "L")
        self.ln(1)

    def draw_paragraph(self, text):
        self.set_font(self.font_name, "", 9.5)
        self.set_text_color(*self.c_text_dark)
        self.multi_cell(0, 5.5, text, 0, "L")
        self.ln(2)

    def draw_bullet(self, title, desc):
        self.set_font(self.font_name, "B", 9.5)
        self.set_text_color(*self.c_primary)
        self.set_x(20)
        self.cell(4, 5.5, "-", 0, 0) # Ky tu gach dau dong
        self.cell(self.get_string_width(title) + 1, 5.5, title + ": ", 0, 0)

        
        self.set_font(self.font_name, "", 9.5)
        self.set_text_color(*self.c_text_dark)
        self.multi_cell(0, 5.5, desc, 0, "L")
        self.ln(1)

    def draw_note_box(self, text):
        self.ln(2)
        self.set_fill_color(*self.c_bg_light)
        self.set_draw_color(*self.c_secondary)
        self.set_line_width(0.3)
        
        # Luu vi tri bat dau
        x = self.get_x()
        y = self.get_y()
        
        # Tinh so dong de ve hop vua van
        self.set_font(self.font_name, "I", 9)
        self.set_text_color(*self.c_primary)
        
        # Ve hop va viet chu lam noi bat ghi chu
        self.rect(15, y, 180, 18, "FD")
        self.set_xy(18, y + 2)
        self.cell(0, 4, "LƯU Ý QUAN TRỌNG:", 0, 1)
        self.set_xy(18, y + 7)
        self.multi_cell(174, 4.5, text, 0, "L")
        self.set_y(y + 20)

    def toc_page(self):
        self.add_page()
        self.draw_section_title("MỤC LỤC CHI TIẾT")
        self.ln(4)
        
        toc_items = [
            ("1. Giới thiệu chung về hệ thống Sentinel Warden AI", 2),
            ("2. Nguyên lý giám sát & Cơ chế cảnh báo vi phạm của AI", 3),
            ("3. Hướng dẫn sử dụng giao diện Dashboard Quản lý", 4),
            ("4. Quy trình thiết lập và vẽ vùng an toàn (ROI)", 5),
            ("5. Hướng dẫn cấu hình hệ thống dành cho Quản trị viên", 6),
            ("6. Các vấn đề thường gặp và cách khắc phục (Troubleshooting)", 7)
        ]
        
        for item, page in toc_items:
            self.set_font(self.font_name, "B", 10)
            self.set_text_color(*self.c_text_dark)
            w_item = self.get_string_width(item)
            self.cell(w_item, 8, item, 0, 0)
            
            # Ve cac dau cham keo dai den so trang
            w_dots = 165 - w_item
            dots_str = "." * int(w_dots / 1.5)
            self.set_font(self.font_name, "", 10)
            self.set_text_color(160, 174, 192)
            self.cell(w_dots, 8, dots_str, 0, 0, "R")
            
            self.set_font(self.font_name, "B", 10)
            self.set_text_color(*self.c_primary)
            self.cell(15, 8, f"Trang {page}", 0, 1, "R")
            self.ln(2)

    def write_section_1(self):
        self.draw_section_title("1. Giới thiệu chung về hệ thống Sentinel Warden AI")
        self.draw_paragraph(
            "Sentinel Warden AI (phiên bản V5.6 Enterprise) là giải pháp công nghệ cao chuyên biệt cho việc giám sát "
            "an toàn lao động và kỷ luật tác phong trong môi trường công nghiệp hiện đại. Sử dụng mô hình trí tuệ nhân tạo "
            "tiên tiến YOLOv8 kết hợp với bộ tối ưu hóa ONNX Runtime, hệ thống có khả năng phân tích trực tiếp luồng camera (RTSP/USB) "
            "với độ chính xác vượt trội và tài nguyên CPU tối thiểu nhờ cơ chế điều phối luồng Zero-Spin độc quyền."
        )
        
        self.draw_subsection_title("Các tính năng cốt lõi:")
        
        self.draw_bullet("Giám sát đa luồng camera", "Hỗ trợ kết nối song song và xử lý đồng thời lên đến 15+ camera IP RTSP chất lượng cao trên hạ tầng phần cứng thông thường.")
        self.draw_bullet("Phát hiện xâm nhập / rời vị trí", "Tự động phát hiện sự hiện diện của nhân sự trong các khu vực làm việc hoặc các vùng nguy hiểm (vùng cấm) được vẽ trực tiếp.")
        self.draw_bullet("Cảnh báo tức thời đa kênh", "Truyền dữ liệu trạng thái qua SocketIO tới dashboard dưới 100ms, đồng thời gửi email đính kèm ảnh bằng chứng và đồng bộ hóa API ERP thời gian thực.")
        self.draw_bullet("Cấu hình ROI trực quan", "Cho phép vẽ/xóa đa giác vùng an toàn trực tiếp trên trình duyệt bằng chuột và hỗ trợ cơ chế nạp lại cấu hình nóng (Hot-reload) không cần khởi động lại máy chủ.")
        self.draw_bullet("Tối ưu hóa Server", "Áp dụng cơ chế giới hạn luồng PyTorch/ONNX chống nghẽn CPU trên các hệ thống Server doanh nghiệp lớn có số nhân CPU cao (lên tới 256 nhân).")

        self.draw_note_box(
            "Hệ thống Sentinel Warden AI hoạt động hoàn toàn tự động 24/7. Toàn bộ ảnh bằng chứng vi phạm "
            "và lịch sử sự kiện được lưu trữ cục bộ (local SQLite) hoặc đồng bộ lên hệ thống cơ sở dữ liệu MySQL tập trung của nhà máy."
        )

    def write_section_2(self):
        self.add_page()
        self.draw_section_title("2. Nguyên lý giám sát & Cơ chế cảnh báo vi phạm của AI")
        self.draw_paragraph(
            "Hệ thống giám sát an toàn dựa trên mô hình Máy trạng thái hữu hạn (FSM) kết hợp với các bộ lọc chống nhiễu "
            "nhằm loại bỏ các trường hợp cảnh báo giả (false positives) gây ra bởi nhiễu camera hoặc chuyển động thoáng qua."
        )
        
        self.draw_subsection_title("2.1 Các trạng thái hoạt động chính của AI:")
        
        self.draw_bullet("AN TOÀN (STATUS_SAFE)", "Phát hiện nhân viên ở bên trong vùng an toàn (ROI) đã cấu hình. Trạng thái này hiển thị màu XANH CYAN sáng trên màn hình điều khiển.")
        self.draw_bullet("RỜI VỊ TRÍ (STATUS_LEFT)", "Nhân viên bước ra khỏi vùng ROI. Trạng thái lập tức chuyển sang CẢNH BÁO màu VÀNG/CAM. Một thanh đếm ngược thời gian bắt đầu chạy. Nếu nhân viên trở lại trước ngưỡng vi phạm, hệ thống sẽ tự động đặt lại bộ đếm mà không ghi nhận lỗi.")
        self.draw_bullet("VI PHẠM (STATUS_VIOLATION)", "Nhân viên vắng mặt liên tục vượt quá thời gian cho phép (mặc định là 5.0 giây hoặc 30.0 giây tùy vị trí cấu hình). Hệ thống sẽ chuyển sang trạng thái VI PHẠM với HUD màu ĐỎ nhấp nháy trên giao diện và kích hoạt chuỗi cảnh báo.")

        self.draw_subsection_title("2.2 Quy trình xử lý và lưu giữ bằng chứng vi phạm:")
        self.draw_paragraph(
            "Khi trạng thái chuyển sang VI PHẠM, hệ thống thực hiện tuần tự các bước sau:\n"
            "1. Chụp ảnh khung hình hiện tại từ camera độ phân giải cao.\n"
            "2. Vẽ Bounding Box (khung viền xanh lá cho người an toàn, viền vàng cho người ngoài vùng nguy hiểm) và vẽ đa giác vùng ROI lên ảnh bằng chứng (màu đỏ tại vị trí vi phạm).\n"
            "3. Chèn văn bản tiếng Việt không dấu chỉ rõ vị trí máy/vùng vi phạm ở góc trái ảnh.\n"
            "4. Lưu ảnh bằng chứng vào thư mục 'data/violations/' với định dạng tên file: violation_YYYYMMDD_HHMMSS.jpg.\n"
            "5. Ghi nhận sự kiện vào database (camera_id, zone_id, loại vi phạm, đường dẫn ảnh, thời gian bắt đầu).\n"
            "6. Kích hoạt thông báo Gmail đính kèm ảnh bằng chứng và gửi webhook đồng bộ lên ERP nhà máy."
        )

        self.draw_note_box(
            "Khi nhân viên quay lại vùng an toàn (ROI) sau khi vi phạm, hệ thống sẽ tự động hoàn tất sự kiện "
            "(Finish Event) trong database, ghi nhận tổng thời gian rời vị trí và chuyển trạng thái camera về lại AN TOÀN."
        )

    def write_section_3(self):
        self.add_page()
        self.draw_section_title("3. Hướng dẫn sử dụng giao diện Dashboard Quản lý")
        self.draw_paragraph(
            "Giao diện Dashboard được thiết kế theo phong cách tối giản, hiện đại, tối ưu cho việc quan sát "
            "và phản ứng nhanh của nhân viên an toàn tại phòng trung tâm điều hành."
        )
        
        self.draw_subsection_title("3.1 Cách truy cập:")
        self.draw_paragraph(
            "Mở trình duyệt Web bất kỳ (khuyến nghị Google Chrome hoặc Microsoft Edge) và truy cập địa chỉ:\n"
            "  - Localhost (chạy trên máy chủ): http://localhost:5000\n"
            "  - Truy cập qua mạng LAN: http://[IP_MAY_CHU]:5000 (Ví dụ: http://192.168.100.15:5000)"
        )
        
        self.draw_subsection_title("3.2 Các Tab chức năng chính:")
        
        self.draw_bullet("Tab Giám Sát (Live Monitor)", "Xem lưới camera trực tiếp (Live Grid). Bạn có thể bấm vào một camera bất kỳ để phóng to (Focus Mode) nhằm theo dõi chi tiết với chất lượng và tốc độ FPS cao hơn. Hệ thống sẽ tự động điều tiết tài nguyên: chỉ camera đang focus mới truyền luồng ảnh động 10 FPS về trình duyệt, các camera ẩn sẽ chạy ngầm ở 1 FPS để tiết kiệm tối đa băng thông mạng LAN.")
        
        self.draw_bullet("Tab Nhật Ký (Violation Logs)", "Lưu trữ lịch sử tất cả các lần vi phạm đã xảy ra. Bảng bao gồm: Tên Camera, Tên Vị Trí, Thời gian bắt đầu, Tổng thời gian vắng mặt, và nút xem ảnh bằng chứng. Quản lý có thể lọc theo Camera hoặc Vị trí để tra cứu nhanh.")
        
        self.draw_bullet("Tab Phân Tích (Analytics)", "Cung cấp biểu đồ trực quan về hiệu suất làm việc. Thống kê tổng giờ làm việc an toàn, tổng số lần rời máy, tỷ lệ vi phạm theo từng ca làm việc, hỗ trợ xuất báo cáo Excel cho phòng nhân sự và quản lý sản xuất.")
        
        self.draw_bullet("Tab Cấu Hình (ROI Config)", "Cho phép lựa chọn camera và vẽ trực tiếp vùng an toàn (ROI) ngay trên khung hình thực tế của camera đó.")

    def write_section_4(self):
        self.add_page()
        self.draw_section_title("4. Quy trình thiết lập và vẽ vùng an toàn (ROI)")
        self.draw_paragraph(
            "Thiết lập vùng an toàn (Region of Interest) chính xác là yếu tố quan trọng nhất để hệ thống "
            "nhận diện đúng tác phong của công nhân và tránh báo động sai do môi trường xung quanh."
        )
        
        self.draw_subsection_title("4.1 Các bước thực hiện vẽ vùng an toàn:")
        self.draw_paragraph(
            "Bước 1: Truy cập vào giao diện quản trị, chọn Tab Cấu Hình ở thanh điều hướng bên trái.\n"
            "Bước 2: Lựa chọn camera cần vẽ hoặc chỉnh sửa từ danh sách camera hiển thị.\n"
            "Bước 3: Sử dụng Chuột Trái click liên tiếp trên hình ảnh camera trực tiếp để chấm các điểm nối nhau tạo thành một hình đa giác (polygon) bao kín vùng an toàn làm việc của công nhân.\n"
            "Bước 4: Nếu chấm lệch điểm, dùng Chuột Phải để xóa điểm vừa chấm gần nhất (hoàn tác - undo).\n"
            "Bước 5: Sau khi hoàn thành vùng bao quanh, nhập Tên vùng (Ví dụ: 'Máy Hàn 01', 'Bàn Lắp Ráp 2') và nhấn nút 'Lưu Cấu Hình'.\n"
            "Bước 6: Hệ thống sẽ báo 'Thành công'. AI Worker quản lý camera đó sẽ tự động nạp cấu hình mới ngay lập tức (Hot-Reload) mà không cần bạn phải khởi động lại máy chủ."
        )

        self.draw_subsection_title("4.2 Một số mẹo vẽ ROI chuẩn xác:")
        
        self.draw_bullet("Vẽ rộng hơn thực tế một chút", "Nên vẽ vùng ROI rộng hơn khu vực đứng của công nhân khoảng 10-15cm. AI sử dụng giải thuật tính toán tỷ lệ giao nhau của bounding box người và đa giác ROI, vì thế chỉ cần một phần cơ thể (bàn chân, tay) lọt vào ROI là hệ thống đã ghi nhận trạng thái An Toàn.")
        self.draw_bullet("Tránh các vùng có chuyển động nền", "Tránh vẽ đè lên lối đi chung của công nhân khác hoặc khu vực cánh tay robot, băng chuyền tự động để không bị nhận diện nhầm người đi qua là đang đứng vận hành.")
        
        self.draw_note_box(
            "Bạn có thể vẽ nhiều vùng ROI độc lập trên cùng một Camera để quản lý nhiều máy hoặc "
            "nhiều vị trí công nhân đứng làm việc cùng lúc trên một khung hình rộng."
        )

    def write_section_5(self):
        self.add_page()
        self.draw_section_title("5. Hướng dẫn cấu hình hệ thống dành cho Quản trị viên")
        self.draw_paragraph(
            "Toàn bộ hành vi hệ thống được quản trị thông qua tệp cấu hình môi trường '.env' nằm tại "
            "thư mục gốc của dự án. Quản trị viên hệ thống có thể điều chỉnh các thông số này để phù hợp với tài nguyên server."
        )
        
        self.draw_subsection_title("5.1 Bảng chú giải các tham số trong tệp .env:")
        
        # Tao bang thong so
        self.set_font(self.font_name, "B", 8.5)
        self.set_fill_color(*self.c_primary)
        self.set_text_color(255, 255, 255)
        self.set_draw_color(*self.c_border)
        
        # Headers
        self.cell(45, 7, "Tên Biến Cấu Hình", 1, 0, "C", True)
        self.cell(25, 7, "Giá Trị Mặc Định", 1, 0, "C", True)
        self.cell(110, 7, "Mô Tả & Tác Dụng Chi Tiết", 1, 1, "C", True)
        
        # Rows
        self.set_font(self.font_name, "", 8)
        self.set_text_color(*self.c_text_dark)
        
        configs = [
            ("RTSP_URL1 -> RTSP_URL100", "rtsp://...", "Đường dẫn luồng camera IP (Hikvision, Dahua, Dahua...)"),
            ("CAMERA_NAME1 -> CAMERA_NAME100", "CAMERA 0001", "Tên hiển thị thân thiện của camera trên giao diện"),
            ("MODEL_PATH", "models/yolov8n.onnx", "Đường dẫn file model AI định dạng ONNX (n:nano, s:small)"),
            ("CONFIDENCE_THRESHOLD", "0.10 - 0.25", "Độ tự tin tối thiểu để AI ghi nhận là người (Tránh nhận diện nhầm)"),
            ("ALARM_DELAY_SECONDS", "30.0", "Thời gian vắng mặt tối đa (giây) trước khi chuyển trạng thái Vi phạm"),
            ("AI_MAX_FPS", "5.0", "Tốc độ xử lý khung hình tối đa của AI trên mỗi camera (tối ưu tải CPU)"),
            ("DATABASE_URL", "mysql+pymysql://...", "Đường dẫn kết nối Database (hỗ trợ SQLite hoặc MySQL)"),
            ("SMTP_SERVER / PORT", "smtp.gmail.com / 587", "Cấu hình cổng gửi email cảnh báo an toàn lao động"),
            ("NOTIFICATION_EMAILS", "hoanhminhz@...", "Danh sách email nhận cảnh báo vi phạm (ngăn cách bởi dấu phẩy)")
        ]
        
        fill = False
        for var, val, desc in configs:
            self.set_fill_color(*self.c_bg_light)
            self.cell(45, 6.5, var, 1, 0, "L", fill)
            self.cell(25, 6.5, val, 1, 0, "C", fill)
            self.cell(110, 6.5, desc, 1, 1, "L", fill)
            fill = not fill
            
        self.ln(3)
        self.draw_subsection_title("5.2 Vận hành bằng Docker Container:")
        self.draw_paragraph(
            "Để triển khai nhanh hệ thống trong môi trường Production mà không cần cài đặt các thư viện Python thủ công:\n"
            "  1. Cài đặt Docker và Docker Compose trên máy chủ.\n"
            "  2. Đặt file model 'yolov8n.onnx' hoặc 'yolov8s.onnx' vào thư mục models/.\n"
            "  3. Cấu hình các biến camera trong file .env.\n"
            "  4. Chạy lệnh: docker compose up -d\n"
            "Hệ thống sẽ tự động tải các image cần thiết, khởi tạo database và khởi chạy dịch vụ tại cổng 5000."
        )

    def write_section_6(self):
        self.add_page()
        self.draw_section_title("6. Các vấn đề thường gặp và cách khắc phục (Troubleshooting)")
        self.draw_paragraph(
            "Trong quá trình vận hành hệ thống Sentinel Warden AI tại nhà máy, có thể xảy ra một số sự cố "
            "về mạng hoặc phần cứng. Dưới đây là hướng dẫn xử lý nhanh dành cho kỹ thuật viên:"
        )
        
        self.draw_subsection_title("6.1 Luồng camera bị giật, lag hoặc hiển thị ngoại tuyến:")
        
        self.draw_bullet("Nguyên nhân 1: Mất kết nối vật lý", "Kiểm tra cáp mạng LAN, cổng nguồn POE của camera IP xem có tín hiệu hay không.")
        self.draw_bullet("Nguyên nhân 2: Băng thông mạng yếu", "Camera IP truyền tải luồng video liên tục yêu cầu đường truyền LAN ổn định. Đảm bảo máy chủ và camera được kết nối bằng cáp Ethernet chuẩn Cat6 thay vì sử dụng Wifi.")
        self.draw_bullet("Nguyên nhân 3: Ép luồng TCP", "Trong tệp '.env' hoặc file khởi chạy hệ thống, đảm bảo OpenCV được ép chạy bằng giao thức TCP (rtsp_transport;tcp) để chống rớt gói tin và vỡ khung hình.")

        self.draw_subsection_title("6.2 Máy chủ bị nghẽn CPU (CPU tải 100%):")
        self.draw_bullet("Nguyên nhân 1: Quá nhiều camera chạy cùng lúc", "Hệ thống AI xử lý lượng ảnh lớn liên tục. Hãy giảm thông số 'AI_MAX_FPS' xuống mức 2.0 hoặc 3.0 trong file .env. Điều này giúp giảm tải CPU đi một nửa mà vẫn đảm bảo độ trễ cảnh báo dưới 1 giây.")
        self.draw_bullet("Nguyên nhân 2: Trùng lặp luồng AI bận", "Đảm bảo rằng hệ thống đã cấu hình giới hạn số luồng (OMP_NUM_THREADS=1, PyTorch thread=1) như đã tối ưu ở bản V5.6 trong file 'app/main.py'. Điều này ngăn chặn việc các camera tranh chấp nhân CPU.")

        self.draw_subsection_title("6.3 Cách kiểm tra nhật ký log bằng script chuẩn đoán:")
        self.draw_paragraph(
            "Hệ thống cung cấp sẵn một công cụ chuẩn đoán lỗi nhanh thông qua dòng lệnh. Bạn có thể mở Terminal "
            "trên máy chủ, di chuyển vào thư mục dự án và chạy lệnh sau:\n"
            "  python check_logs.py\n"
            "Script này sẽ tự động phân tích các tệp nhật ký trong thư mục 'logs/' và chỉ ra chính xác lỗi nằm ở: "
            "Kết nối camera RTSP thất bại, Lỗi kết nối cơ sở dữ liệu MySQL/SQLite, hay lỗi xác thực tài khoản gửi email SMTP."
        )
        
        self.draw_note_box(
            "Nếu gặp lỗi liên quan đến mô hình AI không thể khởi chạy, hãy kiểm tra kỹ đường dẫn tệp ONNX "
            "trong file cấu hình .env và chắc chắn rằng tệp tin model không bị lỗi trong quá trình tải về."
        )

def main():
    print("Đang khởi tạo PDF...")
    pdf = SentinelManualPDF()
    pdf.register_fonts()
    pdf.alias_nb_pages()
    
    # Tao cac trang
    pdf.cover_page()
    pdf.toc_page()
    pdf.write_section_1()
    pdf.write_section_2()
    pdf.write_section_3()
    pdf.write_section_4()
    pdf.write_section_5()
    pdf.write_section_6()
    
    # Ghi ra file PDF
    output_filename = "Huong_Dan_Su_Dung_Sentinel_Warden_AI.pdf"
    print(f"Đang ghi tài liệu ra file: {output_filename}...")
    pdf.output(output_filename)
    print("Hoàn tất!")

if __name__ == "__main__":
    main()
