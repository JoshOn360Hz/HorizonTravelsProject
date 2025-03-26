# Imports

import random
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory,abort,send_file
import mysql.connector
from flask_bcrypt import Bcrypt
from datetime import datetime

# imports for the QR code generation and generating boarding pass

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import qrcode
from reportlab.lib.utils import ImageReader



# Configuring flask, bcrypt ( encrypting passwords) and setting the secret key

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'secret'  
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript from accessing the cookie that stores session info
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # Restrict cross-site cookie usage 
 

db_config = {
    "host": "localhost",
    "user": "root",
    "passwd": "webyear1",
    "database": "Database"
}


# Mapping and configuring what the index page does, in this case sending all the flight info to the form to allow the user to pick flights

@app.route('/')
def index():
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        query = """
        SELECT DISTINCT departure FROM Flights
        UNION
        SELECT DISTINCT arrival FROM Flights;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        locations = sorted([row[0] for row in results])
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        locations = []
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
    user_name = session.get('user_name')
    return render_template('index.html', locations=locations, user_name=user_name)


# Mapping and setting up what the login page does, in this case capturing email and password, checking them against the hashed database password and if they match, redirecting to the index page

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_error = False
    password_reset_success = False  # Add default value
    password_reset_error = False  # Add default value
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            query = "SELECT * FROM Users WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            if user and bcrypt.check_password_hash(user['pass'], password):
                session['user_id'] = user['a_num']
                session['user_name'] = f"{user['f_name']} {user['l_name']}"
                return redirect(url_for('index'))
            else:
                login_error = True
        finally:
            cursor.close()
            db.close()
    
    return render_template(
    'login.html',
    login_error=login_error or False,
    password_reset_success=password_reset_success or False,
    password_reset_error=password_reset_error or False
    )


# Mapping and setting up what the register page does, in this case capturing the first name, last name, email and password, hashing the password and inserting the user into the database


@app.route('/register', methods=['GET', 'POST'])
def register():
    account_created = False
    email_exists = False
    forgot_password_pin = None  # To pass to the modal later

    if request.method == 'POST':
        f_name = request.form['f_name']
        l_name = request.form['l_name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Generate a random 6-digit PIN
        forgot_password_pin = f"{random.randint(100000, 999999)}"

        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)

            # Check if email already exists
            check_query = "SELECT * FROM Users WHERE email = %s"
            cursor.execute(check_query, (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                email_exists = True
            else:
                # Insert the new user with the PIN
                insert_query = """
                INSERT INTO Users (f_name, l_name, email, pass, forgot_password_pin)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (f_name, l_name, email, hashed_password, forgot_password_pin))
                db.commit()
                account_created = True
        finally:
            cursor.close()
            db.close()

    return render_template(
        'register.html',
        account_created=account_created,
        email_exists=email_exists,
        forgot_password_pin=forgot_password_pin
    )


# Mapping and setting up what the logout page does, in this case clearing the session and redirecting to the index page

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
    
    

# Mapping and setting up what the my account page does, redirecting to login if not logged in, getting the user id, name, email and bookings from the database and displaying them on the page

@app.route('/account')
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_name = session.get('user_name')
    user_first_name, user_last_name = user_name.split(' ', 1)
    user_email = None
    recovery_pin = None
    bookings = []

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        
        # Fetch user details
        query_email = "SELECT email, forgot_password_pin FROM Users WHERE a_num = %s"
        cursor.execute(query_email, (user_id,))
        result = cursor.fetchone()
        
        if result:
            user_email = result['email']
            recovery_pin = result['forgot_password_pin']
        
        # Fetch bookings
        query_bookings = """
        SELECT 
            b.ref_num, 
            b.Fl_num_DEP, 
            b.PAX,
            DATE(b.departure_date) AS departure_date, 
            TIME(fs.departure_time) AS dep_time,
            f_departure.departure AS departure_airport, 
            f_departure.arrival AS arrival_airport,
            bd.B_Class AS business_class, 
            bd.Econ AS economy_class, 
            ti.price * b.PAX * (CASE WHEN bd.B_Class > 0 THEN 2 ELSE 1.0 END) AS total_price
        FROM Bookings b
        LEFT JOIN Flight_Schedules fs ON b.Fl_num_DEP = fs.f_num
        LEFT JOIN Flights f_departure ON fs.f_num = f_departure.f_num
        LEFT JOIN Booking_Details bd ON b.ref_num = bd.ref_num
        LEFT JOIN Ticket_Info ti ON b.Fl_num_DEP = ti.f_num
        WHERE b.a_num = %s
        ORDER BY b.ref_num DESC
        """
        cursor.execute(query_bookings, (user_id,))
        bookings = cursor.fetchall()

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    return render_template(
        'my_account.html',
        user_name=user_name,
        user_first_name=user_first_name,
        user_last_name=user_last_name,
        user_email=user_email,
        recovery_pin=recovery_pin,
        bookings=bookings
    )


# setting up the update account fields, then using that to "fill" current user data, if they change data it then will update the database

@app.route('/update_account', methods=['GET', 'POST'])
def update_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    f_name = request.form['f_name']
    l_name = request.form['l_name']
    email = request.form['email']
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        query_update = """
        UPDATE Users
        SET f_name = %s, l_name = %s, email = %s
        WHERE a_num = %s
        """
        cursor.execute(query_update, (f_name, l_name, email, user_id))
        db.commit()
        session['user_name'] = f"{f_name} {l_name}"
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('account'))


# Setting up the update password function, taking data from the form, using bcrypt to check the password they entered and if it matches changing it to the new one

