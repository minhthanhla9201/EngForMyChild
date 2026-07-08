-- ===========================================================================
-- Update icons for catalog_topic and catalog_word
-- Generated: 2026-07-07
-- Mô tả: Cập nhật cột icon trong catalog_topic (theo name_en)
--         và cột icon trong catalog_word (theo text_en).
--         Chạy trên SQLite (dùng với Django project EngForMyChild).
--
-- Lưu ý: catalog_word hiện tại KHÔNG có cột icon. Nếu bạn muốn thêm,
--         hãy chạy migration trước:
--           ALTER TABLE catalog_word ADD COLUMN icon VARCHAR(50) DEFAULT '📖';
--         Sau đó mới chạy phần 2 của script này.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- 1. catalog_topic — cập nhật icon đại diện cho từng chủ đề (28 records)
-- ---------------------------------------------------------------------------
UPDATE catalog_topic SET icon = '🏃' WHERE name_en = 'Actions';
UPDATE catalog_topic SET icon = '🐾' WHERE name_en = 'Animals';
UPDATE catalog_topic SET icon = '🚿' WHERE name_en = 'Bathroom';
UPDATE catalog_topic SET icon = '🐦' WHERE name_en = 'Birds';
UPDATE catalog_topic SET icon = '🫀' WHERE name_en = 'Body';
UPDATE catalog_topic SET icon = '👗' WHERE name_en = 'Clothes';
UPDATE catalog_topic SET icon = '🌈' WHERE name_en = 'Colors';
UPDATE catalog_topic SET icon = '🥤' WHERE name_en = 'Drinks';
UPDATE catalog_topic SET icon = '👨‍👩‍👧‍👦' WHERE name_en = 'Family';
UPDATE catalog_topic SET icon = '😊' WHERE name_en = 'Feelings';
UPDATE catalog_topic SET icon = '🍔' WHERE name_en = 'Food';
UPDATE catalog_topic SET icon = '🍎' WHERE name_en = 'Fruits';
UPDATE catalog_topic SET icon = '🏠' WHERE name_en = 'House';
UPDATE catalog_topic SET icon = '🐛' WHERE name_en = 'Insects';
UPDATE catalog_topic SET icon = '👷' WHERE name_en = 'Jobs';
UPDATE catalog_topic SET icon = '🎸' WHERE name_en = 'Music';
UPDATE catalog_topic SET icon = '🌿' WHERE name_en = 'Nature';
UPDATE catalog_topic SET icon = '🔢' WHERE name_en = 'Numbers';
UPDATE catalog_topic SET icon = '🦎' WHERE name_en = 'Reptiles';
UPDATE catalog_topic SET icon = '🎒' WHERE name_en = 'School';
UPDATE catalog_topic SET icon = '🐚' WHERE name_en = 'Sea animals';
UPDATE catalog_topic SET icon = '🔷' WHERE name_en = 'Shapes';
UPDATE catalog_topic SET icon = '⚽' WHERE name_en = 'Sports';
UPDATE catalog_topic SET icon = '⏰' WHERE name_en = 'Time';
UPDATE catalog_topic SET icon = '🧸' WHERE name_en = 'Toys';
UPDATE catalog_topic SET icon = '🥕' WHERE name_en = 'Vegetables';
UPDATE catalog_topic SET icon = '🚗' WHERE name_en = 'Vehicles';
UPDATE catalog_topic SET icon = '⛅' WHERE name_en = 'Weather';


-- ---------------------------------------------------------------------------
-- 2. catalog_word — cập nhật icon theo text_en (437 words)
--    ⚠️  Cần thêm cột icon vào bảng trước nếu chưa có:
--        ALTER TABLE catalog_word ADD COLUMN icon VARCHAR(50) DEFAULT '📖';
-- ---------------------------------------------------------------------------

-- ── Actions ──────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '👏' WHERE LOWER(text_en) = 'clap';
UPDATE catalog_word SET icon = '😢' WHERE LOWER(text_en) = 'cry';
UPDATE catalog_word SET icon = '💃' WHERE LOWER(text_en) = 'dance';
UPDATE catalog_word SET icon = '🎨' WHERE LOWER(text_en) = 'draw';
UPDATE catalog_word SET icon = '🥤' WHERE LOWER(text_en) = 'drink';
UPDATE catalog_word SET icon = '🍽️' WHERE LOWER(text_en) = 'eat';
UPDATE catalog_word SET icon = '🤸' WHERE LOWER(text_en) = 'jump';
UPDATE catalog_word SET icon = '😄' WHERE LOWER(text_en) = 'laugh';
UPDATE catalog_word SET icon = '👂' WHERE LOWER(text_en) = 'listen';
UPDATE catalog_word SET icon = '📖' WHERE LOWER(text_en) = 'read';
UPDATE catalog_word SET icon = '🏃' WHERE LOWER(text_en) = 'run';
UPDATE catalog_word SET icon = '🎤' WHERE LOWER(text_en) = 'sing';
UPDATE catalog_word SET icon = '🪑' WHERE LOWER(text_en) = 'sit';
UPDATE catalog_word SET icon = '😴' WHERE LOWER(text_en) = 'sleep';
UPDATE catalog_word SET icon = '🧍' WHERE LOWER(text_en) = 'stand';
UPDATE catalog_word SET icon = '🏊' WHERE LOWER(text_en) = 'swim';
UPDATE catalog_word SET icon = '🚶' WHERE LOWER(text_en) = 'walk';
UPDATE catalog_word SET icon = '✍️' WHERE LOWER(text_en) = 'write';

