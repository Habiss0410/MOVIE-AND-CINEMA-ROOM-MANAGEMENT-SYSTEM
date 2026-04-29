"""
app.py  –  Cinema Room Management System
Usage: python app.py
Requires: pip install mysql-connector-python tabulate
"""
import sys
import mysql.connector
import os
from tabulate import tabulate
from datetime import datetime

# ── Global Session State ───────────────────────────────────────────────────
SESSION = {
    "user": None,
    "pw":   None,
    "role": None # 'admin' or 'clerk'
}

def get_conn():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user=SESSION["user"],
            password=SESSION["pw"],
            database="cinema_db"
        )
        return conn
    except mysql.connector.Error as e:
        print(f"\n  [!] DATABASE ERROR: {e.msg}")
        print("  Possible reasons: MySQL Server stopped or Network issue.")
        input("  Press Enter to exit...")
        sys.exit(1)

# ── Utilities ────────────────────────────────────────────────────────────────
def print_table(rows, headers):
    if not rows:
        print("  (No records found)\n")
    else:
        print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
        print()

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_seat_map(screening_id):
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            
            # Retrieve room capacity and name for the specific screening
            cur.execute("""
                SELECT r.Capacity, r.RoomName 
                FROM Screenings s 
                JOIN CinemaRooms r ON s.RoomID = r.RoomID 
                WHERE s.ScreeningID = %s""", (screening_id,))
            res = cur.fetchone()
            
            if not res:
                print(f"  [!] Screening ID {screening_id} not found.")
                return
                
            capacity, room_name = res

            # Retrieve list of seats already booked for this screening
            cur.execute("SELECT SeatNumber FROM Tickets WHERE ScreeningID = %s", (screening_id,))
            booked_seats = [row[0] for row in cur.fetchall()]

        print(f"\n  ── SEAT MAP: {room_name} (Screening #{screening_id}) ──")
        
        # Grid Configuration (10 columns per row)
        cols = 10
        rows = (capacity + cols - 1) // cols
        
        for r in range(rows):
            row_label = chr(65 + r)  # Generates Row A, B, C...
            row_str = f"  {row_label} |"
            
            for c in range(1, cols + 1):
                seat_id = f"{row_label}{c}"
                
                # Stop printing if we exceed total room capacity
                if ((r * cols) + c) > capacity: 
                    break
                
                # Visual Logic: [X] for Sold, [ID] for Available
                if seat_id in booked_seats:
                    row_str += "  [X]  "
                else:
                    # ^3 centers the seat ID (e.g., [ A1 ])
                    row_str += f" [{seat_id:^3}]"
            print(row_str)
            
        print("  " + "─" * 55)
        print("  Status: [X] = Sold | [ID] = Available\n")
        
    except Exception as e:
        print(f"  [!] Error loading seat map: {e}")

# ── Security: Authentication & Role Check ────────────────────────────────────
def login():
    global SESSION

    print("\n" + "═"*45)
    print("      🎬 CINEMA SYSTEM LOGIN 🎬")
    print("═"*45)

    u = input("  Username: ").strip()
    p = input("  Password: ").strip()

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user=u,
            password=p,
            database="cinema_db"
        )
        cur = conn.cursor()
        
        try:
            cur.execute("SET ROLE ALL")
        except:
            pass
        cur.execute("SELECT CURRENT_ROLE()")
        raw_role = cur.fetchone()[0]  
        role_name = ""
        if raw_role and raw_role != "NONE":
            role_name = raw_role.split('@')[0].strip("'`").lower()

        SESSION["user"] = u
        SESSION["pw"] = p   
        SESSION["role"] = "clerk"  

        if role_name == "cinema_admin_role":
            SESSION["role"] = "admin"
        elif role_name == "cinema_clerk_role":
            SESSION["role"] = "clerk"

        cur.close()
        conn.close()

        print(f"\n  ✓ Login successful! Role: {SESSION['role'].upper()}")
        return True

    except mysql.connector.Error as e:
        if e.errno == 1045:
            print("\n  ✗ Access Denied: Invalid username or password.")
        elif e.errno == 2003:
            print("\n  ✗ Connection Error: MySQL Server is not running.")
        else:
            print(f"\n  ✗ Database Error [{e.errno}]: {e.msg}")
        return False
    
# ════════════════════════════════════════════════════════════════════════════
# MOVIE MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

def list_movies():
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT MovieID, MovieTitle, Genre, DurationMinutes FROM Movies ORDER BY MovieID")
            rows = cur.fetchall()
            print_table(rows, ["ID", "Title", "Genre", "Duration (min)"])
    except mysql.connector.Error as e:
        print(f"  ✗ Error fetching movies: {e.msg}\n")

