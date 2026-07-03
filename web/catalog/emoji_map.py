"""
Bảng ánh xạ TỪ TIẾNG ANH → EMOJI để tự tải hình minh hoạ (Twemoji SVG).

Dùng bởi lệnh `manage.py fetch_images`. Chỉ cần khai ở đây; lệnh lo phần tải + gán.
- Key: text_en (chữ thường) đúng như trong DB.
- Value: 1 ký tự emoji minh hoạ sát nghĩa nhất (ưu tiên hình vui, dễ nhận cho bé).
- Từ trừu tượng (cảm xúc/hành động/thời gian) chọn emoji gần nghĩa nhất; từ nào
  không có emoji phù hợp thì KHÔNG khai (để trống, vẫn hiển thị icon tạm).

Thêm từ mới: chỉ cần thêm một dòng vào đúng nhóm rồi chạy lại `fetch_images`.
"""

EMOJI_MAP = {
    # --- Animals (Động vật) ---
    'cat': '🐱', 'dog': '🐶', 'bird': '🐦', 'cow': '🐮', 'deer': '🦌', 'duck': '🦆',
    'elephant': '🐘', 'fish': '🐟', 'fox': '🦊', 'giraffe': '🦒', 'horse': '🐴',
    'kangaroo': '🦘', 'koala': '🐨', 'lion': '🦁', 'monkey': '🐵', 'panda': '🐼',
    'penguin': '🐧', 'pig': '🐷', 'rabbit': '🐰', 'sheep': '🐑', 'tiger': '🐯',
    'wolf': '🐺', 'zebra': '🦓', 'bear': '🐻',

    # --- Birds (Loài chim) ---
    'chick': '🐤', 'chicken': '🐔', 'dove': '🕊️', 'eagle': '🦅', 'owl': '🦉',
    'parrot': '🦜', 'peacock': '🦚', 'rooster': '🐓', 'swan': '🦢', 'turkey': '🦃',
    'flamingo': '🦩', 'crow': '🐦', 'ostrich': '🦤',
    'sparrow': '🐦', 'pigeon': '🕊️', 'seagull': '🐦', 'woodpecker': '🐦',
    'hummingbird': '🐦',

    # --- Insects (Côn trùng) ---
    'ant': '🐜', 'bee': '🐝', 'beetle': '🪲', 'butterfly': '🦋', 'cricket': '🦗',
    'fly': '🪰', 'ladybug': '🐞', 'mosquito': '🦟', 'snail': '🐌', 'worm': '🪱',
    'spider': '🕷️', 'moth': '🦋', 'caterpillar': '🐛', 'dragonfly': '🦋',
    'firefly': '🐛', 'grasshopper': '🦗', 'termite': '🐜', 'wasp': '🐝',

    # --- Reptiles (Bò sát) ---
    'crocodile': '🐊', 'dinosaur': '🦕', 'dragon': '🐉', 'frog': '🐸', 'lizard': '🦎',
    'snake': '🐍', 'turtle': '🐢', 'tortoise': '🐢', 'alligator': '🐊', 'cobra': '🐍',
    'python': '🐍', 'gecko': '🦎', 'chameleon': '🦎', 'iguana': '🦎',

    # --- Sea animals (Động vật biển) ---
    'crab': '🦀', 'dolphin': '🐬', 'jellyfish': '🎐', 'lobster': '🦞', 'octopus': '🐙',
    'otter': '🦦', 'seal': '🦭', 'shark': '🦈', 'shrimp': '🦐', 'squid': '🦑',
    'whale': '🐳', 'blowfish': '🐡', 'tropical fish': '🐠',

    # --- Fruits (Trái cây) ---
    'apple': '🍎', 'avocado': '🥑', 'banana': '🍌', 'blueberries': '🫐', 'cherry': '🍒',
    'coconut': '🥥', 'grape': '🍇', 'kiwi': '🥝', 'lemon': '🍋', 'mango': '🥭',
    'melon': '🍈', 'orange': '🍊', 'peach': '🍑', 'pear': '🍐', 'pineapple': '🍍',
    'strawberry': '🍓', 'watermelon': '🍉',

    # --- Vegetables (Rau củ) ---
    'broccoli': '🥦', 'carrot': '🥕', 'corn': '🌽', 'cucumber': '🥒', 'eggplant': '🍆',
    'garlic': '🧄', 'mushroom': '🍄', 'onion': '🧅', 'peanut': '🥜', 'pepper': '🌶️',
    'potato': '🥔', 'tomato': '🍅', 'cabbage': '🥬', 'lettuce': '🥬', 'pumpkin': '🎃',
    'celery': '🥬', 'radish': '🥕', 'spinach': '🥬',

    # --- Food (Đồ ăn) ---
    'bread': '🍞', 'cake': '🍰', 'candy': '🍬', 'cheese': '🧀', 'chocolate': '🍫',
    'cookie': '🍪', 'egg': '🥚', 'hamburger': '🍔', 'honey': '🍯', 'noodles': '🍜',
    'pizza': '🍕', 'popcorn': '🍿', 'rice': '🍚', 'sandwich': '🥪',

    # --- Drinks (Đồ uống) ---
    'coffee': '☕', 'juice': '🧃', 'milk': '🥛', 'soda': '🥤', 'tea': '🍵', 'water': '💧',
    'lemonade': '🍋', 'smoothie': '🥤', 'cocoa': '☕', 'yogurt': '🥛', 'ice': '🧊',
    'milkshake': '🥤', 'coconut water': '🥥', 'hot chocolate': '☕',

    # --- Colors (Màu sắc) ---
    'red': '🔴', 'blue': '🔵', 'green': '🟢', 'yellow': '🟡', 'orange_color': '🟠',
    'purple': '🟣', 'brown': '🟤', 'black': '⚫', 'white': '⚪', 'pink': '🌸',
    'gray': '🌫️', 'rainbow': '🌈', 'gold': '🥇', 'silver': '🥈',

    # --- Numbers (Con số) ---
    'zero': '0️⃣', 'one': '1️⃣', 'two': '2️⃣', 'three': '3️⃣', 'four': '4️⃣', 'five': '5️⃣',
    'six': '6️⃣', 'seven': '7️⃣', 'eight': '8️⃣', 'nine': '9️⃣', 'ten': '🔟',
    'hundred': '💯', 'first': '🥇', 'second': '🥈',

    # --- Shapes (Hình khối) ---
    'circle': '⭕', 'square': '🟥', 'triangle': '🔺', 'heart': '❤️', 'diamond': '🔷',
    'star': '⭐', 'arrow': '➡️', 'cross': '❌', 'rectangle': '🟪',

    # --- Body (Cơ thể) ---
    'arm': '💪', 'bone': '🦴', 'brain': '🧠', 'ear': '👂', 'eye': '👁️', 'foot': '🦶',
    'hair': '💇', 'hand': '✋', 'leg': '🦵', 'mouth': '👄', 'nose': '👃', 'thumb': '👍',
    'tongue': '👅', 'tooth': '🦷', 'finger': '👆', 'toe': '🦶', 'knee': '🦵',
    'shoulder': '💪', 'neck': '🧣', 'elbow': '💪', 'cheek': '😊', 'chin': '😀',

    # --- Family (Gia đình) ---
    'baby': '👶', 'boy': '👦', 'girl': '👧', 'brother': '👦', 'sister': '👧',
    'father': '👨', 'mother': '👩', 'grandfather': '👴', 'grandmother': '👵',
    'family': '👨‍👩‍👧‍👦', 'parents': '👫', 'twins': '👯', 'uncle': '👨', 'aunt': '👩',
    'son': '👦', 'daughter': '👧', 'husband': '🤵', 'wife': '👰', 'cousin': '🧒',

    # --- Clothes (Quần áo) ---
    'boots': '👢', 'cap': '🧢', 'coat': '🧥', 'crown': '👑', 'dress': '👗',
    'glasses': '👓', 'gloves': '🧤', 'hat': '👒', 'pants': '👖', 'ring': '💍',
    'scarf': '🧣', 'shirt': '👕', 'shoe': '👟', 'socks': '🧦',

    # --- House (Đồ trong nhà) ---
    'bathtub': '🛁', 'bed': '🛏️', 'broom': '🧹', 'candle': '🕯️', 'chair': '🪑',
    'clock': '🕐', 'door': '🚪', 'house': '🏠', 'key': '🔑', 'lamp': '💡',
    'plate': '🍽️', 'spoon': '🥄', 'toilet': '🚽', 'window': '🪟',

    # --- Bathroom (Phòng tắm) ---
    'soap': '🧼', 'towel': '🧻', 'toothbrush': '🪥', 'mirror': '🪞', 'comb': '💈',
    'shower': '🚿', 'sink': '🚰', 'sponge': '🧽',

    # --- School (Trường học) ---
    'book': '📚', 'crayon': '🖍️', 'globe': '🌍', 'microscope': '🔬', 'notebook': '📓',
    'paint': '🎨', 'pen': '🖊️', 'pencil': '✏️', 'ruler': '📏', 'scissors': '✂️',
    'backpack': '🎒', 'bell': '🔔', 'abacus': '🧮', 'paperclip': '📎',

    # --- Toys (Đồ chơi) ---
    'ball': '⚽', 'balloon': '🎈', 'blocks': '🧱', 'dice': '🎲', 'doll': '🪆',
    'drum': '🥁', 'kite': '🪁', 'puzzle': '🧩', 'robot': '🤖', 'teddy bear': '🧸',
    'marbles': '🔵', 'slide': '🛝', 'swing': '🎠', 'scooter': '🛴',
    'toy car': '🚗', 'train set': '🚂', 'spinning top': '🔝', 'yo-yo': '🪀',

    # --- Music (Nhạc cụ) ---
    'piano': '🎹', 'guitar': '🎸', 'violin': '🎻', 'flute': '🎶', 'trumpet': '🎺',
    'harp': '🎵', 'tambourine': '🪘', 'saxophone': '🎵', 'xylophone': '🎶',

    # --- Sports (Thể thao) ---
    'baseball': '⚾', 'basketball': '🏀', 'bowling': '🎳', 'boxing': '🥊', 'cycling': '🚴',
    'medal': '🏅', 'running': '🏃', 'skiing': '⛷️', 'soccer': '⚽', 'swimming': '🏊',
    'tennis': '🎾', 'trophy': '🏆', 'volleyball': '🏐',

    # --- Vehicles (Phương tiện) ---
    'airplane': '✈️', 'ambulance': '🚑', 'bicycle': '🚲', 'boat': '⛵', 'bus': '🚌',
    'car': '🚗', 'fire engine': '🚒', 'helicopter': '🚁', 'motorcycle': '🏍️',
    'police car': '🚓', 'rocket': '🚀', 'ship': '🚢', 'taxi': '🚕', 'tractor': '🚜',
    'train': '🚆', 'truck': '🚚',

    # --- Nature (Thiên nhiên) ---
    'cactus': '🌵', 'fire': '🔥', 'flower': '🌸', 'grass': '🌱', 'leaf': '🍃',
    'mountain': '⛰️', 'palm tree': '🌴', 'rock': '🪨', 'rose': '🌹', 'seedling': '🌱',
    'tree': '🌳', 'volcano': '🌋',

    # --- Weather (Thời tiết) ---
    'cloud': '☁️', 'fog': '🌫️', 'lightning': '⚡', 'moon': '🌙', 'rain': '🌧️',
    'snow': '❄️', 'snowman': '⛄', 'sun': '☀️', 'tornado': '🌪️', 'umbrella': '☂️',
    'wind': '💨',

    # --- Actions (Hành động) ---
    'run': '🏃', 'walk': '🚶', 'jump': '🤸', 'sit': '🪑', 'stand': '🧍', 'eat': '🍽️',
    'drink': '🥤', 'sleep': '😴', 'read': '📖', 'write': '✍️', 'sing': '🎤',
    'dance': '💃', 'swim': '🏊', 'draw': '🎨', 'laugh': '😄', 'cry': '😢',
    'listen': '👂', 'clap': '👏',

    # --- Feelings (Cảm xúc) ---
    'happy': '😊', 'sad': '😢', 'angry': '😠', 'scared': '😨', 'tired': '😫',
    'hungry': '😋', 'thirsty': '🥵', 'sleepy': '😴', 'excited': '🤩', 'shy': '😳',
    'surprised': '😲', 'proud': '😌', 'bored': '😑', 'love': '❤️',

    # --- Time (Thời gian) ---
    'today': '📅', 'tomorrow': '📆', 'yesterday': '🗓️', 'morning': '🌅',
    'afternoon': '🌤️', 'night': '🌃', 'week': '📅', 'month': '🗓️', 'year': '📆',

    # --- Jobs (Nghề nghiệp) ---
    'teacher': '👩‍🏫', 'doctor': '👨‍⚕️', 'nurse': '👩‍⚕️', 'farmer': '👨‍🌾',
    'police officer': '👮', 'firefighter': '👨‍🚒', 'chef': '👨‍🍳', 'pilot': '👨‍✈️',
    'dentist': '🦷', 'singer': '🎤', 'painter': '🎨', 'driver': '🚗',
    'vet': '🐾', 'astronaut': '🚀', 'doctor': '🩺', 'nurse': '💉', 'pilot': '🛩️',

    # --- Time: thứ trong tuần dùng lịch (không có emoji riêng) ---
    'monday': '📅', 'tuesday': '📅', 'wednesday': '📅', 'thursday': '📅',
    'friday': '📅', 'saturday': '📅', 'sunday': '📅',

    # --- Shapes bổ sung (khối 3D không có emoji riêng → dùng hình gần nhất) ---
    'oval': '⭕', 'cube': '🧊', 'cone': '🍦', 'cylinder': '🥫', 'pentagon': '🔷',
    'line': '➖',

    # --- Colors bổ sung ---
    'violet': '🟣', 'turquoise': '🔵',

    # --- Bathroom bổ sung ---
    'shampoo': '🧴', 'toothpaste': '🪥',
}
