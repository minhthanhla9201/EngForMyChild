"""
Handler ghi log ra file có TÊN THEO NGÀY: <prefix>-YYYY-MM-DD.log

Khác với TimedRotatingFileHandler mặc định (giữ 1 tên file rồi đổi đuôi khi xoay),
handler này đặt thẳng ngày vào tên file ngay từ đầu → dễ tìm log theo ngày.
File mới tự tạo khi sang ngày mới.
"""

import os
import time
from logging.handlers import TimedRotatingFileHandler


class DailyFileHandler(TimedRotatingFileHandler):
    """Ghi log vào <log_dir>/<prefix>-YYYY-MM-DD.log, xoay vòng lúc nửa đêm."""

    def __init__(self, log_dir, prefix, when='midnight', backup_count=30, encoding='utf-8'):
        self.log_dir = log_dir
        self.prefix = prefix
        os.makedirs(log_dir, exist_ok=True)
        # Khởi tạo với tên file của ngày hôm nay.
        super().__init__(self._current_path(), when=when, backupCount=backup_count, encoding=encoding)

    def _current_path(self):
        """Đường dẫn file log cho ngày hiện tại."""
        return os.path.join(self.log_dir, f'{self.prefix}-{time.strftime("%Y-%m-%d")}.log')

    def doRollover(self):
        """Khi sang ngày mới: trỏ sang file có tên ngày mới thay vì thêm đuôi .YYYY-MM-DD."""
        if self.stream:
            self.stream.close()
            self.stream = None
        self.baseFilename = os.path.abspath(self._current_path())
        if not self.delay:
            self.stream = self._open()
        # Tính lại mốc xoay vòng kế tiếp.
        self.rolloverAt = self.computeRollover(int(time.time()))