def add_movie():
    print("\n  ── Add New Movie ──")
    title    = input("  Title    : ").strip()
    genre    = input("  Genre    : ").strip()
    duration = input("  Duration (minutes): ").strip()
    if not title or not genre or not duration.isdigit():
        print("  ✗ Invalid input.\n"); return
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO Movies (MovieTitle, Genre, DurationMinutes) VALUES (%s,%s,%s)", (title, genre, int(duration)))
            conn.commit()
            print(f"  ✓ Movie added ID={cur.lastrowid}\n")
    except mysql.connector.Error as e:
        print(f"  ✗ Error: {e.msg}\n")

def edit_movie():
    print("\n  ── Edit Movie ──")
    mid = input("  Movie ID to edit: ").strip()
    if not mid.isdigit(): print("  ✗ Invalid ID.\n"); return
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Movies WHERE MovieID=%s", (int(mid),))
            row = cur.fetchone()
            if not row: print("  ✗ Not found.\n"); return
            t = input(f"  New Title ({row[1]}): ").strip() or row[1]
            g = input(f"  New Genre ({row[2]}): ").strip() or row[2]
            d = input(f"  New Dur   ({row[3]}): ").strip() or str(row[3])
            cur.execute("UPDATE Movies SET MovieTitle=%s, Genre=%s, DurationMinutes=%s WHERE MovieID=%s", (t, g, int(d), int(mid)))
            conn.commit()
            print("  ✓ Movie Updated.\n")
    except mysql.connector.Error as e:
        print(f"  ✗ Error: {e.msg}\n")

def movie_menu():
    if SESSION["role"] != "admin":
        print("  ✗ Access Denied: Admin role required.\n")
        return
    while True:
        print("\n  ╔══ MOVIE MANAGEMENT ══╗")
        print("  1. List all movies")
        print("  2. Add movie")
        print("  3. Edit movie")
        print("  0. Back")
        ch = input("  > ").strip()
        if ch == "1": list_movies()
        elif ch == "2": add_movie()
        elif ch == "3": edit_movie()
        elif ch == "0": break

# ════════════════════════════════════════════════════════════════════════════
# CINEMA ROOM MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

def list_rooms():
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT RoomID, RoomName, Capacity FROM CinemaRooms ORDER BY RoomID")
            print_table(cur.fetchall(), ["ID", "Room Name", "Capacity"])
    except mysql.connector.Error as e:
        print(f"  ✗ Error: {e.msg}\n")

def add_room():
    print("\n  ── Add Cinema Room ──")
    name = input("  Room Name : ").strip()
    cap  = input("  Capacity  : ").strip()
    
    if not name or not cap.isdigit():
        print("  ✗ Invalid input: Name is required and Capacity must be a number.\n")
        return

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO CinemaRooms (RoomName, Capacity) VALUES (%s,%s)", (name, int(cap)))
            conn.commit()
            print(f"  ✓ Room added with ID={cur.lastrowid}\n")
    except mysql.connector.Error as e:
        print(f"  ✗ Database Error: {e.msg}\n")
    except Exception as e:
        print(f"  ⚠️ Unexpected Error: {e}\n")

def room_menu():
    if SESSION["role"] != "admin":
        print("  ✗ Access Denied: Admin role required.\n")
        return
    while True:
        print("\n  ╔══ ROOM MANAGEMENT ══╗")
        print("  1. List all rooms")
        print("  2. Add room")
        print("  0. Back")
        ch = input("  > ").strip()
        if ch == "1": list_rooms()
        elif ch == "2": add_room()
        elif ch == "0": break

# ════════════════════════════════════════════════════════════════════════════
# SCREENING MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

def list_screenings():
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT ScreeningID, ScreeningDate, ScreeningTime, MovieTitle, RoomName, AvailableSeats, OccupancyRate FROM vw_DailyScreenings ORDER BY ScreeningDate, ScreeningTime")
            rows = [(*r[:-1], f"{r[-1]}%") for r in cur.fetchall()]
            print_table(rows, ["ID","Date","Time","Movie","Room","Available","Occupancy"])
    except mysql.connector.Error as e:
        print(f"  ✗ Error: {e.msg}\n")