-- ── Animals ───────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🐻' WHERE LOWER(text_en) = 'bear';
UPDATE catalog_word SET icon = '🐦' WHERE LOWER(text_en) = 'bird';
UPDATE catalog_word SET icon = '🐱' WHERE LOWER(text_en) = 'cat';
UPDATE catalog_word SET icon = '🐮' WHERE LOWER(text_en) = 'cow';
UPDATE catalog_word SET icon = '🦌' WHERE LOWER(text_en) = 'deer';
UPDATE catalog_word SET icon = '🐶' WHERE LOWER(text_en) = 'dog';
UPDATE catalog_word SET icon = '🦆' WHERE LOWER(text_en) = 'duck';
UPDATE catalog_word SET icon = '🐘' WHERE LOWER(text_en) = 'elephant';
UPDATE catalog_word SET icon = '🐟' WHERE LOWER(text_en) = 'fish';
UPDATE catalog_word SET icon = '🦊' WHERE LOWER(text_en) = 'fox';
UPDATE catalog_word SET icon = '🦒' WHERE LOWER(text_en) = 'giraffe';
UPDATE catalog_word SET icon = '🐴' WHERE LOWER(text_en) = 'horse';
UPDATE catalog_word SET icon = '🦘' WHERE LOWER(text_en) = 'kangaroo';
UPDATE catalog_word SET icon = '🐨' WHERE LOWER(text_en) = 'koala';
UPDATE catalog_word SET icon = '🦁' WHERE LOWER(text_en) = 'lion';
UPDATE catalog_word SET icon = '🐵' WHERE LOWER(text_en) = 'monkey';
UPDATE catalog_word SET icon = '🐼' WHERE LOWER(text_en) = 'panda';
UPDATE catalog_word SET icon = '🐧' WHERE LOWER(text_en) = 'penguin';
UPDATE catalog_word SET icon = '🐷' WHERE LOWER(text_en) = 'pig';
UPDATE catalog_word SET icon = '🐰' WHERE LOWER(text_en) = 'rabbit';
UPDATE catalog_word SET icon = '🐑' WHERE LOWER(text_en) = 'sheep';
UPDATE catalog_word SET icon = '🐯' WHERE LOWER(text_en) = 'tiger';
UPDATE catalog_word SET icon = '🐺' WHERE LOWER(text_en) = 'wolf';
UPDATE catalog_word SET icon = '🦓' WHERE LOWER(text_en) = 'zebra';

-- ── Bathroom ──────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '💈' WHERE LOWER(text_en) = 'comb';
UPDATE catalog_word SET icon = '🪞' WHERE LOWER(text_en) = 'mirror';
UPDATE catalog_word SET icon = '🧴' WHERE LOWER(text_en) = 'shampoo';
UPDATE catalog_word SET icon = '🚿' WHERE LOWER(text_en) = 'shower';
UPDATE catalog_word SET icon = '🚰' WHERE LOWER(text_en) = 'sink';
UPDATE catalog_word SET icon = '🧼' WHERE LOWER(text_en) = 'soap';
UPDATE catalog_word SET icon = '🧽' WHERE LOWER(text_en) = 'sponge';
UPDATE catalog_word SET icon = '🪥' WHERE LOWER(text_en) = 'toothbrush';
UPDATE catalog_word SET icon = '🪥' WHERE LOWER(text_en) = 'toothpaste';
UPDATE catalog_word SET icon = '🧻' WHERE LOWER(text_en) = 'towel';

-- ── Birds ─────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🐤' WHERE LOWER(text_en) = 'chick';
UPDATE catalog_word SET icon = '🐔' WHERE LOWER(text_en) = 'chicken';
UPDATE catalog_word SET icon = '🐦' WHERE LOWER(text_en) = 'crow';
UPDATE catalog_word SET icon = '🕊️' WHERE LOWER(text_en) = 'dove';
UPDATE catalog_word SET icon = '🦅' WHERE LOWER(text_en) = 'eagle';
UPDATE catalog_word SET icon = '🦩' WHERE LOWER(text_en) = 'flamingo';
UPDATE catalog_word SET icon = '🐦' WHERE LOWER(text_en) = 'hummingbird';
UPDATE catalog_word SET icon = '🦤' WHERE LOWER(text_en) = 'ostrich';
UPDATE catalog_word SET icon = '🦉' WHERE LOWER(text_en) = 'owl';
UPDATE catalog_word SET icon = '🦜' WHERE LOWER(text_en) = 'parrot';
UPDATE catalog_word SET icon = '🦚' WHERE LOWER(text_en) = 'peacock';
UPDATE catalog_word SET icon = '🕊️' WHERE LOWER(text_en) = 'pigeon';
UPDATE catalog_word SET icon = '🐓' WHERE LOWER(text_en) = 'rooster';
UPDATE catalog_word SET icon = '🐦' WHERE LOWER(text_en) = 'seagull';
UPDATE catalog_word SET icon = '🐦' WHERE LOWER(text_en) = 'sparrow';
UPDATE catalog_word SET icon = '🦢' WHERE LOWER(text_en) = 'swan';
UPDATE catalog_word SET icon = '🦃' WHERE LOWER(text_en) = 'turkey';
UPDATE catalog_word SET icon = '🐦' WHERE LOWER(text_en) = 'woodpecker';

-- ── Body ──────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '💪' WHERE LOWER(text_en) = 'arm';
UPDATE catalog_word SET icon = '🦴' WHERE LOWER(text_en) = 'bone';
UPDATE catalog_word SET icon = '🧠' WHERE LOWER(text_en) = 'brain';
UPDATE catalog_word SET icon = '😊' WHERE LOWER(text_en) = 'cheek';
UPDATE catalog_word SET icon = '😀' WHERE LOWER(text_en) = 'chin';
UPDATE catalog_word SET icon = '👂' WHERE LOWER(text_en) = 'ear';
UPDATE catalog_word SET icon = '💪' WHERE LOWER(text_en) = 'elbow';
UPDATE catalog_word SET icon = '👁️' WHERE LOWER(text_en) = 'eye';
UPDATE catalog_word SET icon = '👆' WHERE LOWER(text_en) = 'finger';
UPDATE catalog_word SET icon = '🦶' WHERE LOWER(text_en) = 'foot';
UPDATE catalog_word SET icon = '💇' WHERE LOWER(text_en) = 'hair';
UPDATE catalog_word SET icon = '✋' WHERE LOWER(text_en) = 'hand';
UPDATE catalog_word SET icon = '🦵' WHERE LOWER(text_en) = 'knee';
UPDATE catalog_word SET icon = '🦵' WHERE LOWER(text_en) = 'leg';
UPDATE catalog_word SET icon = '👄' WHERE LOWER(text_en) = 'mouth';
UPDATE catalog_word SET icon = '🧣' WHERE LOWER(text_en) = 'neck';
UPDATE catalog_word SET icon = '👃' WHERE LOWER(text_en) = 'nose';
UPDATE catalog_word SET icon = '💪' WHERE LOWER(text_en) = 'shoulder';
UPDATE catalog_word SET icon = '👍' WHERE LOWER(text_en) = 'thumb';
UPDATE catalog_word SET icon = '🦶' WHERE LOWER(text_en) = 'toe';
UPDATE catalog_word SET icon = '👅' WHERE LOWER(text_en) = 'tongue';
UPDATE catalog_word SET icon = '🦷' WHERE LOWER(text_en) = 'tooth';

