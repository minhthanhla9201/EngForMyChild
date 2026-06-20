"""
Bộ nạp module game theo `code` của GameType.

Module game đặt trong games/engine/<module>.py. Thêm game mới = thêm file module
+ một bản ghi GameType (field `module` trỏ tới tên file). KHÔNG cần sửa view.
"""

import importlib

# Whitelist tên module hợp lệ → tránh import tuỳ tiện từ dữ liệu DB.
_PACKAGE = 'games.engine'


def load_game_module(module_name):
    """
    Nạp module game theo tên (vd 'listen_pick'). Trả module hoặc raise ValueError
    nếu module không tồn tại / thiếu hàm bắt buộc.
    """
    if not module_name or not module_name.isidentifier():
        raise ValueError(f'Tên module game không hợp lệ: {module_name!r}')
    try:
        mod = importlib.import_module(f'{_PACKAGE}.{module_name}')
    except ImportError as e:
        raise ValueError(f'Không tìm thấy module game {module_name!r}: {e}')
    # Bắt buộc có đủ interface chung.
    for fn in ('build_round', 'score_round'):
        if not hasattr(mod, fn):
            raise ValueError(f'Module game {module_name!r} thiếu hàm {fn}().')
    return mod