def add_screening():
    print("\n  ── Add Screening ──")
    list_movies()
    mid = input("  Movie ID    : ").strip()
    list_rooms()
    rid = input("  Room ID     : ").strip()
    d, t = input("  Date (YYYY-MM-DD): ").strip(), input("  Time (HH:MM): ").strip()
    try:
        datetime.strptime(d, "%Y-%m-%d")
        datetime.strptime(t, "%H:%M")
    except ValueError:
        print("  ✗ Invalid date/time format.\n"); return

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO Screenings (MovieID, RoomID, ScreeningDate, ScreeningTime) VALUES (%s,%s,%s,%s)",
                        (int(mid), int(rid), d, t + ":00"))
            conn.commit()
            print(f"  ✓ Screening added with ID={cur.lastrowid}\n")
    except (mysql.connector.Error, ValueError) as e:
        msg = e.msg if hasattr(e, 'msg') else str(e)
        print(f"  ✗ Error: {msg}\n")

def screening_menu():
    while True:
        print("\n  ╔══ SCREENING MANAGEMENT ══╗")
        print("  1. List all screenings")
        print("  2. Add screening")
        print("  0. Back")
        ch = input("  > ").strip()
        if ch == "1": list_screenings()
        elif ch == "2": add_screening()
        elif ch == "0": break

# ════════════════════════════════════════════════════════════════════════════
# CUSTOMER MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

def list_customers():
    if SESSION["role"] == "clerk":
        target_table = "vw_ClerkCustomerView"
        headers = ["ID", "Customer Name", "Phone (Masked)"]
    else:
        target_table = "Customers"
        headers = ["ID", "Customer Name", "Phone Number"]

    print(f"\n  ── Customer List (Access Level: {SESSION['role'].upper()}) ──")
    
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {target_table} ORDER BY CustomerID")
            rows = cur.fetchall()
            print_table(rows, headers)
    except mysql.connector.Error as e:
        print(f"  ✗ Security Error: You do not have permission to access {target_table}.")
        print(f"  Details: {e.msg}\n")

def add_customer():
    print("\n  ── Add Customer ──")
    name  = input("  Name  : ").strip()
    phone = input("  Phone : ").strip()
    if not name or not phone:
        print("  ✗ Invalid input.\n"); return
    
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO Customers (CustomerName, PhoneNumber) VALUES (%s,%s)", (name, phone))
            conn.commit()
            print(f"  ✓ Customer added with ID={cur.lastrowid}\n")
    except mysql.connector.Error as e:
        print(f"  ✗ Database Error: {e.msg}\n")
    except Exception as e:
        print(f"  ⚠️ Unexpected Error: {e}\n")

def update_customer():
    print("\n  ── Update Customer ──")
    cid = input("  Customer ID: ").strip()
    if not cid.isdigit(): print("  ✗ Invalid ID.\n"); return

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Customers WHERE CustomerID=%s", (int(cid),))
            row = cur.fetchone()
            if not row: print("  ✗ Not found.\n"); return
            n = input(f"  New Name ({row[1]}): ").strip() or row[1]
            p = input(f"  New Phone ({row[2]}): ").strip() or row[2]
            cur.execute("UPDATE Customers SET CustomerName=%s, PhoneNumber=%s WHERE CustomerID=%s", (n, p, int(cid)))
            conn.commit()
            print("  ✓ Updated.\n")
    except mysql.connector.Error as e:
        print(f"  ✗ Error: {e.msg}\n")

def customer_menu():
    while True:
        print("\n  ╔══ CUSTOMER MANAGEMENT ══╗")
        print("  1. List customers")
        print("  2. Add customer")
        print("  3. Update customer")
        print("  0. Back")
        ch = input("  > ").strip()
        if ch == "1": list_customers()
        elif ch == "2": add_customer()
        elif ch == "3": update_customer()
        elif ch == "0": break

# ════════════════════════════════════════════════════════════════════════════
# TICKET BOOKING
# ════════════════════════════════════════════════════════════════════════════