-- ── Clothes ───────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '👢' WHERE LOWER(text_en) = 'boots';
UPDATE catalog_word SET icon = '🧢' WHERE LOWER(text_en) = 'cap';
UPDATE catalog_word SET icon = '🧥' WHERE LOWER(text_en) = 'coat';
UPDATE catalog_word SET icon = '👑' WHERE LOWER(text_en) = 'crown';
UPDATE catalog_word SET icon = '👗' WHERE LOWER(text_en) = 'dress';
UPDATE catalog_word SET icon = '👓' WHERE LOWER(text_en) = 'glasses';
UPDATE catalog_word SET icon = '🧤' WHERE LOWER(text_en) = 'gloves';
UPDATE catalog_word SET icon = '👒' WHERE LOWER(text_en) = 'hat';
UPDATE catalog_word SET icon = '👖' WHERE LOWER(text_en) = 'pants';
UPDATE catalog_word SET icon = '💍' WHERE LOWER(text_en) = 'ring';
UPDATE catalog_word SET icon = '🧣' WHERE LOWER(text_en) = 'scarf';
UPDATE catalog_word SET icon = '👕' WHERE LOWER(text_en) = 'shirt';
UPDATE catalog_word SET icon = '👟' WHERE LOWER(text_en) = 'shoe';
UPDATE catalog_word SET icon = '🧦' WHERE LOWER(text_en) = 'socks';

-- ── Colors ────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '⚫' WHERE LOWER(text_en) = 'black';
UPDATE catalog_word SET icon = '🔵' WHERE LOWER(text_en) = 'blue';
UPDATE catalog_word SET icon = '🟤' WHERE LOWER(text_en) = 'brown';
UPDATE catalog_word SET icon = '🥇' WHERE LOWER(text_en) = 'gold';
UPDATE catalog_word SET icon = '🌫️' WHERE LOWER(text_en) = 'gray';
UPDATE catalog_word SET icon = '🟢' WHERE LOWER(text_en) = 'green';
UPDATE catalog_word SET icon = '🟠' WHERE LOWER(text_en) = 'orange';
UPDATE catalog_word SET icon = '🌸' WHERE LOWER(text_en) = 'pink';
UPDATE catalog_word SET icon = '🟣' WHERE LOWER(text_en) = 'purple';
UPDATE catalog_word SET icon = '🌈' WHERE LOWER(text_en) = 'rainbow';
UPDATE catalog_word SET icon = '🔴' WHERE LOWER(text_en) = 'red';
UPDATE catalog_word SET icon = '🥈' WHERE LOWER(text_en) = 'silver';
UPDATE catalog_word SET icon = '🔵' WHERE LOWER(text_en) = 'turquoise';
UPDATE catalog_word SET icon = '🟣' WHERE LOWER(text_en) = 'violet';
UPDATE catalog_word SET icon = '⚪' WHERE LOWER(text_en) = 'white';
UPDATE catalog_word SET icon = '🟡' WHERE LOWER(text_en) = 'yellow';

-- ── Drinks ────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '☕' WHERE LOWER(text_en) = 'cocoa';
UPDATE catalog_word SET icon = '🥥' WHERE LOWER(text_en) = 'coconut water';
UPDATE catalog_word SET icon = '☕' WHERE LOWER(text_en) = 'coffee';
UPDATE catalog_word SET icon = '☕' WHERE LOWER(text_en) = 'hot chocolate';
UPDATE catalog_word SET icon = '🧊' WHERE LOWER(text_en) = 'ice';
UPDATE catalog_word SET icon = '🧃' WHERE LOWER(text_en) = 'juice';
UPDATE catalog_word SET icon = '🍋' WHERE LOWER(text_en) = 'lemonade';
UPDATE catalog_word SET icon = '🥛' WHERE LOWER(text_en) = 'milk';
UPDATE catalog_word SET icon = '🥤' WHERE LOWER(text_en) = 'milkshake';
UPDATE catalog_word SET icon = '🥤' WHERE LOWER(text_en) = 'smoothie';
UPDATE catalog_word SET icon = '🥤' WHERE LOWER(text_en) = 'soda';
UPDATE catalog_word SET icon = '🍵' WHERE LOWER(text_en) = 'tea';
UPDATE catalog_word SET icon = '💧' WHERE LOWER(text_en) = 'water';
UPDATE catalog_word SET icon = '🥛' WHERE LOWER(text_en) = 'yogurt';

-- ── Family ────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '👩' WHERE LOWER(text_en) = 'aunt';
UPDATE catalog_word SET icon = '👶' WHERE LOWER(text_en) = 'baby';
UPDATE catalog_word SET icon = '👦' WHERE LOWER(text_en) = 'boy';
UPDATE catalog_word SET icon = '👦' WHERE LOWER(text_en) = 'brother';
UPDATE catalog_word SET icon = '🧒' WHERE LOWER(text_en) = 'cousin';
UPDATE catalog_word SET icon = '👧' WHERE LOWER(text_en) = 'daughter';
UPDATE catalog_word SET icon = '👨‍👩‍👧‍👦' WHERE LOWER(text_en) = 'family';
UPDATE catalog_word SET icon = '👨' WHERE LOWER(text_en) = 'father';
UPDATE catalog_word SET icon = '👧' WHERE LOWER(text_en) = 'girl';
UPDATE catalog_word SET icon = '👴' WHERE LOWER(text_en) = 'grandfather';
UPDATE catalog_word SET icon = '👵' WHERE LOWER(text_en) = 'grandmother';
UPDATE catalog_word SET icon = '🤵' WHERE LOWER(text_en) = 'husband';
UPDATE catalog_word SET icon = '👩' WHERE LOWER(text_en) = 'mother';
UPDATE catalog_word SET icon = '👫' WHERE LOWER(text_en) = 'parents';
UPDATE catalog_word SET icon = '👧' WHERE LOWER(text_en) = 'sister';
UPDATE catalog_word SET icon = '👦' WHERE LOWER(text_en) = 'son';
UPDATE catalog_word SET icon = '👯' WHERE LOWER(text_en) = 'twins';
UPDATE catalog_word SET icon = '👨' WHERE LOWER(text_en) = 'uncle';
UPDATE catalog_word SET icon = '👰' WHERE LOWER(text_en) = 'wife';

