import pygame
import sys
import random
import math
from datetime import datetime, timedelta
import json

# Ekran boyutları (görüntü için uygun)
WIDTH, HEIGHT = 1609, 907

# Ölçekleme fonksiyonu (haritaya göre)
def scale_point(x, y, original_width=1609, original_height=907, target_width=WIDTH, target_height=HEIGHT):
    scaled_x = int(x / original_width * target_width)
    scaled_y = int(y / original_height * target_height)
    return (scaled_x, scaled_y)

# Renkler
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Araç renkleri
def get_car_colors():
    return [
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 165, 0), (128, 0, 128),
        (0, 255, 255), (255, 255, 0), (128, 128, 128), (255, 105, 180), (0, 128, 128)
    ]
CAR_COLORS = get_car_colors()

# Gerçek koordinatlara göre tanımlı durak bağlantıları
ROAD_NETWORK = {
    (1530, 300): [(1400, 380)],
    (1400, 380): [(1530, 300), (1470, 600), (1300, 430)],
    (1470, 600): [(1400, 380), (1389, 764)],  # Eski bağlantı (1075, 830) kaldırıldı
    (930, 830): [(1389, 764), (677, 660)],  # Eski bağlantı (1470, 600) kaldırıldı
    (1389, 764): [(1470, 600), (930, 830)],
    (677, 660): [(930, 830), (500, 580), (756, 562)],
    (500, 580): [(677, 660), (250, 470)],
    (250, 470): [(500, 580), (120, 209)],
    (120, 209): [(250, 470), (500, 165),(500, 100)],
    (500, 165): [(120, 209)],
    (500, 100): [(830, 220),(120, 209)],
    (830, 220): [(500, 100), (1000, 350)],
    (1000, 350): [(830, 220), (1145, 430)],
    (1145, 430): [(1000, 350), (1300, 430), (1100, 510)],
    (1300, 430): [(1145, 430), (1400, 380)],
    (1100, 510): [(1145, 430)],
    (756, 562): [(677, 660), (990, 685)],
    (990, 685): [(756, 562)]
}

ENTRY_EXIT_POINT = (1530, 300)
TARGETS = list(ROAD_NETWORK.keys())

# Ölçeklenmiş değerler
def scale_network(network):
    return {scale_point(*k): [scale_point(*v) for v in vs] for k, vs in network.items()}
SCALED_ROAD_NETWORK = scale_network(ROAD_NETWORK)
SCALED_TARGETS = [scale_point(*t) for t in TARGETS]
SCALED_ENTRY_EXIT_POINT = scale_point(*ENTRY_EXIT_POINT)

active_vehicles = []
gps_log = []