@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        query_fetch = "SELECT pass FROM Users WHERE a_num = %s"
        cursor.execute(query_fetch, (user_id,))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user['pass'], current_password):
            if new_password == confirm_password:
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                query_update = "UPDATE Users SET pass = %s WHERE a_num = %s"
                cursor.execute(query_update, (hashed_password, user_id))
                db.commit()
    finally:
        cursor.close()
        db.close()
    return redirect(url_for('account'))


#setting up the check timings page to get the data from the form and then query the database to get the flight timings

@app.route('/check_timings', methods=['POST' , 'GET'])
def check_timings():
    user_name = session.get('user_name')
    try:
        from_location = request.form['from']
        to_location = request.form['destination']
        travel_date = request.form['travelDate']
        travel_class = request.form['class']
        passengers = int(request.form['passengers'])

        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)

        # Get available flights
        dep_query = """
        SELECT Flights.f_num, Flights.departure, Flights.arrival,
        Flight_Schedules.departure_time, Flight_Schedules.arrival_time
        FROM Flights
        JOIN Flight_Schedules ON Flights.f_num = Flight_Schedules.f_num
        WHERE Flights.departure = %s AND Flights.arrival = %s
        """
        cursor.execute(dep_query, (from_location, to_location))
        departure_flights = cursor.fetchall()

        # Check availability for each flight
        for flight in departure_flights:
            flight_number = flight['f_num']

            # Get current passenger count from PAX table
            pax_query = """
            SELECT total_passengers FROM PAX WHERE f_num = %s AND travel_date = %s
            """
            cursor.execute(pax_query, (flight_number, travel_date))
            pax_result = cursor.fetchone()

            # If no record exists, assume 0 passengers booked
            booked_passengers = pax_result['total_passengers'] if pax_result else 0

            # Store the availability check in the flight data
            flight['available_seats'] = 130 - booked_passengers

        # Close DB connection
        cursor.close()
        db.close()

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return redirect(url_for('index'))

    return render_template(
        'flight_timings.html',
        departure_flights=departure_flights,
        travel_date=travel_date,
        travel_class=travel_class,
        passengers=passengers,
        user_name=user_name
    )


    # setting up the confirm booking page, getting the data from the form and then calculating the total price of the booking

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    selected_flight = request.form['selected_flight']
    travel_date_str = request.form['travel_date']
    travel_class = request.form['travel_class']
    passengers = int(request.form['passengers'])
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        query_price = "SELECT price FROM Ticket_Info WHERE f_num = %s"
        cursor.execute(query_price, (selected_flight,))
        departure_price_row = cursor.fetchone()
        if not departure_price_row:
            return redirect(url_for('index'))
        price_per_ticket = float(departure_price_row['price'])
        multiplier = 2 if travel_class == 'Business Class' else 1.0
        total_price = price_per_ticket * multiplier * passengers

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    # Redirect to payment page with flight details and total price
    return redirect(
        url_for(
            'payment',
            flight_number=selected_flight,
            travel_date=travel_date_str,
            travel_class=travel_class,
            passengers=passengers,
            total_price=total_price
        )
    )


# setting up the booking summary page, getting the data from the form and then calculating the total price of the booking after payment is made

@app.route('/booking_summary', methods=['GET', 'POST'])
def booking_summary():
    selected_flight = request.form['selected_flight']
    travel_class = request.form['travel_class']
    passengers = int(request.form['passengers'])
    return_date = request.form.get('return_date')
    travel_date = request.form['travel_date']

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        query_flight = """
        SELECT f.*, fs.departure_time, fs.arrival_time, ti.standard_tickets, ti.business_tickets, ti.price
        FROM Flights f 
        JOIN Flight_Schedules fs ON f.f_num = fs.f_num
        JOIN Ticket_Info ti ON f.f_num = ti.f_num
        WHERE f.f_num = %s
        """
        cursor.execute(query_flight, (selected_flight,))
        flight_details = cursor.fetchone()
        return_flight_details = None
        if return_date:
            selected_return = request.form.get('selected_return')
            cursor.execute(query_flight, (selected_return,))
            return_flight_details = cursor.fetchone()
        price_per_ticket = float(flight_details['price']) * (2 if travel_class == 'Business Class' else 1.0)
        total_price = price_per_ticket * passengers
        if return_flight_details:
            return_price_per_ticket = float(return_flight_details['price']) * (2 if travel_class == 'Business Class' else 1.0)
            total_price += return_price_per_ticket * passengers
        travel_date_obj = datetime.strptime(travel_date, '%Y-%m-%d').date()
        booking_date = datetime.today().date()
        days_in_advance = (travel_date_obj - booking_date).days
        if 80 <= days_in_advance <= 90:
            discount_percentage = 25
        elif 60 <= days_in_advance <= 79:
            discount_percentage = 15
        elif 45 <= days_in_advance <= 59:
            discount_percentage = 10
        else:
            discount_percentage = 0

        discount_amount = (total_price * discount_percentage) / 100
        total_price_after_discount = total_price - discount_amount

    except mysql.connector.Error as err:
        print("Database Error:", err)
        return redirect(url_for('index'))

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    return render_template(
        'booking_summary.html',
        flight_details=flight_details,
        return_flight_details=return_flight_details,
        travel_class=travel_class,
        passengers=passengers,
        total_price=total_price_after_discount,
        discount_percentage=discount_percentage,
        discount_amount=discount_amount,
        travel_date=travel_date,
        return_date=return_date,
        user_name=session.get('user_name')
    )