-- ── Feelings ──────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '😠' WHERE LOWER(text_en) = 'angry';
UPDATE catalog_word SET icon = '😑' WHERE LOWER(text_en) = 'bored';
UPDATE catalog_word SET icon = '🤩' WHERE LOWER(text_en) = 'excited';
UPDATE catalog_word SET icon = '😊' WHERE LOWER(text_en) = 'happy';
UPDATE catalog_word SET icon = '😋' WHERE LOWER(text_en) = 'hungry';
UPDATE catalog_word SET icon = '❤️' WHERE LOWER(text_en) = 'love';
UPDATE catalog_word SET icon = '😌' WHERE LOWER(text_en) = 'proud';
UPDATE catalog_word SET icon = '😢' WHERE LOWER(text_en) = 'sad';
UPDATE catalog_word SET icon = '😨' WHERE LOWER(text_en) = 'scared';
UPDATE catalog_word SET icon = '😳' WHERE LOWER(text_en) = 'shy';
UPDATE catalog_word SET icon = '😴' WHERE LOWER(text_en) = 'sleepy';
UPDATE catalog_word SET icon = '😲' WHERE LOWER(text_en) = 'surprised';
UPDATE catalog_word SET icon = '🥵' WHERE LOWER(text_en) = 'thirsty';
UPDATE catalog_word SET icon = '😫' WHERE LOWER(text_en) = 'tired';

-- ── Food ──────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🍞' WHERE LOWER(text_en) = 'bread';
UPDATE catalog_word SET icon = '🍰' WHERE LOWER(text_en) = 'cake';
UPDATE catalog_word SET icon = '🍬' WHERE LOWER(text_en) = 'candy';
UPDATE catalog_word SET icon = '🧀' WHERE LOWER(text_en) = 'cheese';
UPDATE catalog_word SET icon = '🍫' WHERE LOWER(text_en) = 'chocolate';
UPDATE catalog_word SET icon = '🍪' WHERE LOWER(text_en) = 'cookie';
UPDATE catalog_word SET icon = '🥚' WHERE LOWER(text_en) = 'egg';
UPDATE catalog_word SET icon = '🍔' WHERE LOWER(text_en) = 'hamburger';
UPDATE catalog_word SET icon = '🍯' WHERE LOWER(text_en) = 'honey';
UPDATE catalog_word SET icon = '🍜' WHERE LOWER(text_en) = 'noodles';
UPDATE catalog_word SET icon = '🍕' WHERE LOWER(text_en) = 'pizza';
UPDATE catalog_word SET icon = '🍿' WHERE LOWER(text_en) = 'popcorn';
UPDATE catalog_word SET icon = '🍚' WHERE LOWER(text_en) = 'rice';
UPDATE catalog_word SET icon = '🥪' WHERE LOWER(text_en) = 'sandwich';

-- ── Fruits ────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🍎' WHERE LOWER(text_en) = 'apple';
UPDATE catalog_word SET icon = '🥑' WHERE LOWER(text_en) = 'avocado';
UPDATE catalog_word SET icon = '🍌' WHERE LOWER(text_en) = 'banana';
UPDATE catalog_word SET icon = '🫐' WHERE LOWER(text_en) = 'blueberries';
UPDATE catalog_word SET icon = '🍒' WHERE LOWER(text_en) = 'cherry';
UPDATE catalog_word SET icon = '🥥' WHERE LOWER(text_en) = 'coconut';
UPDATE catalog_word SET icon = '🍇' WHERE LOWER(text_en) = 'grape';
UPDATE catalog_word SET icon = '🥝' WHERE LOWER(text_en) = 'kiwi';
UPDATE catalog_word SET icon = '🍋' WHERE LOWER(text_en) = 'lemon';
UPDATE catalog_word SET icon = '🥭' WHERE LOWER(text_en) = 'mango';
UPDATE catalog_word SET icon = '🍈' WHERE LOWER(text_en) = 'melon';
UPDATE catalog_word SET icon = '🍊' WHERE LOWER(text_en) = 'orange';
UPDATE catalog_word SET icon = '🍑' WHERE LOWER(text_en) = 'peach';
UPDATE catalog_word SET icon = '🍐' WHERE LOWER(text_en) = 'pear';
UPDATE catalog_word SET icon = '🍍' WHERE LOWER(text_en) = 'pineapple';
UPDATE catalog_word SET icon = '🍓' WHERE LOWER(text_en) = 'strawberry';
UPDATE catalog_word SET icon = '🍉' WHERE LOWER(text_en) = 'watermelon';

-- ── House ─────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🛁' WHERE LOWER(text_en) = 'bathtub';
UPDATE catalog_word SET icon = '🛏️' WHERE LOWER(text_en) = 'bed';
UPDATE catalog_word SET icon = '🧹' WHERE LOWER(text_en) = 'broom';
UPDATE catalog_word SET icon = '🕯️' WHERE LOWER(text_en) = 'candle';
UPDATE catalog_word SET icon = '🪑' WHERE LOWER(text_en) = 'chair';
UPDATE catalog_word SET icon = '🕐' WHERE LOWER(text_en) = 'clock';
UPDATE catalog_word SET icon = '🚪' WHERE LOWER(text_en) = 'door';
UPDATE catalog_word SET icon = '🏠' WHERE LOWER(text_en) = 'house';
UPDATE catalog_word SET icon = '🔑' WHERE LOWER(text_en) = 'key';
UPDATE catalog_word SET icon = '💡' WHERE LOWER(text_en) = 'lamp';
UPDATE catalog_word SET icon = '🍽️' WHERE LOWER(text_en) = 'plate';
UPDATE catalog_word SET icon = '🥄' WHERE LOWER(text_en) = 'spoon';
UPDATE catalog_word SET icon = '🚽' WHERE LOWER(text_en) = 'toilet';
UPDATE catalog_word SET icon = '🪟' WHERE LOWER(text_en) = 'window';

