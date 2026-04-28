-- ============================================================
-- PROJECT 08: MOVIE AND CINEMA ROOM MANAGEMENT SYSTEM
-- Database: cinema_db
-- Author: [Pham Thu Ha - 11247164]
-- ============================================================

DROP DATABASE IF EXISTS cinema_db;
CREATE DATABASE cinema_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cinema_db;

-- ============================================================
-- TABLE STRUCTURES
-- ============================================================

CREATE TABLE Movies (
    MovieID     INT AUTO_INCREMENT PRIMARY KEY,
    MovieTitle  VARCHAR(255) NOT NULL,
    Genre       VARCHAR(100) NOT NULL,
    DurationMinutes INT NOT NULL CHECK (DurationMinutes > 0)
);

CREATE TABLE CinemaRooms (
    RoomID      INT AUTO_INCREMENT PRIMARY KEY,
    RoomName    VARCHAR(100) NOT NULL UNIQUE,
    Capacity    INT NOT NULL CHECK (Capacity > 0)
);

CREATE TABLE Screenings (
    ScreeningID     INT AUTO_INCREMENT PRIMARY KEY,
    MovieID         INT NOT NULL,
    RoomID          INT NOT NULL,
    ScreeningDate   DATE NOT NULL,
    ScreeningTime   TIME NOT NULL,
    FOREIGN KEY (MovieID) REFERENCES Movies(MovieID) ON DELETE CASCADE,
    FOREIGN KEY (RoomID)  REFERENCES CinemaRooms(RoomID) ON DELETE CASCADE,
    UNIQUE KEY uq_room_datetime (RoomID, ScreeningDate, ScreeningTime)
);