# setting up the booking complete page, getting the data from the form and then calculating the total price of the booking after payment is made

@app.route('/booking_complete/<int:booking_ref>')
def booking_complete(booking_ref):
    db = None
    cursor = None
    boarding_group = None  # Default value

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)

        # Fetch the boarding group from the Bookings table
        cursor.execute("SELECT boarding_group FROM Bookings WHERE ref_num = %s", (booking_ref,))
        booking_data = cursor.fetchone()

        if booking_data:
            boarding_group = booking_data['boarding_group']
        else:
            boarding_group = "Unknown"

    except Exception as e:
        print(f"Error fetching boarding group: {e}")
        boarding_group = "Error"

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    return render_template(
        'booking_complete.html',
        booking_ref=booking_ref,
        user_name=session.get('user_name'),
        boarding_group=boarding_group
    )

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    ref_num = request.form['ref_num']

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        # Get flight details and passenger count
        query_get_booking = """
        SELECT Fl_num_DEP, departure_date, PAX 
        FROM Bookings WHERE ref_num = %s AND a_num = %s
        """
        cursor.execute(query_get_booking, (ref_num, session['user_id']))
        booking = cursor.fetchone()

        if not booking:
            print("Booking not found in database")
            return redirect(url_for('account')) 

        flight_number, travel_date, pax_count = booking
        print(f"Cancelling booking for flight {flight_number} on {travel_date} with {pax_count} passengers.")

        # Reduce passenger count in PAX table
        query_update_pax = """
        UPDATE PAX 
        SET total_passengers = total_passengers - %s 
        WHERE f_num = %s AND travel_date = %s
        """
        cursor.execute(query_update_pax, (pax_count, flight_number, travel_date))
        # Check the new PAX count
        query_check_pax = """
        SELECT total_passengers FROM PAX WHERE f_num = %s AND travel_date = %s
        """
        cursor.execute(query_check_pax, (flight_number, travel_date))
        pax_result = cursor.fetchone()

        if pax_result:
            print(f"Current PAX count after update: {pax_result[0]}")
        else:
            print(" No entry found in PAX after update")

        # If total passengers are now 0, delete the entry from PAX
        if pax_result and pax_result[0] <= 0:
            query_cleanup_pax = """
            DELETE FROM PAX WHERE f_num = %s AND travel_date = %s
            """
            cursor.execute(query_cleanup_pax, (flight_number, travel_date))
        # Mark payment as refunded
        query_update_payments = "UPDATE Payments SET refunded = 1 WHERE ref_num = %s"
        cursor.execute(query_update_payments, (ref_num,))
        # Delete from Booking_Details
        query_delete_details = "DELETE FROM Booking_Details WHERE ref_num = %s"
        cursor.execute(query_delete_details, (ref_num,))
        # Delete from Bookings
        query_delete_booking = "DELETE FROM Bookings WHERE ref_num = %s AND a_num = %s"
        cursor.execute(query_delete_booking, (ref_num, session['user_id']))
        print(f" Deleted booking {ref_num}.")

        db.commit()
   

    finally:
        cursor.close()
        db.close()

    return redirect(url_for('account'))


# setting up the booking details page, this displays all the information on the booking and allows the user to change the date of travel or cancel the booking

@app.route('/booking_details/<int:booking_ref>')
def booking_details(booking_ref):
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        
        query = """
        SELECT 
            b.ref_num AS booking_ref,
            b.Fl_num_DEP AS flight_number,
            f_departure.departure AS departure_airport,
            f_departure.arrival AS arrival_airport,
            b.departure_date AS departure_date,
            TIME(fs_departure.departure_time) AS departure_time,
            TIME(fs_departure.arrival_time) AS arrival_time,
            bd.B_Class AS business_class,
            bd.Econ AS economy_class,
            b.PAX AS passengers,
            ti.price * b.PAX * (CASE WHEN bd.B_Class > 0 THEN 2 ELSE 1.0 END) AS total_price,
            b.Payment_ID,
            b.boarding_group  -- Fetching boarding group from the Bookings table
        FROM 
            Bookings b
        LEFT JOIN Flight_Schedules fs_departure ON b.Fl_num_DEP = fs_departure.f_num
        LEFT JOIN Flights f_departure ON fs_departure.f_num = f_departure.f_num
        LEFT JOIN Booking_Details bd ON b.ref_num = bd.ref_num
        LEFT JOIN Ticket_Info ti ON b.Fl_num_DEP = ti.f_num
        WHERE 
            b.ref_num = %s
        """
        cursor.execute(query, (booking_ref,))
        booking = cursor.fetchone()
        
        if not booking:
            return redirect(url_for('account'))

        if booking['departure_date']:
            departure_date = booking['departure_date'].strftime('%Y-%m-%d')
            booking_date = datetime.today().strftime('%Y-%m-%d')
            days_in_advance = (datetime.strptime(departure_date, '%Y-%m-%d') - datetime.strptime(booking_date, '%Y-%m-%d')).days
            
            if 80 <= days_in_advance <= 90:
                discount_percentage = 25
            elif 60 <= days_in_advance <= 79:
                discount_percentage = 15
            elif 45 <= days_in_advance <= 59:
                discount_percentage = 10
            else:
                discount_percentage = 0

            discount_amount = (booking['total_price'] * discount_percentage) / 100
            final_price = booking['total_price'] - discount_amount
        else:
            days_in_advance = None
            discount_percentage = 0
            discount_amount = 0
            final_price = booking['total_price']

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    return render_template(
        'booking_details.html',
        booking=booking,
        days_in_advance=days_in_advance,
        discount_percentage=discount_percentage,
        discount_amount=discount_amount,
        final_price=final_price,
        user_name=session.get('user_name'),
        boarding_group=booking['boarding_group'] if booking.get('boarding_group') else 'Not Assigned'
    )

