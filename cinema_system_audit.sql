USE cinema_db;

-- 1. DATABASE STRUCTURE FOR LOGS
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS SystemLogs;
CREATE TABLE SystemLogs (
    LogID       INT AUTO_INCREMENT PRIMARY KEY,
    ActionTime  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UserDB      VARCHAR(100),  -- Database User
    ActionType  VARCHAR(20),   -- INSERT, UPDATE, DELETE
    TableName   VARCHAR(50),   -- Tables affected
    Description TEXT,          -- Alter details
    INDEX (ActionTime),       
    INDEX (TableName)
);

DELIMITER $$

-- 2. TICKET & BOOKING LOGS
-- -----------------------------------------------------------------------------

-- Book
CREATE TRIGGER trg_LogInsertTicket
AFTER INSERT ON Tickets
FOR EACH ROW
BEGIN
    INSERT INTO SystemLogs (UserDB, ActionType, TableName, Description)
    VALUES (USER(), 'INSERT', 'Tickets', 
            CONCAT('SUCCESS: New Booking. TicketID: ', NEW.TicketID, 
                   ' | Seat: ', NEW.SeatNumber, 
                   ' | Price: ', FORMAT(NEW.Price, 0), ' VND'));
END$$

-- Cancel
CREATE TRIGGER trg_LogDeleteTicket
AFTER DELETE ON Tickets
FOR EACH ROW
BEGIN
    INSERT INTO SystemLogs (UserDB, ActionType, TableName, Description)
    VALUES (USER(), 'DELETE', 'Tickets', 
            CONCAT('SUCCESS: Ticket Cancelled. TicketID: ', OLD.TicketID, 
                   ' | Seat: ', OLD.SeatNumber));
END$$


-- 3. CUSTOMER MANAGEMENT LOGS
-- -----------------------------------------------------------------------------

-- Add
CREATE TRIGGER trg_LogInsertCustomer
AFTER INSERT ON Customers
FOR EACH ROW
BEGIN
    INSERT INTO SystemLogs (UserDB, ActionType, TableName, Description)
    VALUES (USER(), 'INSERT', 'Customers', 
            CONCAT('New Customer Added: ', NEW.CustomerName, ' | Phone: ', NEW.PhoneNumber));
END$$

-- Update
CREATE TRIGGER trg_LogUpdateCustomer
AFTER UPDATE ON Customers
FOR EACH ROW
BEGIN
    INSERT INTO SystemLogs (UserDB, ActionType, TableName, Description)
    VALUES (USER(), 'UPDATE', 'Customers', 
            CONCAT('Updated CID: ', OLD.CustomerID, 
                   ' | Name: ', OLD.CustomerName, ' -> ', NEW.CustomerName,
                   ' | Phone: ', OLD.PhoneNumber, ' -> ', NEW.PhoneNumber));
END$$


-- 4. MOVIE & SCREENING LOGS (ADMIN ACTIONS)
-- -----------------------------------------------------------------------------

-- Add
CREATE TRIGGER trg_LogInsertMovie
AFTER INSERT ON Movies
FOR EACH ROW
BEGIN
    INSERT INTO SystemLogs (UserDB, ActionType, TableName, Description)
    VALUES (USER(), 'INSERT', 'Movies', 
            CONCAT('Admin added movie: ', NEW.MovieTitle, ' | Genre: ', NEW.Genre));
END$$

-- Update Movie
CREATE TRIGGER trg_LogUpdateMovie
AFTER UPDATE ON Movies
FOR EACH ROW
BEGIN
    INSERT INTO SystemLogs (UserDB, ActionType, TableName, Description)
    VALUES (USER(), 'UPDATE', 'Movies', 
            CONCAT('Modified Movie ID: ', OLD.MovieID, 
                   ' | Title: "', OLD.MovieTitle, '" -> "', NEW.MovieTitle, '"'));
END$$

-- Update Screen
CREATE TRIGGER trg_LogUpdateScreening
AFTER UPDATE ON Screenings
FOR EACH ROW
BEGIN
    INSERT INTO SystemLogs (UserDB, ActionType, TableName, Description)
    VALUES (USER(), 'UPDATE', 'Screenings', 
            CONCAT('Screening ID ', OLD.ScreeningID, ' rescheduled to: ', NEW.ScreeningDate, ' ', NEW.ScreeningTime));
END$$

DELIMITER ;

-- 5. SECURITY & PERMISSIONS
-- -----------------------------------------------------------------------------

-- Admin: full administrative control over Logs
GRANT SELECT ON cinema_db.SystemLogs TO 'cinema_admin_role';

-- Clerk: only generate Logs (through Triggers) but cannot view or delete them
GRANT INSERT ON cinema_db.SystemLogs TO 'cinema_clerk_role';

FLUSH PRIVILEGES;

-- -----------------------------------------------------------------------------
-- END OF SCRIPT
-- -----------------------------------------------------------------------------