def book_ticket():
    print("\n" + "═"*45)
    print("      🎟️  NEW TICKET BOOKING")
    print("═"*45)
    
    list_screenings()
    scr_id = input("  ➤ Enter Screening ID to view seats: ").strip()
    if not scr_id.isdigit():
        print("  ✗ Error: Invalid ID format.\n")
        return
    
    show_seat_map(int(scr_id))
    
    list_customers()
    cust_id = input("  ➤ Enter Customer ID: ").strip()
    if not cust_id.isdigit():
        print("  ✗ Error: Invalid Customer ID.\n")
        return
        
    seat = input("  ➤ Choose Seat Number (e.g., A1): ").strip().upper()
    if not seat:
        print("  ✗ Error: Seat Number is required.\n")
        return

    price_raw = input("  ➤ Enter Ticket Price (VND): ").strip()
    try:
        price = float(price_raw)
        if price <= 0:
            print("  ✗ Error: Price must be a positive number.\n")
            return
    except ValueError:
        print("  ✗ Error: Please enter a valid numeric value for Price.\n")
        return

    conn = get_conn()
    cur = conn.cursor()
    try:
        conn.start_transaction()
        result = cur.callproc("sp_BookTicket", [int(cust_id), int(scr_id), seat, price, ""])
        res = result[4]
        
        if res and res.startswith("SUCCESS"):
            conn.commit()  
            print(f"\n  ✓ {res}\n")
        else:
            conn.rollback() 
            print(f"\n  ✗ BOOKING FAILED: {res if res else 'Unknown database error.'}\n")

    except mysql.connector.Error as e:
        conn.rollback()
        print(f"\n  [!] System Error: {e.msg}\n")
    finally:
        cur.close()
        conn.close()

def cancel_ticket():
    print("\n  ── Cancel Ticket (Secure Transaction) ──")
    tid = input("  Ticket ID to cancel: ").strip()
    if not tid.isdigit(): return
    
    conn = get_conn()
    cur = conn.cursor()
    try:
        conn.start_transaction() 
        result = cur.callproc("sp_CancelTicket", [int(tid), ""])
        res = result[1]
        
        if res and res.startswith("SUCCESS"):
            conn.commit()
            print(f"  ✓ {res}\n")
        else:
            conn.rollback()
            print(f"  ✗ {res if res else 'Unknown error'}\n")
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"  ✗ System Error: {e.msg}\n")
    finally:
        cur.close()
        conn.close()

def check_seats():
    print("\n  ── Check Available Seats & Map ──")
    scr_id = input("  Enter Screening ID: ").strip()
    
    if not scr_id.isdigit(): 
        print("  ✗ Invalid ID format.\n")
        return
    
    show_seat_map(int(scr_id))
    
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.callproc("sp_AvailableSeats", [int(scr_id)])
            
            for result in cur.stored_results():
                rows = result.fetchall()
                if rows:
                    formatted_rows = [(r[0], f"{r[1]}%") for r in rows]
                    print_table(formatted_rows, ["Total Available Seats", "Occupancy Rate"])
                else:
                    print("  [!] No data found for this screening.")
                    
    except mysql.connector.Error as e:
        print(f"  [!] Database Error: {e.msg}")

def ticket_menu():
    while True:
        print("\n  ╔══ TICKET BOOKING ══╗")
        print("  1. Book a ticket")
        print("  2. Cancel a ticket")
        print("  3. Check available seats")
        print("  0. Back")
        ch = input("  > ").strip()
        if ch == "1": book_ticket()
        elif ch == "2": cancel_ticket()
        elif ch == "3": check_seats()
        elif ch == "0": break

# ════════════════════════════════════════════════════════════════════════════
# REPORTS
# ════════════════════════════════════════════════════════════════════════════

def report_sales():
    print("\n  ── Sales Report by Date Range ──")
    d_from = input("  From date (YYYY-MM-DD): ").strip()
    d_to   = input("  To date   (YYYY-MM-DD): ").strip()
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.callproc("sp_SalesReport", [d_from, d_to])
            for result in cur.stored_results():
                rows = [(*r[:-1], f"{r[-1]}%") for r in result.fetchall()]
                print_table(rows, ["Date","Movie","Room","Tickets","Revenue","Occupancy"])
    except mysql.connector.Error as e:
        print(f"  ✗ Error: {e.msg}\n")

def report_by_movie():
    print("\n  ── Revenue by Movie ──")
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT MovieTitle, Genre, TotalTicketsSold, TotalRevenue FROM vw_RevenueByMovie ORDER BY TotalRevenue DESC")
            print_table(cur.fetchall(), ["Movie","Genre","Tickets Sold","Revenue (VND)"])
    except mysql.connector.Error as e:
        print(f"  ✗ Error: {e.msg}\n")

def report_customer():
    print("\n  ── Customer Booking History ──")
    cid = input("  Customer ID (0 for all): ").strip()
    if not cid.isdigit(): return
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            if cid == "0":
                cur.execute("SELECT CustomerName, MovieTitle, ScreeningDate, BookingTime, SeatNumber, Price FROM vw_CustomerBookings ORDER BY BookingTime DESC")
            else:
                cur.execute("SELECT CustomerName, MovieTitle, ScreeningDate, BookingTime, SeatNumber, Price FROM vw_CustomerBookings WHERE CustomerID=%s ORDER BY BookingTime DESC", (int(cid),))
            print_table(cur.fetchall(), ["Customer", "Movie", "Show Date", "Booked At", "Seat", "Price"])
    except mysql.connector.Error as e:
        print(f"  ✗ Error: {e.msg}\n")