# setting up the about page, not much goes on here just gets the user name for the nav bar

@app.route('/about')
def about():
    return render_template('about.html', user_name=session.get('user_name'))


# sets up the main admin page, and if the admin is not logged in it will redirect to the admin login page

@app.route('/admin')
def admin_panel():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin.html')


# Sets up the admin login page, checks credentials against the admin details stored in the database

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    login_error = False  
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor(dictionary=True)
            query = "SELECT * FROM Admins WHERE username = %s"
            cursor.execute(query, (username,))
            admin = cursor.fetchone()
            if admin and bcrypt.check_password_hash(admin['password'], password):
                session['admin_logged_in'] = True
                session['admin_id'] = admin['id']
                return redirect(url_for('admin_panel'))
            else:
                login_error = True  
        finally:
            cursor.close()
            db.close()

    return render_template('admin_login.html', login_error=login_error)

# configures logging out, redirects to login and clears session 

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# sets up the manage users page, if the admin is not logged in it will redirect to the admin login page

@app.route('/admin/users', methods=['GET', 'POST'])
def manage_users():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            if action == 'update_password':
                new_password = request.form.get('new_password')
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                query_update_password = "UPDATE Users SET pass = %s WHERE a_num = %s"
                cursor.execute(query_update_password, (hashed_password, user_id))
                db.commit()
            elif action == 'update_details':
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                email = request.form.get('email')
                query_update_details = """
                UPDATE Users
                SET f_name = %s, l_name = %s, email = %s
                WHERE a_num = %s
                """
                cursor.execute(query_update_details, (first_name, last_name, email, user_id))
                db.commit()
            elif action == 'delete_user':
                query_delete_user = "DELETE FROM Users WHERE a_num = %s"
                cursor.execute(query_delete_user, (user_id,))
                db.commit()
        finally:
            cursor.close()
            db.close()
    users = []
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        query = "SELECT a_num AS id, f_name, l_name, email FROM Users"
        cursor.execute(query)
        users = cursor.fetchall()
    finally:
        cursor.close()
        db.close()

    return render_template('manage_users.html', users=users)


# sets up the manage bookings page and gets all the booking info from the database and allows the admin to search for individual bookings to ammend or cancel them, if the admin is not logged in it will redirect to the admin login page

@app.route('/admin/bookings', methods=['GET', 'POST'])
def check_booking():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    booking = None
    search_criteria = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'search_booking':
            search_type = request.form.get('search_type')
            search_value = request.form.get('search_value')

            try:
                db = mysql.connector.connect(**db_config)
                cursor = db.cursor(dictionary=True)
                
                query = """
                SELECT 
                    b.ref_num AS booking_ref,
                    b.Fl_num_DEP AS flight_number,
                    f.departure AS departure_airport,
                    f.arrival AS arrival_airport,
                    DATE(b.departure_date) AS departure_date,
                    TIME(fs.departure_time) AS departure_time,
                    b.PAX AS passengers,
                    bd.B_Class AS business_class,
                    bd.Econ AS economy_class,
                    ti.price * b.PAX * (CASE WHEN bd.B_Class > 0 THEN 2 ELSE 1.0 END) AS total_price
                FROM 
                    Bookings b
                LEFT JOIN Flight_Schedules fs ON b.Fl_num_DEP = fs.f_num
                LEFT JOIN Flights f ON fs.f_num = f.f_num
                LEFT JOIN Booking_Details bd ON b.ref_num = bd.ref_num
                LEFT JOIN Ticket_Info ti ON b.Fl_num_DEP = ti.f_num
                WHERE 
                    b.ref_num = %s
                """ if search_type == 'ref_num' else """
                SELECT 
                    b.ref_num AS booking_ref,
                    b.Fl_num_DEP AS flight_number,
                    f.departure AS departure_airport,
                    f.arrival AS arrival_airport,
                    DATE(b.departure_date) AS departure_date,
                    TIME(fs.departure_time) AS departure_time,
                    b.PAX AS passengers,
                    bd.B_Class AS business_class,
                    bd.Econ AS economy_class,
                    ti.price * b.PAX * (CASE WHEN bd.B_Class > 0 THEN 2 ELSE 1.0 END) AS total_price
                FROM 
                    Bookings b
                LEFT JOIN Flight_Schedules fs ON b.Fl_num_DEP = fs.f_num
                LEFT JOIN Flights f ON fs.f_num = f.f_num
                LEFT JOIN Booking_Details bd ON b.ref_num = bd.ref_num
                LEFT JOIN Ticket_Info ti ON b.Fl_num_DEP = ti.f_num
                WHERE 
                    b.a_num = %s
                """
                
                cursor.execute(query, (search_value,))
                booking = cursor.fetchall()

            finally:
                cursor.close()
                db.close()
            
            search_criteria = search_value

        elif action == 'cancel_booking':
            booking_ref = request.form.get('booking_ref')

            try:
                db = mysql.connector.connect(**db_config)
                cursor = db.cursor()

                query_get_booking = """
                SELECT Fl_num_DEP, departure_date, PAX 
                FROM Bookings WHERE ref_num = %s
                """
                cursor.execute(query_get_booking, (booking_ref,))
                booking = cursor.fetchone()

                if not booking:
                    return redirect(url_for('check_booking'))

                flight_number, travel_date, pax_count = booking
                print(f"Admin cancelling booking for flight {flight_number} on {travel_date} with {pax_count} passengers.")

                query_update_pax = """
                UPDATE PAX 
                SET total_passengers = total_passengers - %s 
                WHERE f_num = %s AND travel_date = %s
                """
                cursor.execute(query_update_pax, (pax_count, flight_number, travel_date))

                query_check_pax = """
                SELECT total_passengers FROM PAX WHERE f_num = %s AND travel_date = %s
                """
                cursor.execute(query_check_pax, (flight_number, travel_date))
                pax_result = cursor.fetchone()

                if pax_result:
                    print(f"Current PAX count after update: {pax_result[0]}")
                else:
                    print("No entry found in PAX after update")

                if pax_result and pax_result[0] <= 0:
                    query_cleanup_pax = """
                    DELETE FROM PAX WHERE f_num = %s AND travel_date = %s
                    """
                    cursor.execute(query_cleanup_pax, (flight_number, travel_date))
                    print(f"Deleted PAX entry for flight {flight_number} on {travel_date}.")

                query_update_payments = "UPDATE Payments SET refunded = 1 WHERE ref_num = %s"
                cursor.execute(query_update_payments, (booking_ref,))

                query_delete_details = "DELETE FROM Booking_Details WHERE ref_num = %s"
                cursor.execute(query_delete_details, (booking_ref,))

                query_delete_booking = "DELETE FROM Bookings WHERE ref_num = %s"
                cursor.execute(query_delete_booking, (booking_ref,))
                print(f"Deleted booking {booking_ref}.")

                db.commit()

            finally:
                cursor.close()
                db.close()

    return render_template('check_booking.html', booking=booking, search_criteria=search_criteria)