-- ── Insects ───────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🐜' WHERE LOWER(text_en) = 'ant';
UPDATE catalog_word SET icon = '🐝' WHERE LOWER(text_en) = 'bee';
UPDATE catalog_word SET icon = '🪲' WHERE LOWER(text_en) = 'beetle';
UPDATE catalog_word SET icon = '🦋' WHERE LOWER(text_en) = 'butterfly';
UPDATE catalog_word SET icon = '🐛' WHERE LOWER(text_en) = 'caterpillar';
UPDATE catalog_word SET icon = '🦗' WHERE LOWER(text_en) = 'cricket';
UPDATE catalog_word SET icon = '🦋' WHERE LOWER(text_en) = 'dragonfly';
UPDATE catalog_word SET icon = '🐛' WHERE LOWER(text_en) = 'firefly';
UPDATE catalog_word SET icon = '🪰' WHERE LOWER(text_en) = 'fly';
UPDATE catalog_word SET icon = '🦗' WHERE LOWER(text_en) = 'grasshopper';
UPDATE catalog_word SET icon = '🐞' WHERE LOWER(text_en) = 'ladybug';
UPDATE catalog_word SET icon = '🦟' WHERE LOWER(text_en) = 'mosquito';
UPDATE catalog_word SET icon = '🦋' WHERE LOWER(text_en) = 'moth';
UPDATE catalog_word SET icon = '🐌' WHERE LOWER(text_en) = 'snail';
UPDATE catalog_word SET icon = '🕷️' WHERE LOWER(text_en) = 'spider';
UPDATE catalog_word SET icon = '🐜' WHERE LOWER(text_en) = 'termite';
UPDATE catalog_word SET icon = '🐝' WHERE LOWER(text_en) = 'wasp';
UPDATE catalog_word SET icon = '🪱' WHERE LOWER(text_en) = 'worm';

-- ── Jobs ──────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🚀' WHERE LOWER(text_en) = 'astronaut';
UPDATE catalog_word SET icon = '👨‍🍳' WHERE LOWER(text_en) = 'chef';
UPDATE catalog_word SET icon = '🦷' WHERE LOWER(text_en) = 'dentist';
UPDATE catalog_word SET icon = '🩺' WHERE LOWER(text_en) = 'doctor';
UPDATE catalog_word SET icon = '🚗' WHERE LOWER(text_en) = 'driver';
UPDATE catalog_word SET icon = '👨‍🌾' WHERE LOWER(text_en) = 'farmer';
UPDATE catalog_word SET icon = '👨‍🚒' WHERE LOWER(text_en) = 'firefighter';
UPDATE catalog_word SET icon = '💉' WHERE LOWER(text_en) = 'nurse';
UPDATE catalog_word SET icon = '🎨' WHERE LOWER(text_en) = 'painter';
UPDATE catalog_word SET icon = '🛩️' WHERE LOWER(text_en) = 'pilot';
UPDATE catalog_word SET icon = '👮' WHERE LOWER(text_en) = 'police officer';
UPDATE catalog_word SET icon = '🎤' WHERE LOWER(text_en) = 'singer';
UPDATE catalog_word SET icon = '👩‍🏫' WHERE LOWER(text_en) = 'teacher';
UPDATE catalog_word SET icon = '🐾' WHERE LOWER(text_en) = 'vet';

-- ── Music ─────────────────────────────────────────────────────────────────────
-- Lưu ý: 'bell' và 'drum' xuất hiện ở cả Music và School/Toys.
-- Các lệnh dưới không có topic_id vì text_en là duy nhất trong topic đó.
UPDATE catalog_word SET icon = '🎶' WHERE LOWER(text_en) = 'flute';
UPDATE catalog_word SET icon = '🎸' WHERE LOWER(text_en) = 'guitar';
UPDATE catalog_word SET icon = '🎵' WHERE LOWER(text_en) = 'harp';
UPDATE catalog_word SET icon = '🎹' WHERE LOWER(text_en) = 'piano';
UPDATE catalog_word SET icon = '🪘' WHERE LOWER(text_en) = 'tambourine';
UPDATE catalog_word SET icon = '🎺' WHERE LOWER(text_en) = 'trumpet';
UPDATE catalog_word SET icon = '🎻' WHERE LOWER(text_en) = 'violin';
UPDATE catalog_word SET icon = '🎶' WHERE LOWER(text_en) = 'xylophone';
-- 'bell' cũng có ở School — dùng subquery để phân biệt
UPDATE catalog_word SET icon = '🔔'
  WHERE LOWER(text_en) = 'bell'
    AND topic_id = (SELECT id FROM catalog_topic WHERE name_en = 'Music');
-- 'drum' cũng có ở Toys — dùng subquery để phân biệt
UPDATE catalog_word SET icon = '🥁'
  WHERE LOWER(text_en) = 'drum'
    AND topic_id = (SELECT id FROM catalog_topic WHERE name_en = 'Music');

-- ── Nature ────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🌵' WHERE LOWER(text_en) = 'cactus';
UPDATE catalog_word SET icon = '🔥' WHERE LOWER(text_en) = 'fire';
UPDATE catalog_word SET icon = '🌸' WHERE LOWER(text_en) = 'flower';
UPDATE catalog_word SET icon = '🌱' WHERE LOWER(text_en) = 'grass';
UPDATE catalog_word SET icon = '🍃' WHERE LOWER(text_en) = 'leaf';
UPDATE catalog_word SET icon = '⛰️' WHERE LOWER(text_en) = 'mountain';
UPDATE catalog_word SET icon = '🌴' WHERE LOWER(text_en) = 'palm tree';
UPDATE catalog_word SET icon = '🪨' WHERE LOWER(text_en) = 'rock';
UPDATE catalog_word SET icon = '🌹' WHERE LOWER(text_en) = 'rose';
UPDATE catalog_word SET icon = '🌱' WHERE LOWER(text_en) = 'seedling';
UPDATE catalog_word SET icon = '🌳' WHERE LOWER(text_en) = 'tree';
UPDATE catalog_word SET icon = '🌋' WHERE LOWER(text_en) = 'volcano';