def report_performance_udf():
    print("\n  ── Screening Performance (UDF Real-time) ──")
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.ScreeningID, m.MovieTitle, s.ScreeningDate,
                       fn_TotalRevenue(s.ScreeningID) AS Revenue
                FROM Screenings s
                JOIN Movies m ON s.MovieID = m.MovieID
                ORDER BY Revenue DESC
            """)
            rows = cur.fetchall()
        print_table(rows, ["ID", "Movie", "Date", "Revenue (VND)"])
    except mysql.connector.Error as e:
        print(f"  [!] Error: {e.msg}\n")

def view_audit_logs():
    print("\n  ── SYSTEM AUDIT LOGS (Admin Access Only) ──")
    
    if SESSION["role"] != "admin":
        print("  ✗ Access Denied: Admin privileges required to view logs.\n")
        return

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            
            query = """
                SELECT 
                    DATE_FORMAT(ActionTime, '%H:%i:%s %d/%m') as Time, 
                    UserDB, 
                    ActionType, 
                    TableName, 
                    Description 
                FROM SystemLogs 
                ORDER BY ActionTime DESC 
                LIMIT 20
            """
            cur.execute(query)
            rows = cur.fetchall()
            
            headers = ["Time", "Executed By", "Action", "Table", "Change Details"]
            
            print_table(rows, headers)
            
    except mysql.connector.Error as e:
        print(f"  [!] Error fetching audit data: {e.msg}\n")


def report_menu():
    while True:
        print("\n  ╔══ REPORTS MANAGEMENT ══╗")
        print("  1. Daily Sales Report")
        print("  2. Revenue by Movie" + ("" if SESSION["role"]=='admin' else " [ADMIN ONLY]"))
        print("  3. Customer Booking History")
        print("  4. High-Level Performance (UDF)" + ("" if SESSION["role"]=='admin' else " [ADMIN ONLY]"))
        print("  5. View System Audit Logs" + ("" if SESSION["role"]=='admin' else " [ADMIN ONLY]"))
        print("  0. Back")
        
        ch = input("  > ").strip()
        clear ()
        if ch == "1": report_sales()
        elif ch == "2" and SESSION["role"] == "admin": report_by_movie()
        elif ch == "3": report_customer()
        elif ch == "4" and SESSION["role"] == "admin": report_performance_udf() 
        elif ch == "5" and SESSION["role"] == "admin": view_audit_logs()
        elif ch == "0": break
        elif ch in ["2", "4", "5"]: print("  ✗ Access Denied.\n")

# ════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ════════════════════════════════════════════════════════════════════════════

BANNER = """
╔══════════════════════════════════════════════════════╗
║     🎬  CINEMA ROOM MANAGEMENT SYSTEM  🎬            ║
║        NEU Database Management Project               ║
╚══════════════════════════════════════════════════════╝
"""

def main():
    clear ()
    print(BANNER)
    
    if not login():
        print("  System closed. Goodbye! 👋\n")
        sys.exit(0)

    while True:
        print(f"\n  LOGGED IN AS: {SESSION['user'].upper()} | ROLE: {SESSION['role'].upper()}")
        print("  " + "═"*45)
        
        if SESSION["role"] == "admin":
            print("  1. 🎬 Movie Management")
            print("  2. 🏢 Cinema Room Management")
            print("  3. 📅 Screening Management")
        else:
            print("  🔒 1-3. Admin Functions (Locked)")
            
        print("  4. 👤 Customer Management")
        print("  5. 🎟️ Ticket Booking")
        print("  6. 📊 Reports & Audit Logs")
        print("  0. 🚪 Exit")
        
        ch = input("\n  Choose > ").strip()
        clear()
        
        #Security Guard)
        if ch in ["1", "2", "3"] and SESSION["role"] != "admin":
            print("  ✗ ACCESS DENIED: You do not have permission to access Admin tools.\n")
            continue  

        if ch == "1":   movie_menu()
        elif ch == "2": room_menu()
        elif ch == "3": screening_menu()
        elif ch == "4": customer_menu()
        elif ch == "5": ticket_menu()
        elif ch == "6": report_menu()
        elif ch == "0": 
            print("  Logging out... Goodbye! 👋\n")
            break
        else:
            print("  ✗ Invalid choice. Please try again.\n")

if __name__ == "__main__":
    main()