# sets up the manage flights page, where all flight data can be updated, if the admin is not logged in it will redirect to the admin login page

@app.route('/admin/journeys', methods=['GET', 'POST'])
def manage_journeys():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    journeys = []
    if request.method == 'POST':
        flight_number = request.form.get('flight_number')
        departure_time = request.form.get('departure_time')
        arrival_time = request.form.get('arrival_time')
        price = request.form.get('price')
        try:
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()
            query_update = """
            UPDATE Flight_Schedules
            SET departure_time = %s, arrival_time = %s
            WHERE f_num = %s
            """
            cursor.execute(query_update, (departure_time, arrival_time, flight_number))
            query_update_price = """
            UPDATE Ticket_Info
            SET price = %s
            WHERE f_num = %s
            """
            cursor.execute(query_update_price, (price, flight_number))
            db.commit()
        finally:
            cursor.close()
            db.close()
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        query = """
        SELECT 
            fs.f_num AS flight_number,
            f.departure,
            f.arrival,
            fs.departure_time,
            fs.arrival_time,
            ti.price
        FROM Flight_Schedules fs
        JOIN Flights f ON fs.f_num = f.f_num
        JOIN Ticket_Info ti ON fs.f_num = ti.f_num
        """
        cursor.execute(query)
        journeys = cursor.fetchall()
    finally:
        cursor.close()
        db.close()

    return render_template('manage_journeys.html', journeys=journeys)


# sets up the change admin password page

@app.route('/admin/change_password', methods=['GET', 'POST'])
def change_admin_password():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if current_password and new_password and confirm_password:
            try:
                db = mysql.connector.connect(**db_config)
                cursor = db.cursor(dictionary=True)
                query_fetch = "SELECT password FROM Admins WHERE username = 'admin'"
                cursor.execute(query_fetch)
                admin = cursor.fetchone()
                if admin and bcrypt.check_password_hash(admin['password'], current_password):
                    if new_password == confirm_password:
                        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                        query_update = "UPDATE Admins SET password = %s WHERE username = 'admin'"
                        cursor.execute(query_update, (hashed_password,))
                        db.commit()
            finally:
                cursor.close()
                db.close()

    return render_template('change_admin_password.html')


# sets up the statistics page and gathers the information from the database to display

