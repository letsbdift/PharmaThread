# PharmaThread - Pharmacy Management & POS System

PharmaThread is a full-featured, enterprise-grade Pharmacy Management, Drug Inventory, and Point of Sale (POS) system built with **Django**, **Tailwind CSS**, and modern web standards.

## Key Features

- **Point of Sale (POS)**: Fast barcode/drug search, billing, invoice generation, discount & tax calculations.
- **Drug Master & Inventory**: Expiry tracking, batch control, re-order levels, supplier mappings.
- **Procurement (GRN)**: Goods Received Notes, stock inward updates, purchase rate tracking.
- **Financial & P&L Reports**: Real-time sales summaries, profit & loss reports, revenue analytics.
- **Responsive Mobile Navigation**: Adaptive slide-out navigation drawer designed specifically for mobile Chrome and handheld devices.
- **Progressive Web App (PWA)**: Installable, lightweight, with offline-friendly static caching.
- **Standalone Offline Bundles**: Supports offline local deployments with standalone launchers.

## Tech Stack

- **Backend**: Python 3.10+, Django 4+
- **Frontend**: HTML5, Tailwind CSS, Phosphor Icons, JavaScript
- **Database**: SQLite (default / development), PostgreSQL / MySQL compatible
- **Deployment**: Configured for PythonAnywhere (`pharmathread.pythonanywhere.com`) & standalone Windows runtime

## Setup & Running Locally

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install django requests reportlab
   ```

3. Run database migrations:
   ```bash
   python manage.py migrate
   ```

4. Start development server:
   ```bash
   python manage.py runserver
   ```