-- ── Numbers ───────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '8️⃣' WHERE LOWER(text_en) = 'eight';
UPDATE catalog_word SET icon = '🔢' WHERE LOWER(text_en) = 'eleven';
UPDATE catalog_word SET icon = '5️⃣' WHERE LOWER(text_en) = 'fifty';
UPDATE catalog_word SET icon = '🥇' WHERE LOWER(text_en) = 'first';
UPDATE catalog_word SET icon = '5️⃣' WHERE LOWER(text_en) = 'five';
UPDATE catalog_word SET icon = '4️⃣' WHERE LOWER(text_en) = 'four';
UPDATE catalog_word SET icon = '💯' WHERE LOWER(text_en) = 'hundred';
UPDATE catalog_word SET icon = '9️⃣' WHERE LOWER(text_en) = 'nine';
UPDATE catalog_word SET icon = '1️⃣' WHERE LOWER(text_en) = 'one';
UPDATE catalog_word SET icon = '🥈' WHERE LOWER(text_en) = 'second';
UPDATE catalog_word SET icon = '7️⃣' WHERE LOWER(text_en) = 'seven';
UPDATE catalog_word SET icon = '6️⃣' WHERE LOWER(text_en) = 'six';
UPDATE catalog_word SET icon = '🔟' WHERE LOWER(text_en) = 'ten';
UPDATE catalog_word SET icon = '🔢' WHERE LOWER(text_en) = 'thirteen';
UPDATE catalog_word SET icon = '3️⃣' WHERE LOWER(text_en) = 'three';
UPDATE catalog_word SET icon = '🔢' WHERE LOWER(text_en) = 'twelve';
UPDATE catalog_word SET icon = '🔢' WHERE LOWER(text_en) = 'twenty';
UPDATE catalog_word SET icon = '2️⃣' WHERE LOWER(text_en) = 'two';
UPDATE catalog_word SET icon = '0️⃣' WHERE LOWER(text_en) = 'zero';

-- ── Reptiles ──────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🐊' WHERE LOWER(text_en) = 'alligator';
UPDATE catalog_word SET icon = '🦎' WHERE LOWER(text_en) = 'chameleon';
UPDATE catalog_word SET icon = '🐍' WHERE LOWER(text_en) = 'cobra';
UPDATE catalog_word SET icon = '🐊' WHERE LOWER(text_en) = 'crocodile';
UPDATE catalog_word SET icon = '🦕' WHERE LOWER(text_en) = 'dinosaur';
UPDATE catalog_word SET icon = '🐉' WHERE LOWER(text_en) = 'dragon';
UPDATE catalog_word SET icon = '🐸' WHERE LOWER(text_en) = 'frog';
UPDATE catalog_word SET icon = '🦎' WHERE LOWER(text_en) = 'gecko';
UPDATE catalog_word SET icon = '🦎' WHERE LOWER(text_en) = 'iguana';
UPDATE catalog_word SET icon = '🦎' WHERE LOWER(text_en) = 'lizard';
UPDATE catalog_word SET icon = '🐍' WHERE LOWER(text_en) = 'python';
UPDATE catalog_word SET icon = '🐍' WHERE LOWER(text_en) = 'snake';
UPDATE catalog_word SET icon = '🐢' WHERE LOWER(text_en) = 'tortoise';
-- 'turtle' cũng có ở Sea animals — dùng subquery
UPDATE catalog_word SET icon = '🐢'
  WHERE LOWER(text_en) = 'turtle'
    AND topic_id = (SELECT id FROM catalog_topic WHERE name_en = 'Reptiles');

-- ── School ────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🧮' WHERE LOWER(text_en) = 'abacus';
UPDATE catalog_word SET icon = '🎒' WHERE LOWER(text_en) = 'backpack';
-- 'bell' cũng có ở Music — dùng subquery
UPDATE catalog_word SET icon = '🔔'
  WHERE LOWER(text_en) = 'bell'
    AND topic_id = (SELECT id FROM catalog_topic WHERE name_en = 'School');
UPDATE catalog_word SET icon = '📚' WHERE LOWER(text_en) = 'book';
UPDATE catalog_word SET icon = '🖍️' WHERE LOWER(text_en) = 'crayon';
UPDATE catalog_word SET icon = '🌍' WHERE LOWER(text_en) = 'globe';
UPDATE catalog_word SET icon = '🔬' WHERE LOWER(text_en) = 'microscope';
UPDATE catalog_word SET icon = '📓' WHERE LOWER(text_en) = 'notebook';
UPDATE catalog_word SET icon = '🎨' WHERE LOWER(text_en) = 'paint';
UPDATE catalog_word SET icon = '📎' WHERE LOWER(text_en) = 'paperclip';
UPDATE catalog_word SET icon = '🖊️' WHERE LOWER(text_en) = 'pen';
UPDATE catalog_word SET icon = '✏️' WHERE LOWER(text_en) = 'pencil';
UPDATE catalog_word SET icon = '📏' WHERE LOWER(text_en) = 'ruler';
UPDATE catalog_word SET icon = '✂️' WHERE LOWER(text_en) = 'scissors';

-- ── Sea animals ───────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🐡' WHERE LOWER(text_en) = 'blowfish';
UPDATE catalog_word SET icon = '🦀' WHERE LOWER(text_en) = 'crab';
UPDATE catalog_word SET icon = '🐬' WHERE LOWER(text_en) = 'dolphin';
UPDATE catalog_word SET icon = '🎐' WHERE LOWER(text_en) = 'jellyfish';
UPDATE catalog_word SET icon = '🦞' WHERE LOWER(text_en) = 'lobster';
UPDATE catalog_word SET icon = '🐙' WHERE LOWER(text_en) = 'octopus';
UPDATE catalog_word SET icon = '🦦' WHERE LOWER(text_en) = 'otter';
UPDATE catalog_word SET icon = '🦭' WHERE LOWER(text_en) = 'seal';
UPDATE catalog_word SET icon = '🦈' WHERE LOWER(text_en) = 'shark';
UPDATE catalog_word SET icon = '🦐' WHERE LOWER(text_en) = 'shrimp';
UPDATE catalog_word SET icon = '🦑' WHERE LOWER(text_en) = 'squid';
UPDATE catalog_word SET icon = '🐠' WHERE LOWER(text_en) = 'tropical fish';
-- 'turtle' cũng có ở Reptiles — dùng subquery
UPDATE catalog_word SET icon = '🐢'
  WHERE LOWER(text_en) = 'turtle'
    AND topic_id = (SELECT id FROM catalog_topic WHERE name_en = 'Sea animals');