@app.route('/admin/statistics')
def admin_statistics():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    statistics = {
        "monthly_sales": [],
        "sales_per_journey": [],
        "top_customers": [],
        "most_sold_route": None,
    }

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        query_monthly_sales = """
        SELECT 
            DATE_FORMAT(b.departure_date, '%Y-%m') AS month,
            SUM(b.PAX * ti.price * (CASE WHEN bd.B_Class > 0 THEN 2 ELSE 1.0 END)) AS total_sales
        FROM Bookings b
        JOIN Ticket_Info ti ON b.Fl_num_DEP = ti.f_num
        LEFT JOIN Booking_Details bd ON b.ref_num = bd.ref_num
        GROUP BY DATE_FORMAT(b.departure_date, '%Y-%m')
        ORDER BY month DESC
        """
        cursor.execute(query_monthly_sales)
        statistics["monthly_sales"] = cursor.fetchall()

        query_sales_per_journey = """
        SELECT 
            CONCAT(f.departure, ' - ', f.arrival) AS route,
            SUM(b.PAX * ti.price * (CASE WHEN bd.B_Class > 0 THEN 2 ELSE 1.0 END)) AS total_sales
        FROM Bookings b
        JOIN Flights f ON b.Fl_num_DEP = f.f_num
        JOIN Ticket_Info ti ON b.Fl_num_DEP = ti.f_num
        LEFT JOIN Booking_Details bd ON b.ref_num = bd.ref_num
        GROUP BY f.departure, f.arrival
        ORDER BY total_sales DESC
        """
        cursor.execute(query_sales_per_journey)
        statistics["sales_per_journey"] = cursor.fetchall()

        query_top_customers = """
        SELECT 
            CONCAT(u.f_name, ' ', u.l_name) AS customer,
            SUM(b.PAX * ti.price * (CASE WHEN bd.B_Class > 0 THEN 2 ELSE 1.0 END)) AS total_spent,
            COUNT(b.ref_num) AS total_bookings
        FROM Bookings b
        JOIN Users u ON b.a_num = u.a_num
        JOIN Ticket_Info ti ON b.Fl_num_DEP = ti.f_num
        LEFT JOIN Booking_Details bd ON b.ref_num = bd.ref_num
        GROUP BY b.a_num
        ORDER BY total_spent DESC
        LIMIT 10
        """
        cursor.execute(query_top_customers)
        statistics["top_customers"] = cursor.fetchall()

        query_most_sold_route = """
        SELECT 
            CONCAT(f.departure, ' - ', f.arrival) AS route,
            COUNT(*) AS total_bookings
        FROM Bookings b
        JOIN Flights f ON b.Fl_num_DEP = f.f_num
        GROUP BY f.departure, f.arrival
        ORDER BY total_bookings DESC
        LIMIT 1
        """
        cursor.execute(query_most_sold_route)
        most_sold_route = cursor.fetchone()
        if most_sold_route:
            statistics["most_sold_route"] = most_sold_route["route"]

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    return render_template('admin_statistics.html', statistics=statistics)


# sets up the method in which the user can change their booking date

@app.route('/change_booking_date', methods=['GET', 'POST'])
def change_booking_date():
    ref_num = request.form.get('ref_num')
    new_date = request.form.get('new_date')
    
    if not ref_num or not new_date:
        return redirect(url_for('account'))  
    
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        query_update_date = """
        UPDATE Bookings 
        SET departure_date = %s 
        WHERE ref_num = %s
        """
        cursor.execute(query_update_date, (new_date, ref_num))
        db.commit()
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
    
    return redirect(url_for('booking_details', booking_ref=ref_num ))


# sets up the payment page, gathers all info from the forms filled in and the user name

@app.route('/payment')
def payment():
    flight_number = request.args.get('flight_number')
    travel_date_str = request.args.get('travel_date')
    travel_class = request.args.get('travel_class')
    passengers = request.args.get('passengers', type=int)
    total_price = request.args.get('total_price', type=float)
    user_name = session.get('user_name')

    if not all([flight_number, travel_date_str, travel_class, passengers, total_price]):
        return "Incomplete booking details provided.", 400
    travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
    booking_date = datetime.today().date()
    days_in_advance = (travel_date - booking_date).days
    if 80 <= days_in_advance <= 90:
        discount_percentage = 25
    elif 60 <= days_in_advance <= 79:
        discount_percentage = 15
    elif 45 <= days_in_advance <= 59:
        discount_percentage = 10
    else:
        discount_percentage = 0
    discount_amount = (total_price * discount_percentage) / 100
    total_price_after_discount = total_price - discount_amount

    return render_template(
        'payment_form.html',
        flight_number=flight_number,
        travel_date=travel_date_str,
        travel_class=travel_class,
        passengers=passengers,
        total_price=total_price_after_discount,
        discount_percentage=discount_percentage,
        discount_amount=discount_amount,
        user_name=user_name
    )


# sets up the "payment processing", in this case just submits to the database as i am not actually processing payemnts, validates inputs and then "commits" or adds the data to the database, if this was done on a live site it would violate GDPR and PCI compliance, so this is just a demonstration, in a live version only payment ID and booking id would be stored in the database