CREATE TABLE Customers (
    CustomerID      INT AUTO_INCREMENT PRIMARY KEY,
    CustomerName    VARCHAR(255) NOT NULL,
    PhoneNumber     VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE Tickets (
    TicketID        INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID      INT NOT NULL,
    ScreeningID     INT NOT NULL,
    SeatNumber      VARCHAR(10) NOT NULL,
    BookingTime     DATETIME DEFAULT CURRENT_TIMESTAMP,
    Price           DECIMAL(10,2) NOT NULL DEFAULT 85000,
    FOREIGN KEY (CustomerID)  REFERENCES Customers(CustomerID) ON DELETE CASCADE,
    FOREIGN KEY (ScreeningID) REFERENCES Screenings(ScreeningID) ON DELETE CASCADE,
    UNIQUE KEY uq_seat_screening (ScreeningID, SeatNumber)
);


-- ============================================================
-- VIEWS
-- ============================================================

-- View: Daily screening schedule with movie and room info
CREATE VIEW vw_DailyScreenings AS
SELECT
    s.ScreeningID,
    s.ScreeningDate,
    s.ScreeningTime,
    m.MovieTitle,
    m.Genre,
    m.DurationMinutes,
    r.RoomName,
    r.Capacity,
    COUNT(t.TicketID) AS TicketsSold,
    r.Capacity - COUNT(t.TicketID) AS AvailableSeats,
	ROUND(COUNT(t.TicketID) / r.Capacity * 100, 2) AS OccupancyRate

FROM Screenings s
JOIN Movies       m ON s.MovieID = m.MovieID
JOIN CinemaRooms  r ON s.RoomID  = r.RoomID
LEFT JOIN Tickets t ON s.ScreeningID = t.ScreeningID
GROUP BY s.ScreeningID, s.ScreeningDate, s.ScreeningTime,
         m.MovieTitle, m.Genre, m.DurationMinutes, r.RoomName, r.Capacity;

-- View: Revenue report per movie
CREATE VIEW vw_RevenueByMovie AS
SELECT
    m.MovieID,
    m.MovieTitle,
    m.Genre,
    COUNT(t.TicketID) AS TotalTicketsSold,
    SUM(t.Price)      AS TotalRevenue
FROM Movies m
JOIN Screenings s ON m.MovieID = s.MovieID
JOIN Tickets    t ON s.ScreeningID = t.ScreeningID
GROUP BY m.MovieID, m.MovieTitle, m.Genre;

-- View: Customer booking history
CREATE VIEW vw_CustomerBookings AS
SELECT
    c.CustomerID,
    c.CustomerName,
    c.PhoneNumber,
    m.MovieTitle,
    s.ScreeningDate,
    s.ScreeningTime,
    r.RoomName,
    t.SeatNumber,
    t.Price,
    t.BookingTime
FROM Customers  c
JOIN Tickets    t ON c.CustomerID   = t.CustomerID
JOIN Screenings s ON t.ScreeningID  = s.ScreeningID
JOIN Movies     m ON s.MovieID      = m.MovieID
JOIN CinemaRooms r ON s.RoomID      = r.RoomID;

-- View: Customer security masking view for Clerk role
CREATE VIEW vw_ClerkCustomerView AS
SELECT 
    CustomerID, 
    CustomerName, 
    CONCAT(LEFT(PhoneNumber, 3), '****', RIGHT(PhoneNumber, 3)) AS MaskedPhone
FROM Customers;

-- ============================================================
-- USER DEFINED FUNCTIONS
-- ============================================================

DELIMITER $$

CREATE FUNCTION fn_OccupancyRate(p_ScreeningID INT)
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_capacity  INT;
    DECLARE v_sold      INT;
    SELECT r.Capacity INTO v_capacity
    FROM Screenings s JOIN CinemaRooms r ON s.RoomID = r.RoomID
    WHERE s.ScreeningID = p_ScreeningID;

    SELECT COUNT(*) INTO v_sold
    FROM Tickets WHERE ScreeningID = p_ScreeningID;

    IF v_capacity = 0 THEN RETURN 0; END IF;
    RETURN ROUND((v_sold / v_capacity) * 100, 2);
END$$

CREATE FUNCTION fn_TotalRevenue(p_ScreeningID INT)
RETURNS DECIMAL(12,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_revenue DECIMAL(12,2);
    SELECT COALESCE(SUM(Price), 0) INTO v_revenue
    FROM Tickets WHERE ScreeningID = p_ScreeningID;
    RETURN v_revenue;
END$$

-- ============================================================
-- STORED PROCEDURES
-- ============================================================

-- Procedure: Book a ticket
CREATE PROCEDURE sp_BookTicket(
    IN  p_CustomerID    INT,
    IN  p_ScreeningID   INT,
    IN  p_SeatNumber    VARCHAR(10),
    IN  p_Price         DECIMAL(10,2),
    OUT p_Result        VARCHAR(100)
)
sp_main: BEGIN
    DECLARE v_capacity  INT;
    DECLARE v_sold      INT;
    DECLARE v_exists    INT;

    -- Check seat already taken
    SELECT COUNT(*) INTO v_exists FROM Tickets
    WHERE ScreeningID = p_ScreeningID AND SeatNumber = p_SeatNumber;
    IF v_exists > 0 THEN
        SET p_Result = 'ERROR: Seat already booked.';
        LEAVE sp_main;
    END IF;

    -- Check capacity
    SELECT r.Capacity INTO v_capacity
    FROM Screenings s JOIN CinemaRooms r ON s.RoomID = r.RoomID
    WHERE s.ScreeningID = p_ScreeningID;

    SELECT COUNT(*) INTO v_sold FROM Tickets WHERE ScreeningID = p_ScreeningID;

    IF v_sold >= v_capacity THEN
        SET p_Result = 'ERROR: Room is fully booked.';
        LEAVE sp_main;
    END IF;

    INSERT INTO Tickets (CustomerID, ScreeningID, SeatNumber, Price)
    VALUES (p_CustomerID, p_ScreeningID, p_SeatNumber, p_Price);

    SET p_Result = CONCAT('SUCCESS: Ticket booked. TicketID=', LAST_INSERT_ID());
END sp_main$$

-- Procedure: Cancel a ticket
CREATE PROCEDURE sp_CancelTicket(
    IN  p_TicketID  INT,
    OUT p_Result    VARCHAR(100)
)
BEGIN
    DECLARE v_exists INT;
    SELECT COUNT(*) INTO v_exists FROM Tickets WHERE TicketID = p_TicketID;
    IF v_exists = 0 THEN
        SET p_Result = 'ERROR: Ticket not found.';
    ELSE
        DELETE FROM Tickets WHERE TicketID = p_TicketID;
        SET p_Result = 'SUCCESS: Ticket cancelled.';
    END IF;
END$$

-- Procedure: Check available seats for a screening
CREATE PROCEDURE sp_AvailableSeats(IN p_ScreeningID INT)
BEGIN
    SELECT r.Capacity - COUNT(t.TicketID) AS AvailableSeats,
           fn_OccupancyRate(p_ScreeningID) AS OccupancyRate
    FROM Screenings s
    JOIN CinemaRooms r ON s.RoomID = r.RoomID
    LEFT JOIN Tickets t ON s.ScreeningID = t.ScreeningID
    WHERE s.ScreeningID = p_ScreeningID
    GROUP BY r.Capacity;
END$$

-- Procedure: Sales report by date range
CREATE PROCEDURE sp_SalesReport(IN p_From DATE, IN p_To DATE)
BEGIN
    SELECT
        s.ScreeningDate,
        m.MovieTitle,
        r.RoomName,
        COUNT(t.TicketID)   AS TicketsSold,
        SUM(t.Price)        AS Revenue,
        fn_OccupancyRate(s.ScreeningID) AS OccupancyPct
    FROM Screenings s
    JOIN Movies      m ON s.MovieID = m.MovieID
    JOIN CinemaRooms r ON s.RoomID  = r.RoomID
    LEFT JOIN Tickets t ON s.ScreeningID = t.ScreeningID
    WHERE s.ScreeningDate BETWEEN p_From AND p_To
    GROUP BY s.ScreeningID
    ORDER BY s.ScreeningDate, s.ScreeningTime;
END$$

DELIMITER ;

-- ============================================================
-- TRIGGERS
-- ============================================================

DELIMITER $$

-- Trigger: Prevent overbooking before insert
CREATE TRIGGER trg_PreventOverbooking
BEFORE INSERT ON Tickets
FOR EACH ROW
BEGIN
    DECLARE v_capacity  INT;
    DECLARE v_sold      INT;

    SELECT r.Capacity INTO v_capacity
    FROM Screenings s JOIN CinemaRooms r ON s.RoomID = r.RoomID
    WHERE s.ScreeningID = NEW.ScreeningID;

    SELECT COUNT(*) INTO v_sold
    FROM Tickets WHERE ScreeningID = NEW.ScreeningID;

    IF v_sold >= v_capacity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Overbooking prevented: room is at full capacity.';
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- DATABASE SECURITY (Roles & Users)
-- ============================================================

-- Setup Roles
DROP ROLE IF EXISTS 'cinema_admin_role', 'cinema_clerk_role';
CREATE ROLE 'cinema_admin_role', 'cinema_clerk_role';

-- Admin: Full Access
GRANT ALL PRIVILEGES ON cinema_db.* TO 'cinema_admin_role';

-- Clerk: Restricted Access (Least Privilege Principle)
GRANT SELECT ON cinema_db.Movies TO 'cinema_clerk_role';
GRANT SELECT ON cinema_db.CinemaRooms TO 'cinema_clerk_role';
GRANT SELECT ON cinema_db.Screenings TO 'cinema_clerk_role';
GRANT SELECT ON cinema_db.vw_DailyScreenings TO 'cinema_clerk_role';
GRANT SELECT ON cinema_db.vw_ClerkCustomerView TO 'cinema_clerk_role';
GRANT INSERT, UPDATE ON cinema_db.Customers TO 'cinema_clerk_role';
GRANT SELECT ON cinema_db.Tickets TO 'cinema_clerk_role';
GRANT EXECUTE ON PROCEDURE cinema_db.sp_BookTicket TO 'cinema_clerk_role';
GRANT EXECUTE ON PROCEDURE cinema_db.sp_AvailableSeats TO 'cinema_clerk_role';
GRANT EXECUTE ON PROCEDURE cinema_db.sp_CancelTicket TO 'cinema_clerk_role';

-- User Assignments
CREATE USER IF NOT EXISTS 'admin_user'@'localhost' IDENTIFIED BY 'Admin@Secure123';
GRANT 'cinema_admin_role' TO 'admin_user'@'localhost';
SET DEFAULT ROLE 'cinema_admin_role' TO 'admin_user'@'localhost';

CREATE USER IF NOT EXISTS 'clerk_user'@'localhost' IDENTIFIED BY 'Clerk@Secure123';
GRANT 'cinema_clerk_role' TO 'clerk_user'@'localhost';
SET DEFAULT ROLE 'cinema_clerk_role' TO 'clerk_user'@'localhost';

FLUSH PRIVILEGES;

-- ============================================================
-- PERFORMANCE OPTIMIZATION (INDEXES)
-- ============================================================

-- 1. Standard Indexes for foreign keys and frequent text searches
CREATE INDEX idx_movie_title       ON Movies(MovieTitle);
CREATE INDEX idx_ticket_customer   ON Tickets(CustomerID);
CREATE INDEX idx_ticket_screening  ON Tickets(ScreeningID);
CREATE INDEX idx_screening_movie   ON Screenings(MovieID);

-- 2. Advanced Composite Index 
-- Optimizes daily schedule lookups and sorting by time
CREATE INDEX idx_screening_schedule ON Screenings(ScreeningDate, ScreeningTime);

-- 3. Maintenance Command
ANALYZE TABLE Movies, CinemaRooms, Screenings, Customers, Tickets;