UPDATE catalog_word SET icon = '🐳' WHERE LOWER(text_en) = 'whale';

-- ── Shapes ────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '➡️' WHERE LOWER(text_en) = 'arrow';
UPDATE catalog_word SET icon = '⭕' WHERE LOWER(text_en) = 'circle';
UPDATE catalog_word SET icon = '🍦' WHERE LOWER(text_en) = 'cone';
UPDATE catalog_word SET icon = '❌' WHERE LOWER(text_en) = 'cross';
UPDATE catalog_word SET icon = '🧊' WHERE LOWER(text_en) = 'cube';
UPDATE catalog_word SET icon = '🥫' WHERE LOWER(text_en) = 'cylinder';
UPDATE catalog_word SET icon = '🔷' WHERE LOWER(text_en) = 'diamond';
UPDATE catalog_word SET icon = '❤️' WHERE LOWER(text_en) = 'heart';
UPDATE catalog_word SET icon = '➖' WHERE LOWER(text_en) = 'line';
UPDATE catalog_word SET icon = '⭕' WHERE LOWER(text_en) = 'oval';
UPDATE catalog_word SET icon = '🔷' WHERE LOWER(text_en) = 'pentagon';
UPDATE catalog_word SET icon = '🟪' WHERE LOWER(text_en) = 'rectangle';
UPDATE catalog_word SET icon = '🟥' WHERE LOWER(text_en) = 'square';
-- 'star' cũng có ở Weather — dùng subquery
UPDATE catalog_word SET icon = '⭐'
  WHERE LOWER(text_en) = 'star'
    AND topic_id = (SELECT id FROM catalog_topic WHERE name_en = 'Shapes');
UPDATE catalog_word SET icon = '🔺' WHERE LOWER(text_en) = 'triangle';

-- ── Sports ────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '⚾' WHERE LOWER(text_en) = 'baseball';
UPDATE catalog_word SET icon = '🏀' WHERE LOWER(text_en) = 'basketball';
UPDATE catalog_word SET icon = '🎳' WHERE LOWER(text_en) = 'bowling';
UPDATE catalog_word SET icon = '🥊' WHERE LOWER(text_en) = 'boxing';
UPDATE catalog_word SET icon = '🚴' WHERE LOWER(text_en) = 'cycling';
UPDATE catalog_word SET icon = '🏅' WHERE LOWER(text_en) = 'medal';
UPDATE catalog_word SET icon = '🏃' WHERE LOWER(text_en) = 'running';
UPDATE catalog_word SET icon = '⛷️' WHERE LOWER(text_en) = 'skiing';
UPDATE catalog_word SET icon = '⚽' WHERE LOWER(text_en) = 'soccer';
UPDATE catalog_word SET icon = '🏊' WHERE LOWER(text_en) = 'swimming';
UPDATE catalog_word SET icon = '🎾' WHERE LOWER(text_en) = 'tennis';
UPDATE catalog_word SET icon = '🏆' WHERE LOWER(text_en) = 'trophy';
UPDATE catalog_word SET icon = '🏐' WHERE LOWER(text_en) = 'volleyball';

-- ── Time ──────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🌤️' WHERE LOWER(text_en) = 'afternoon';
UPDATE catalog_word SET icon = '📅' WHERE LOWER(text_en) = 'friday';
UPDATE catalog_word SET icon = '📅' WHERE LOWER(text_en) = 'monday';
UPDATE catalog_word SET icon = '🗓️' WHERE LOWER(text_en) = 'month';
UPDATE catalog_word SET icon = '🌅' WHERE LOWER(text_en) = 'morning';
UPDATE catalog_word SET icon = '🌃' WHERE LOWER(text_en) = 'night';
UPDATE catalog_word SET icon = '📅' WHERE LOWER(text_en) = 'saturday';
UPDATE catalog_word SET icon = '📅' WHERE LOWER(text_en) = 'sunday';
UPDATE catalog_word SET icon = '📅' WHERE LOWER(text_en) = 'thursday';
UPDATE catalog_word SET icon = '📅' WHERE LOWER(text_en) = 'today';
UPDATE catalog_word SET icon = '📆' WHERE LOWER(text_en) = 'tomorrow';
UPDATE catalog_word SET icon = '📅' WHERE LOWER(text_en) = 'tuesday';
UPDATE catalog_word SET icon = '📅' WHERE LOWER(text_en) = 'wednesday';
UPDATE catalog_word SET icon = '📅' WHERE LOWER(text_en) = 'week';
UPDATE catalog_word SET icon = '📆' WHERE LOWER(text_en) = 'year';
UPDATE catalog_word SET icon = '🗓️' WHERE LOWER(text_en) = 'yesterday';

-- ── Toys ──────────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '⚽' WHERE LOWER(text_en) = 'ball';
UPDATE catalog_word SET icon = '🎈' WHERE LOWER(text_en) = 'balloon';
UPDATE catalog_word SET icon = '🧱' WHERE LOWER(text_en) = 'blocks';
UPDATE catalog_word SET icon = '🎲' WHERE LOWER(text_en) = 'dice';
UPDATE catalog_word SET icon = '🪆' WHERE LOWER(text_en) = 'doll';
-- 'drum' cũng có ở Music — dùng subquery
UPDATE catalog_word SET icon = '🥁'
  WHERE LOWER(text_en) = 'drum'
    AND topic_id = (SELECT id FROM catalog_topic WHERE name_en = 'Toys');