@app.route('/process_payment', methods=['POST'])
def process_payment():
    flight_number = request.form['flight_number']
    travel_date = request.form['travel_date']
    passengers = int(request.form['passengers'])
    total_price = float(request.form['total_price'])
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    db = None
    cursor = None

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)

        # Insert payment details into Payments table
        query_insert_payment = """
        INSERT INTO Payments (card_name, card_number, expiry_date, cvv, amount)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query_insert_payment, (request.form['cardName'], request.form['cardNumber'],
                                              request.form['expiryDate'], request.form['cvv'], total_price))
        db.commit()
        payment_id = cursor.lastrowid  

        # Insert the booking (WITHOUT boarding group)
        query_booking = """
        INSERT INTO Bookings (a_num, Fl_num_DEP, PAX, Payment_ID, departure_date)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query_booking, (user_id, flight_number, passengers, payment_id, travel_date))
        db.commit()
        booking_ref = cursor.lastrowid  

        # Insert Booking Class Details
        query_insert_booking_details = """
        INSERT INTO Booking_details (ref_num, B_Class, Econ)
        VALUES (%s, %s, %s)
        """
        travel_class = request.form['travel_class'].strip().lower()
        if "business" in travel_class:
            cursor.execute(query_insert_booking_details, (booking_ref, 1, 0))  # Business Class
        else:
            cursor.execute(query_insert_booking_details, (booking_ref, 0, 1))  # Economy Class
        db.commit()

        # Fetch booking class from Booking_details table
        cursor.execute(
            "SELECT B_Class, Econ FROM Booking_details WHERE ref_num = %s",
            (booking_ref,)
        )
        booking_data = cursor.fetchone()
        if not booking_data:
            return f"ERROR: No existing booking found for this user and flight. Ref: {booking_ref}", 400
        b_class = booking_data['B_Class']
        econ = booking_data['Econ']

        # Determine Boarding Group
        if b_class > 0:  # Passenger is in Business Class
            boarding_group = "Priority"
        elif econ > 0:  # Passenger is in Economy Class
            boarding_group = str(random.randint(1, 5))  # Randomly assign between 1 and 5
        else:
            return "Invalid class data in database.", 500  # Failsafe

        # Update the booking with the boarding group
        query_update_boarding = """
        UPDATE Bookings SET boarding_group = %s WHERE ref_num = %s
        """
        cursor.execute(query_update_boarding, (boarding_group, booking_ref))
        db.commit()

        # Update the payment reference number
        query_update_payment = "UPDATE Payments SET ref_num = %s WHERE payment_id = %s"
        cursor.execute(query_update_payment, (booking_ref, payment_id))
        db.commit()

        query_check_pax = "SELECT total_passengers FROM PAX WHERE f_num = %s AND travel_date = %s"
        cursor.execute(query_check_pax, (flight_number, travel_date))
        pax_result = cursor.fetchone()

        if pax_result:
            # If a record exists, update the passenger count
            query_update_pax = """
            UPDATE PAX SET total_passengers = total_passengers + %s
            WHERE f_num = %s AND travel_date = %s
            """
            cursor.execute(query_update_pax, (passengers, flight_number, travel_date))
        else:
            # If no record exists, insert a new one
            query_insert_pax = """
            INSERT INTO PAX (f_num, travel_date, total_passengers)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query_insert_pax, (flight_number, travel_date, passengers))

        db.commit()  # Final commit to save all changes

    except Exception as e:
        print(f"Error processing payment: {e}")
        return redirect(url_for('bad_request_error'))

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    return redirect(url_for('booking_complete', booking_ref=booking_ref))

# sets up the admins payment page, in which they can search for user payments and if needed refund them

@app.route('/admin/payments', methods=['GET', 'POST'])
def manage_payments():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    payments = None
    search_criteria = None
    refund_success = False
    error_message = None

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'search_payment':
                search_type = request.form.get('search_type')
                search_value = request.form.get('search_value')

                if search_type and search_value:
                    if search_type == 'ref_num':
                        query = """
                        SELECT 
                            p.payment_id, 
                            p.ref_num, 
                            b.a_num AS account_number,
                            p.card_name, 
                            p.amount, 
                            DATE(p.created_at) AS payment_date,
                            p.refunded
                        FROM Payments p
                        LEFT JOIN Bookings b ON p.ref_num = b.ref_num
                        WHERE p.ref_num = %s
                        """
                        cursor.execute(query, (search_value,))
                    elif search_type == 'a_num':
                        query = """
                        SELECT 
                            p.payment_id, 
                            p.ref_num, 
                            b.a_num AS account_number,
                            p.card_name, 
                            p.amount, 
                            DATE(p.created_at) AS payment_date,
                            p.refunded
                        FROM Payments p
                        LEFT JOIN Bookings b ON p.ref_num = b.ref_num
                        WHERE b.a_num = %s
                        """
                        cursor.execute(query, (search_value,))
                    payments = cursor.fetchall()
                    search_criteria = search_value
                else:
                    error_message = "Please provide valid search criteria."

            elif action == 'refund_payment':
                payment_id = request.form.get('payment_id')
                query_check_payment = """
                SELECT refunded FROM Payments WHERE payment_id = %s
                """
                cursor.execute(query_check_payment, (payment_id,))
                payment = cursor.fetchone()

                if not payment:
                    error_message = "Payment not found."
                elif payment['refunded']:
                    error_message = "Payment has already been refunded."
                else:
                    query_refund_payment = """
                    UPDATE Payments
                    SET refunded = TRUE
                    WHERE payment_id = %s
                    """
                    cursor.execute(query_refund_payment, (payment_id,))
                    db.commit()
                    refund_success = True

    except mysql.connector.Error as err:
        error_message = f"An error occurred: {err}"

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    return render_template(
        'manage_payments.html',
        payments=payments,
        search_criteria=search_criteria,
        refund_success=refund_success,
        error_message=error_message
    )


#allows the admin to update departure date

@app.route('/admin/update_date', methods=['POST'])
def update_booking_date():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    ref_num = request.form.get('ref_num')
    new_date = request.form.get('new_date')

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        
        query = "UPDATE Bookings SET departure_date = %s WHERE ref_num = %s"
        cursor.execute(query, (new_date, ref_num))
        db.commit()

        if cursor.rowcount == 0:  
            return redirect(url_for('check_booking', update_success=False, ref_num=ref_num))
        
        return redirect(url_for('check_booking', update_success=True, ref_num=ref_num))
    except Exception as e:
        return redirect(url_for('check_booking', update_success=False, ref_num=ref_num))
    finally:
        cursor.close()
        db.close()


# Error Handling

@app.errorhandler(404) # sets up the 404 page, if the user tries to access a page that does not exist
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(e):
    return render_template('403.html'), 403

@app.route('/lock') # means i can set url to /lock to demo the 403 page
def restricted_page():
    return render_template('403.html'), 403

@app.errorhandler(400)
def bad_request_error(e):
    return render_template('400.html'), 400

@app.route('/err') # means i can set url to /err to demo the 400 page
def simulate_bad_request():
    abort(400)

@app.route('/405', methods=['POST'])  # Only allows POST requests so entering its url will trigger the error for demo purposes
def trigger_405():
    return "This is to test GET error handling", 405
    
@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("405.html"), 405

@app.errorhandler(503)
def bad_request_error(e):
    return render_template('503.html'), 503

@app.route('/503') # means i can set url to /err to demo the 400 page
def simulate_downtime():
    abort(503)


# makes sure that the favicon ( the little icon in the tab) is displayed
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/apple-touch-icon-precomposed.png')
def apple_touch_icon_precomposed():
    return send_from_directory('static', 'apple-touch-icon-precomposed.png', mimetype='image/png')

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    return send_from_directory('static', 'apple-touch-icon.png', mimetype='image/png')

# lets the user reset their password using the pin generated on sign up

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form['email']
    recovery_pin = request.form['recovery_pin']
    new_password = request.form['new_password']
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

    password_reset_success = False
    password_reset_error = False

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)

        # Check if the email and recovery PIN match
        query = "SELECT * FROM Users WHERE email = %s AND forgot_password_pin = %s"
        cursor.execute(query, (email, recovery_pin))
        user = cursor.fetchone()

        if user:
            # Update the user's password
            update_query = "UPDATE Users SET pass = %s WHERE email = %s"
            cursor.execute(update_query, (hashed_password, email))
            db.commit()
            password_reset_success = True
        else:
            password_reset_error = True

    except Exception as e:
        print(f"Error: {e}")
        password_reset_error = True
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    return render_template(
        'login.html',
        password_reset_success=password_reset_success,
        password_reset_error=password_reset_error
    )

# app route for the seating plan page 

@app.route('/seating')
def seating():
    user_name = session.get('user_name')  
    return render_template('seating.html', user_name=user_name)

# app route for boarding pass generation 

@app.route('/download_boarding_pass/<int:booking_ref>')
def download_boarding_pass(booking_ref):
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor(dictionary=True)
        query = """
        SELECT 
            b.ref_num AS booking_ref,
            b.Fl_num_DEP AS flight_number,
            f_departure.departure AS departure_airport,
            f_departure.arrival AS arrival_airport,
            b.departure_date AS departure_date,
            TIME(fs_departure.departure_time) AS departure_time,
            TIME(fs_departure.arrival_time) AS arrival_time,
            CONCAT(u.f_name, ' ', u.l_name) AS passenger_name,
            b.PAX AS passengers,
            b.boarding_group
        FROM 
            Bookings b
        LEFT JOIN Users u ON b.a_num = u.a_num
        LEFT JOIN Flight_Schedules fs_departure ON b.Fl_num_DEP = fs_departure.f_num
        LEFT JOIN Flights f_departure ON fs_departure.f_num = f_departure.f_num
        WHERE 
            b.ref_num = %s
        """
        cursor.execute(query, (booking_ref,))
        booking = cursor.fetchone()

        if not booking:
            return "Booking not found", 404
        
        boarding_pass_folder = os.path.join(os.getcwd(), "website/static/BoardingPass")
        if not os.path.exists(boarding_pass_folder):
            os.makedirs(boarding_pass_folder)

        pdf_filename = f"boarding_pass_{booking_ref}.pdf"
        pdf_path = os.path.join(boarding_pass_folder, pdf_filename)

        qr_filename = f"qr_{booking_ref}.png"
        qr_path = os.path.join(boarding_pass_folder, qr_filename)

        logo_path = os.path.join("website/static", "logo-print.png")  # Ensure this path is correct

        # Generate QR Code
        qr = qrcode.make(f"Booking Reference: {booking_ref}")
        qr.save(qr_path)

        # Create PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        page_width, page_height = letter  # Standard Letter size

        # Add Logo 
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            logo_width, logo_height = logo.getSize()
            aspect_ratio = logo_width / logo_height
            c.drawImage(logo, (page_width - 200) / 2, 730, width=200, height=200 / aspect_ratio, mask='auto')

        # Title
        c.setFont("Helvetica-Bold", 18)
        text = "Boarding Pass"
        text_width = c.stringWidth(text, "Helvetica-Bold", 18)
        c.drawString((page_width - text_width) / 2, 700, text)  # Centered title

        # Passenger Info
        c.setFont("Helvetica", 14)
        c.drawString(60, 650, f"Passenger: {booking['passenger_name']}")
        c.drawString(60, 630, f"Booking Ref: {booking['booking_ref']}")
        c.drawString(60, 610, f"Flight Number: {booking['flight_number']}")

        # Flight Details
        c.setFont("Helvetica", 12)
        c.drawString(60, 580, f"Departure: {booking['departure_airport']}")
        c.drawString(60, 560, f"Arrival: {booking['arrival_airport']}")
        c.drawString(60, 540, f"Departure Date: {booking['departure_date']}")
        c.drawString(60, 520, f"Departure Time: {booking['departure_time']}")
        c.drawString(60, 500, f"Arrival Time: {booking['arrival_time']}")

        # Boarding Group
        boarding_group = booking['boarding_group'] if booking['boarding_group'] else "Not Assigned"
        c.setFont("Helvetica-Bold", 14)
        c.drawString(60, 460, f"Boarding Group: {boarding_group}")

        # Add QR Code
        qr_img = ImageReader(qr_path)
        c.drawImage(qr_img, 400, 500, width=120, height=120)

        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(60, 380, "This is not valid proof of identity please bring a form of photo ID to the airport.")
        c.drawString(60, 420, "Please arrive at least 2 hours before departure.")
        c.drawString(60, 400, "Thank you for flying with Horizon Travels.")
        c.save()

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

    return send_file(pdf_path, as_attachment=True)

# runs the python file with GUI debugging 

if __name__ == '__main__':
    app.run(debug=True)