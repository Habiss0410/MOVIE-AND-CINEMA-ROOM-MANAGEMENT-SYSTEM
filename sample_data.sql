USE cinema_db;

-- ── Movies (10 rows) ───────────────────────────────────────
INSERT INTO Movies (MovieTitle, Genre, DurationMinutes) VALUES
  ('Interstellar', 'Sci-Fi', 169),
  ('The Dark Knight', 'Action', 152),
  ('Parasite', 'Thriller', 132),
  ('Toy Story 4', 'Animation', 100),
  ('Joker', 'Drama', 122),
  ('Avengers Endgame', 'Action', 181),
  ('Spirited Away', 'Animation', 125),
  ('La La Land', 'Romance', 128),
  ('Get Out', 'Horror', 104),
  ('Inception', 'Sci-Fi', 148);

-- ── CinemaRooms (10 rows) ──────────────────────────────────
INSERT INTO CinemaRooms (RoomName, Capacity) VALUES
  ('Room A - Premier', 50),
  ('Room B - Standard', 80),
  ('Room C - IMAX', 120),
  ('Room D - VIP', 30),
  ('Room E - Standard', 90),
  ('Room F - 4DX', 60),
  ('Room G - Dolby', 70),
  ('Room H - Kids', 40),
  ('Room I - Standard', 100),
  ('Room J - Gold', 45);

-- ── Screenings (10 rows) ───────────────────────────────────
INSERT INTO Screenings (MovieID, RoomID, ScreeningDate, ScreeningTime) VALUES
  (1, 1, '2025-06-01', '09:00:00'),
  (2, 2, '2025-06-04', '11:00:00'),
  (3, 3, '2025-06-07', '13:30:00'),
  (4, 4, '2025-06-10', '16:00:00'),
  (5, 5, '2025-06-13', '18:30:00'),
  (6, 6, '2025-06-16', '21:00:00'),
  (7, 7, '2025-06-19', '09:00:00'),
  (8, 8, '2025-06-22', '11:00:00'),
  (9, 9, '2025-06-25', '13:30:00'),
  (10, 10, '2025-06-28', '16:00:00');

-- ── Customers (10 rows) ────────────────────────────────────
INSERT INTO Customers (CustomerName, PhoneNumber) VALUES
  ('Nguyen Van An', '0321234567'),
  ('Tran Thi Bao', '0331234568'),
  ('Le Van Chau', '0341234569'),
  ('Pham Thi Dung', '0351234570'),
  ('Hoang Van Hang', '0361234571'),
  ('Phan Thi Khanh', '0371234572'),
  ('Vu Van Linh', '0381234573'),
  ('Dang Thi Minh', '0391234574'),
  ('Bui Van Nam', '0961234575'),
  ('Do Thi Phuong', '0971234576');

-- ── Tickets (10 rows) ──────────────────────────────────────
INSERT INTO Tickets (CustomerID, ScreeningID, SeatNumber, Price) VALUES
  (1, 1, 'A1', 75000),
  (2, 2, 'B2', 85000),
  (3, 3, 'C3', 90000),
  (4, 4, 'A4', 95000),
  (5, 5, 'B5', 100000),
  (6, 6, 'C6', 120000),
  (7, 7, 'A7', 75000),
  (8, 8, 'B8', 85000),
  (9, 9, 'C9', 90000),
  (10, 10, 'A10', 95000);

-- Done! 10 rows per table inserted.