UPDATE catalog_word SET icon = '🪁' WHERE LOWER(text_en) = 'kite';
UPDATE catalog_word SET icon = '🔵' WHERE LOWER(text_en) = 'marbles';
UPDATE catalog_word SET icon = '🧩' WHERE LOWER(text_en) = 'puzzle';
UPDATE catalog_word SET icon = '🤖' WHERE LOWER(text_en) = 'robot';
UPDATE catalog_word SET icon = '🛴' WHERE LOWER(text_en) = 'scooter';
UPDATE catalog_word SET icon = '🛝' WHERE LOWER(text_en) = 'slide';
UPDATE catalog_word SET icon = '🔝' WHERE LOWER(text_en) = 'spinning top';
UPDATE catalog_word SET icon = '🎠' WHERE LOWER(text_en) = 'swing';
UPDATE catalog_word SET icon = '🧸' WHERE LOWER(text_en) = 'teddy bear';
UPDATE catalog_word SET icon = '🚗' WHERE LOWER(text_en) = 'toy car';
UPDATE catalog_word SET icon = '🚂' WHERE LOWER(text_en) = 'train set';
UPDATE catalog_word SET icon = '🪀' WHERE LOWER(text_en) = 'yo-yo';

-- ── Vegetables ────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '🥦' WHERE LOWER(text_en) = 'broccoli';
UPDATE catalog_word SET icon = '🥬' WHERE LOWER(text_en) = 'cabbage';
UPDATE catalog_word SET icon = '🥕' WHERE LOWER(text_en) = 'carrot';
UPDATE catalog_word SET icon = '🥬' WHERE LOWER(text_en) = 'celery';
UPDATE catalog_word SET icon = '🌽' WHERE LOWER(text_en) = 'corn';
UPDATE catalog_word SET icon = '🥒' WHERE LOWER(text_en) = 'cucumber';
UPDATE catalog_word SET icon = '🍆' WHERE LOWER(text_en) = 'eggplant';
UPDATE catalog_word SET icon = '🧄' WHERE LOWER(text_en) = 'garlic';
UPDATE catalog_word SET icon = '🥬' WHERE LOWER(text_en) = 'lettuce';
UPDATE catalog_word SET icon = '🍄' WHERE LOWER(text_en) = 'mushroom';
UPDATE catalog_word SET icon = '🧅' WHERE LOWER(text_en) = 'onion';
UPDATE catalog_word SET icon = '🥜' WHERE LOWER(text_en) = 'peanut';
UPDATE catalog_word SET icon = '🌶️' WHERE LOWER(text_en) = 'pepper';
UPDATE catalog_word SET icon = '🥔' WHERE LOWER(text_en) = 'potato';
UPDATE catalog_word SET icon = '🎃' WHERE LOWER(text_en) = 'pumpkin';
UPDATE catalog_word SET icon = '🥕' WHERE LOWER(text_en) = 'radish';
UPDATE catalog_word SET icon = '🥬' WHERE LOWER(text_en) = 'spinach';
UPDATE catalog_word SET icon = '🍅' WHERE LOWER(text_en) = 'tomato';

-- ── Vehicles ──────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '✈️' WHERE LOWER(text_en) = 'airplane';
UPDATE catalog_word SET icon = '🚑' WHERE LOWER(text_en) = 'ambulance';
UPDATE catalog_word SET icon = '🚲' WHERE LOWER(text_en) = 'bicycle';
UPDATE catalog_word SET icon = '⛵' WHERE LOWER(text_en) = 'boat';
UPDATE catalog_word SET icon = '🚌' WHERE LOWER(text_en) = 'bus';
UPDATE catalog_word SET icon = '🚗' WHERE LOWER(text_en) = 'car';
UPDATE catalog_word SET icon = '🚒' WHERE LOWER(text_en) = 'fire engine';
UPDATE catalog_word SET icon = '🚁' WHERE LOWER(text_en) = 'helicopter';
UPDATE catalog_word SET icon = '🏍️' WHERE LOWER(text_en) = 'motorcycle';
UPDATE catalog_word SET icon = '🚓' WHERE LOWER(text_en) = 'police car';
UPDATE catalog_word SET icon = '🚀' WHERE LOWER(text_en) = 'rocket';
UPDATE catalog_word SET icon = '🚢' WHERE LOWER(text_en) = 'ship';
UPDATE catalog_word SET icon = '🚕' WHERE LOWER(text_en) = 'taxi';
UPDATE catalog_word SET icon = '🚜' WHERE LOWER(text_en) = 'tractor';
UPDATE catalog_word SET icon = '🚆' WHERE LOWER(text_en) = 'train';
UPDATE catalog_word SET icon = '🚚' WHERE LOWER(text_en) = 'truck';

-- ── Weather ───────────────────────────────────────────────────────────────────
UPDATE catalog_word SET icon = '☁️' WHERE LOWER(text_en) = 'cloud';
UPDATE catalog_word SET icon = '🌫️' WHERE LOWER(text_en) = 'fog';
UPDATE catalog_word SET icon = '⚡' WHERE LOWER(text_en) = 'lightning';
UPDATE catalog_word SET icon = '🌙' WHERE LOWER(text_en) = 'moon';
UPDATE catalog_word SET icon = '🌧️' WHERE LOWER(text_en) = 'rain';
UPDATE catalog_word SET icon = '❄️' WHERE LOWER(text_en) = 'snow';
UPDATE catalog_word SET icon = '⛄' WHERE LOWER(text_en) = 'snowman';
-- 'star' cũng có ở Shapes — dùng subquery
UPDATE catalog_word SET icon = '⭐'
  WHERE LOWER(text_en) = 'star'
    AND topic_id = (SELECT id FROM catalog_topic WHERE name_en = 'Weather');
UPDATE catalog_word SET icon = '☀️' WHERE LOWER(text_en) = 'sun';
UPDATE catalog_word SET icon = '🌪️' WHERE LOWER(text_en) = 'tornado';
UPDATE catalog_word SET icon = '☂️' WHERE LOWER(text_en) = 'umbrella';
UPDATE catalog_word SET icon = '💨' WHERE LOWER(text_en) = 'wind';

-- ===========================================================================
-- END OF SCRIPT
-- ===========================================================================
