# 🎬 Cinema Room Management System
> Project 08 — Database Management | NEU College of Technology  
> **Author:** Pham Thu Ha — 11247164

---

## 📖 Overview
A cinema management system built with MySQL and Python, supporting movie scheduling, ticket booking, seat management, and sales reporting — with role-based access control and a full audit trail.

---

## 🛠️ Tech Stack
- **Database:** MySQL 5.7 + MySQL Workbench
- **Language:** Python 3.12 (Anaconda)
- **Libraries:** `mysql-connector-python`, `tabulate`
- **Platform:** macOS (Apple M2) + VS Code

---

## 📁 Project Structure
```
├── schema.sql                # Tables, views, functions, procedures, triggers, roles
├── cinema_system_audit.sql   # SystemLogs table + 6 audit triggers
├── sample_data.sql           # Sample data (10 rows per table)
├── app.py                    # Python CLI application
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation                   
```

---

## 🚀 Quick Start

**1. Start MySQL Server:**
```bash
sudo /usr/local/mysql/support-files/mysql.server start
```

**2. Database Setup:** Import SQL files into MySQL Workbench in order:
```
schema.sql  ➔  cinema_system_audit.sql  ➔  sample_data.sql
```

**3. Python Setup:**
```bash
pip install mysql-connector-python tabulate
```

**4. Launch Application:**
```bash
python app.py
```

---

## 🔑 Usage

Login with one of two roles:

| Role | Username | Password | Access |
|---|---|---|---|
| Admin | `admin_user` | `Admin@Secure123` | Full access |
| Clerk | `clerk_user` | `Clerk@Secure123` | Booking & customers only |

---

## ⚙️ Features

| Module | Description |
|---|---|
| Movie Management | Add / edit movies — Admin only |
| Room Management | Manage cinema rooms — Admin only |
| Screening Schedule | Assign movies to rooms & times |
| Customer Management | Add/update customers; phone masked for Clerk |
| Ticket Booking | Visual seat map, book/cancel with transaction safety |
| Reports | Sales by date, revenue by movie, customer history, audit logs |

---

## 🗄️ Database Objects

| Type | Count | Examples |
|---|---|---|
| Tables | 6 | Movies, CinemaRooms, Screenings, Customers, Tickets, SystemLogs |
| Views | 4 | vw_DailyScreenings, vw_RevenueByMovie, vw_CustomerBookings, vw_ClerkCustomerView |
| Stored Procedures | 4 | sp_BookTicket, sp_CancelTicket, sp_AvailableSeats, sp_SalesReport |
| Functions | 2 | fn_OccupancyRate, fn_TotalRevenue |
| Triggers | 7 | trg_PreventOverbooking + 6 audit triggers |
| Indexes | 5 | 4 standard + 1 composite on (ScreeningDate, ScreeningTime) |

---

## 💡 Key Technical Highlights

> 🔒 **Transaction Safety** — Ticket booking and cancellation are wrapped in explicit transactions (`START TRANSACTION` / `ROLLBACK`), ensuring data consistency even on failure. Business logic is enforced inside Stored Procedures, keeping the application layer clean.

> ⚡ **Performance Optimization** — A composite index on `(ScreeningDate, ScreeningTime)` accelerates daily schedule lookups. Five targeted indexes on foreign key columns eliminate full-table scans on the most frequent JOIN queries.

> 🛡️ **Security & Data Masking (RBAC)** — Role-based access control separates Admin and Clerk privileges at the database level. Clerk users access `vw_ClerkCustomerView`, which automatically masks phone numbers (`032****567`), preventing exposure of sensitive customer data.

> 📋 **Audit Trail** — Six `AFTER` triggers automatically record every INSERT, UPDATE, and DELETE across Tickets, Customers, and Movies into a `SystemLogs` table — providing a tamper-evident history of all data changes without any application-level code.

---