class Vehicle:
    car_icon = None
    def __init__(self, id, color, pos):
        self.id = id
        self.original_color = color  # Orijinal rengi sakla
        self.x, self.y = pos
        self.current_node = pos
        self.target_node = random.choice(TARGETS)
        self.route = self.find_route(self.current_node, self.target_node)
        self.next_node = self.route[1] if len(self.route) > 1 else self.target_node
        self.speed = random.uniform(1.0, 2.0)
        self.status = "moving"
        self.park_end_time = None  # Park etmenin biteceği zaman
        self.entry_time = datetime.now()
        self.exit_time = self.entry_time + timedelta(seconds=random.randint(20, 60))
        self.is_exiting = False
        self.moving_time = 0
        self.last_move_tick = pygame.time.get_ticks()
        self.total_parked_time = 0  # Toplam park ettiği süre
        self.park_start_time = None  # Park etmeye başladığı zaman

        # Ziyaret sayacı - en fazla 4 yere uğrayacak
        self.visited_locations = []
        self.max_visits = 4
        self.arrived_at_target = False  # Hedefe ulaşıp ulaşmadığını kontrol için

        # Giriş saatini yazdır
        print(
            f"{self.id} plakalı araç kampüse giriş yaptı. Giriş saati: {self.entry_time.strftime('%H:%M:%S')}, Renk: {self.original_color}")
        if Vehicle.car_icon is None:
            # Araba ikonunu sadece 1 kez yükle ve boyutlandır
            original_icon = pygame.image.load("../carico.png").convert_alpha()
            Vehicle.car_icon = pygame.transform.scale(original_icon, (32, 32))
    def find_route(self, start, end):
        # Basit BFS ile yol bulma
        if start == end:
            return [start]

        # En yakın geçerli düğümü bul
        def find_nearest_node(pos):
            min_dist = float('inf')
            nearest = None
            for node in ROAD_NETWORK.keys():
                dist = math.hypot(pos[0] - node[0], pos[1] - node[1])
                if dist < min_dist:
                    min_dist = dist
                    nearest = node
            return nearest

        # Başlangıç ve bitiş noktalarını geçerli düğümlere çevir
        start_node = find_nearest_node(start) if start not in ROAD_NETWORK else start
        end_node = find_nearest_node(end) if end not in ROAD_NETWORK else end

        if start_node == end_node:
            return [start_node]

        queue = [(start_node, [start_node])]
        visited = set()

        while queue:
            current, path = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            if current == end_node:
                return path

            if current in ROAD_NETWORK:
                for neighbor in ROAD_NETWORK[current]:
                    if neighbor not in visited:
                        queue.append((neighbor, path + [neighbor]))

        # Fallback: En yakın ortak noktayı bul
        print(f"UYARI: {start_node} -> {end_node} arası rota bulunamadı, fallback kullanılıyor")

        # Merkez nokta üzerinden gitmeyi dene
        center_node = (325, 250)
        if start_node != center_node and end_node != center_node:
            path_to_center = self.find_route_simple(start_node, center_node)
            path_from_center = self.find_route_simple(center_node, end_node)
            if len(path_to_center) > 1 and len(path_from_center) > 1:
                return path_to_center + path_from_center[1:]  # Merkez noktayı tekrar etme

        # Son çare: Ana dikdörtgenin köşeleri üzerinden git
        corners = [(150, 150), (450, 150), (450, 350), (150, 350)]
        for corner in corners:
            if corner != start_node and corner != end_node:
                path_to_corner = self.find_route_simple(start_node, corner)
                path_from_corner = self.find_route_simple(corner, end_node)
                if len(path_to_corner) > 1 and len(path_from_corner) > 1:
                    return path_to_corner + path_from_corner[1:]

        return [start_node]  # Hiçbir yol bulunamadı, yerinde kal

    def find_route_simple(self, start, end):
        """Basit BFS - döngüsel çağrıyı önlemek için"""
        if start == end:
            return [start]

        queue = [(start, [start])]
        visited = set()

        while queue:
            current, path = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            if current == end:
                return path

            if current in ROAD_NETWORK:
                for neighbor in ROAD_NETWORK[current]:
                    if neighbor not in visited:
                        queue.append((neighbor, path + [neighbor]))

        return [start]  # Yol bulunamadı

    def move(self):
        now = pygame.time.get_ticks()
        dt = (now - self.last_move_tick) / 1000.0
        self.last_move_tick = now

        # Çıkış zamanı kontrolü
        if not self.is_exiting and datetime.now() >= self.exit_time:
            self.is_exiting = True
            self.target_node = ENTRY_EXIT_POINT
            self.route = self.find_route(self.current_node, self.target_node)
            self.next_node = self.route[1] if len(self.route) > 1 else self.target_node

        # PARK DURUMU KONTROLÜ - EN ÖNCELİK
        if self.status == "parked":
            # Park süresinin bitip bitmediğini kontrol et
            if self.park_end_time and datetime.now() >= self.park_end_time:
                # Park süresi bitti, devam et
                if self.park_start_time is not None:
                    parked_time = (datetime.now() - self.park_start_time).total_seconds()
                    self.total_parked_time += parked_time
                    print(f"{self.id} parktan çıkıyor. Park süresi: {parked_time:.1f} saniye")
                    self.park_start_time = None
                    self.park_end_time = None

                self.status = "moving"

                # En fazla 4 yere uğradıysa çıkışa yönel
                if len(self.visited_locations) >= self.max_visits:
                    self.is_exiting = True
                    self.target_node = ENTRY_EXIT_POINT
                    self.route = self.find_route(self.current_node, self.target_node)
                    self.next_node = self.route[1] if len(self.route) > 1 else self.target_node
                    self.arrived_at_target = False
                elif self.is_exiting:
                    self.target_node = ENTRY_EXIT_POINT
                    self.route = self.find_route(self.current_node, self.target_node)
                    self.next_node = self.route[1] if len(self.route) > 1 else self.target_node
                    self.arrived_at_target = False
                else:
                    # Park süresi bittikten sonra mutlaka yeni hedef seç (mevcut konum hariç)
                    available_targets = [t for t in TARGETS if t != self.current_node]
                    if not available_targets:
                        self.target_node = random.choice(TARGETS)
                    else:
                        self.target_node = random.choice(available_targets)

                    # Rota hesapla ve kontrol et
                    self.route = self.find_route(self.current_node, self.target_node)

                    # Rota geçerliliğini kontrol et
                    if len(self.route) > 1:
                        self.next_node = self.route[1]
                    else:
                        # Rota problemi varsa, yeni hedef seç
                        print(f"UYARI: {self.id} için rota problemi, yeni hedef seçiliyor")
                        self.target_node = random.choice([t for t in TARGETS if t != self.current_node])
                        self.route = self.find_route(self.current_node, self.target_node)
                        self.next_node = self.route[1] if len(self.route) > 1 else self.target_node

                    self.arrived_at_target = False  # Yeni hedef için bayrağı sıfırla

                    # Debug: Park çıkışı bilgisi
                    print(f"{self.id} parktan çıktı, yeni hedef: {self.target_node}, sonraki düğüm: {self.next_node}")
            else:
                # Hala park halinde - HİÇ HAREKET ETME
                return

        # Hedefe ulaştığında park etme kontrolü (sadece bir kez çalışsın)
        if (self.current_node == self.target_node and
                self.status == "moving" and
                not self.is_exiting and
                not self.arrived_at_target):

            self.arrived_at_target = True

            if self.current_node not in self.visited_locations:
                self.visited_locations.append(self.current_node)

            if len(self.visited_locations) >= self.max_visits:
                self.is_exiting = True
                self.target_node = ENTRY_EXIT_POINT
                self.route = self.find_route(self.current_node, self.target_node)
                self.next_node = self.route[1] if len(self.route) > 1 else self.target_node
                self.arrived_at_target = False
                return

            # Park etme kararı
            if random.random() < 0.8:
                self.status = "parked"
                park_duration = random.randint(3, 8)
                self.park_start_time = datetime.now()
                self.park_end_time = self.park_start_time + timedelta(seconds=park_duration)
                print(f"{self.id} hedefe ulaştı ({self.current_node}) - park ediyor. Süre: {park_duration} saniye")
                return  # Park etmeye başladığında fonksiyonu sonlandır
            else:
                # Park etmeyecekse yeni hedef seç
                available_targets = [t for t in TARGETS if t != self.current_node]
                if not available_targets:
                    self.target_node = random.choice(TARGETS)
                else:
                    self.target_node = random.choice(available_targets)

                self.route = self.find_route(self.current_node, self.target_node)
                self.next_node = self.route[1] if len(self.route) > 1 else self.target_node
                self.arrived_at_target = False
                return

        # Yol üzerinde gerçekçi hareket - yoldan çıkmayı engelle
        if self.current_node != self.next_node:
            # Sadece geçerli yol bağlantısı varsa hareket et
            if self.next_node in ROAD_NETWORK.get(self.current_node, []):
                # Bir sonraki düğüme doğru düzgün hareket et
                dx = self.next_node[0] - self.x
                dy = self.next_node[1] - self.y
                dist = math.hypot(dx, dy)

                if dist < self.speed:
                    # Düğüme ulaştık
                    self.x, self.y = self.next_node
                    self.current_node = self.next_node

                    if self.current_node == ENTRY_EXIT_POINT:
                        return "exited"

                    if self.current_node == self.target_node:
                        # Hedefe ulaştık
                        if self.is_exiting:
                            return "exited"
                        # Park kontrolü yukarıda yapılıyor, burada sadece rota güncellenir
                    else:
                        # Rotadaki bir sonraki düğüme geç
                        current_index = self.route.index(self.current_node)
                        if current_index + 1 < len(self.route):
                            self.next_node = self.route[current_index + 1]
                        else:
                            # Rota tamamlandı, yeni rota hesapla
                            self.route = self.find_route(self.current_node, self.target_node)
                            self.next_node = self.route[1] if len(self.route) > 1 else self.target_node
                else:
                    # Düğüme doğru hareket et - sadece geçerli yol üzerinde
                    self.x += self.speed * dx / dist
                    self.y += self.speed * dy / dist
            else:
                # Geçersiz yol bağlantısı - yeni rota hesapla
                print(f"UYARI: {self.id} geçersiz yol bağlantısı ({self.current_node} -> {self.next_node})")

                self.route = self.find_route(self.current_node, self.target_node)

                if len(self.route) > 1:
                    self.next_node = self.route[1]
                else:
                    # Rota bulunamadıysa yeni hedef seç
                    self.target_node = random.choice([t for t in TARGETS if t != self.current_node])
                    self.route = self.find_route(self.current_node, self.target_node)
                    self.next_node = self.route[1] if len(self.route) > 1 else self.target_node

        # Hareket süresi sayacı
        if self.status == "moving":
            self.moving_time += dt

    def draw(self, surface):
        icon = Vehicle.car_icon
        if self.status == "parked":
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            icon.blit(Vehicle.car_icon, (0, 0))
            # Üstüne gri filtre uygula
            icon.fill((64, 64, 64, 150), special_flags=pygame.BLEND_RGBA_MULT)

        surface.blit(icon, (int(self.x) - 16, int(self.y) - 16))  # Ortalamak için

        # Plaka bilgisini çiz
        font = pygame.font.Font(None, 16)
        status_text = "P" if self.status == "parked" else "M"
        text = font.render(f"{self.id}-{status_text}", True, BLACK)
        text_rect = text.get_rect()
        surface.blit(text, (int(self.x) - text_rect.width // 2, int(self.y) - 30))

    def get_gps_like_data(self):
        return {
            "id": self.id,
            "latitude": round(self.y, 3),
            "longitude": round(self.x, 3),
            "speed": round(self.speed if self.status == "moving" else 0, 2),
            "status": self.status,
            "timestamp": datetime.now().isoformat()
        }




def start_vehicle_simulation(plate):
    color = random.choice(CAR_COLORS)
    entry_point = ENTRY_EXIT_POINT
 # Dikdörtgen kenarındaki giriş noktası
    vehicle = Vehicle(plate, color, entry_point)
    active_vehicles.append(vehicle)

def run_simulation(plate_queue):
    global background  # dışarıdaki background'a erişim
    background = pygame.image.load("../saumap.png")
    WIDTH, HEIGHT = background.get_size()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    def draw_campus(surface):
        surface.blit(background, (0, 0))

        # Yollar
        for node, connections in SCALED_ROAD_NETWORK.items():
            for connected_node in connections:
                pygame.draw.line(surface, (200, 200, 200), node, connected_node, 3)

        # Duraklar
        for node in SCALED_TARGETS:
            pygame.draw.circle(surface, (255, 0, 0), node, 14)
            pygame.draw.circle(surface, (255, 255, 255), node, 16, 3)

        # Giriş-çıkış
        pygame.draw.circle(surface, (255, 0, 0), SCALED_ENTRY_EXIT_POINT, 12)
        pygame.draw.circle(surface, (0, 0, 0), SCALED_ENTRY_EXIT_POINT, 12, 3)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    pygame.display.set_caption("Kampüs Simülasyonu")
    clock = pygame.time.Clock()

    while True:
        # 🔥 1. KUYRUKTAN PLAKA AL
        while not plate_queue.empty():
            plate = plate_queue.get()
            print(f"[KUYRUK] Yeni plaka alındı: {plate}")
            start_vehicle_simulation(plate)

        # 🔄 2. Pygame olay döngüsü
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Simülasyon kullanıcı tarafından kapatıldı
                with open("../GPS/gps_log.json", "w", encoding="utf-8") as f:
                    json.dump(gps_log, f, ensure_ascii=False, indent=2)
                print("Simülasyon kullanıcı tarafından kapatıldı. GPS verileri kaydedildi.")
                pygame.quit()
                return

        screen.fill(WHITE)
        draw_campus(screen)

        exited_vehicles = []

        for v in active_vehicles:
            result = v.move()
            v.draw(screen)
            gps_log.append(v.get_gps_like_data())
            if result == "exited":
                current_time = datetime.now()
                if v.status == "parked" and v.park_start_time is not None:
                    v.total_parked_time += (current_time - v.park_start_time).total_seconds()
                total_time = current_time - v.entry_time
                actual_moving_time = total_time.total_seconds() - v.total_parked_time
                print(f"{v.id} plakalı araç kampüsten çıkış yaptı.")
                print(f"  Giriş saati: {v.entry_time.strftime('%H:%M:%S')}")
                print(f"  Çıkış saati: {current_time.strftime('%H:%M:%S')}")
                print(f"  Kampüste toplam kalma süresi: {int(total_time.total_seconds())} saniye")
                print(f"  Park ettiği toplam süre: {int(v.total_parked_time)} saniye")
                print(f"  Gerçek hareket ettiği süre: {int(actual_moving_time)} saniye")
                from db_utils import log_vehicle_to_db
                log_vehicle_to_db(
                    v.id,
                    v.entry_time,
                    current_time,
                    int(total_time.total_seconds()),
                    int(v.total_parked_time),
                    int(actual_moving_time)
                )
                print("-" * 50)
                exited_vehicles.append(v)

        for v in exited_vehicles:
            active_vehicles.remove(v)

        pygame.display.flip()
        clock.tick(60)