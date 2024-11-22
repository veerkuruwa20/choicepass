from flask import Flask, render_template, request, redirect, url_for, session
import random
import pickle
import csv
import datetime as dt

app = Flask(__name__)
app.secret_key = 'choicegatepass'

ADMINUSERNAME = "choice"
ADMINPASSWORD = "ss123"
today_date = dt.date.today()
creds = []
requests = []
final = []
all=[]

def refreshrec():
    global creds
    global final
    global requests
    global all
    all.clear()
    creds.clear()
    requests.clear()
    
    
    # Load credentials
    try:
        with open('creds.dat', 'rb') as f:
            while True:
                try:
                    rec = pickle.load(f)
                    creds.append(rec)
                except EOFError:
                    break
    except Exception as e:
        print(f"Error reading creds.dat: {e}")
    
    # Load today's requests from requests.csv
    try:
        with open('requests.csv', 'r') as fin:
            csv_file = csv.reader(fin)
            header = next(csv_file)  # Skip the header row
            for row in csv_file:
                if len(row) >= 9 and row[0] == str(today_date):  # Check if row has enough columns
                    requests.append(row)
    except Exception as e:
        print(f"Error reading requests.csv: {e}")
    
    # Load data.csv for approved/rejected requests, filter by teacher name
    
    
    try:
        with open('data.csv', 'r') as fout2:
            csv_out2 = csv.reader(fout2)
            header = next(csv_out2)  # Skip the header row
            for row in csv_out2:
                if len(row) >= 8 and row[0] == str(today_date): # Check if row has enough columns
                    all.append(row)
    except Exception as e:
        print(f"Error reading data.csv: {e}")

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    global role
    global name
    refreshrec()  # Ensure creds are loaded before checking login
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check for admin login
        if username == ADMINUSERNAME and password == ADMINPASSWORD:
            name = 'ADMIN'
            role = 'ADMIN'
            session['logged_in'] = True
            return redirect(url_for('admin'))
        elif username=='new' and password=='new':
            name = 'ADMIN'
            role = 'ADMIN'
            session['logged_in'] = True
            return redirect(url_for('new'))
        
        # Check for user login
        for i in creds:
            if username == i[0] and password == i[1]:
                name = i[2]
                role = i[3]
                session['logged_in'] = True
                if role == 'TEACHER':
                    return redirect(url_for('teacher'))
                elif role == 'VP/SC':
                    return redirect(url_for('vp'))
        
        # If no match is found
        session['logged_in'] = False

    return render_template('login.html')

@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Handle form submission and append data to requests.csv
    if request.method == 'POST':
        student_name = request.form.get('student_name')
        admission_number = request.form.get('admno')
        class_name = request.form.get('class')  # Get the class value from the form
        division = request.form.get('division')  # Get the division value from the form
        purpose = request.form.get('purpose')
        transport = request.form.get('transport')
        departure_time = request.form.get('departure_time') or 'ETD'  # Ensure 'ETD' is the default if empty
        teachername = name  # This is the teacher's name, ensure 'name' is defined properly

        # Append form data to requests.csv
        with open('requests.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([str(today_date), student_name, admission_number, class_name, division, purpose, transport, departure_time, teachername])

        # Call refreshrec() to refresh the data after appending to requests.csv
        refreshrec()
    try:
        global final
        final.clear()
        with open('data.csv', 'r') as fout:
            csv_out = csv.reader(fout)
            header = next(csv_out)  # Skip the header row
            for row in csv_out:
                if len(row) >= 8 and row[0] == str(today_date) and row[5] == name:  # Check if row has enough columns
                    final.append(row)
    except Exception as e:
        print(f"Error reading data.csv: {e}")
    # Pass the updated final_data to the template
    return render_template('teacher.html', final_data=final)


@app.route('/vp', methods=['GET', 'POST'])
def vp():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Initialize list for today's pending requests
    pending_requests = []

    # Convert today's date to string format (YYYY-MM-DD)
    today_date_str = today_date.strftime('%Y-%m-%d')

    # Read the requests.csv file
    try:
        with open('requests.csv', 'r', newline='', encoding='utf-8') as fin:
            csv_file = csv.reader(fin)
            header = next(csv_file)  # Skip the header
            for row in csv_file:
                # Skip empty rows or rows that don't have the expected number of columns
                if len(row) < 9 or not any(row):  # Expecting 9 columns now (Date, Name, Admission Number, Class, Division, Purpose, Transport, Time, Teacher)
                    continue

                # Ensure the date in requests.csv is in the same format as today's date
                if row[0] == today_date_str:  # Compare as strings
                    pending_requests.append(row)
    except FileNotFoundError:
        print('requests.csv not found')

    # Handle approve/reject actions
    if request.method == 'POST':
        if 'approve' in request.form:
            request_data = request.form['approve']
            request_info = request_data.split('|')

            # Make sure the request data is valid and has the expected number of fields
            if len(request_info) == 5:
                student_name = request_info[0]
                admission_number = request_info[1]
                purpose = request_info[2]
                mode_of_transport = request_info[3]
                teacher = request_info[4]
                
                # Generate random OTP
                otp = random.randint(1000, 9999)
                status = "approved"
                
                # Write to data.csv with approved status and OTP
                with open('data.csv', 'a', newline='', encoding='utf-8') as fout:
                    csv_writer = csv.writer(fout)
                    csv_writer.writerow([str(today_date), student_name, admission_number, purpose, mode_of_transport, teacher, status, otp])

                # Remove the approved request from requests.csv
                with open('requests.csv', 'r', newline='', encoding='utf-8') as fin:
                    requests = list(csv.reader(fin))

                # Filter out the request that has been approved
                updated_requests = [row for row in requests if not (len(row) >= 3 and row[0] == today_date_str and row[1] == student_name and row[2] == admission_number)]
                
                # Write back the remaining requests to requests.csv, but exclude the header
                with open('requests.csv', 'w', newline='', encoding='utf-8') as fout:
                    csv_writer = csv.writer(fout)
                    csv_writer.writerows(updated_requests)  # Do NOT write the header again

        elif 'reject' in request.form:
            request_data = request.form['reject']
            request_info = request_data.split('|')

            # Make sure the request data is valid and has the expected number of fields
            if len(request_info) == 5:
                student_name = request_info[0]
                admission_number = request_info[1]
                purpose = request_info[2]
                mode_of_transport = request_info[3]
                teacher = request_info[4]

                # Write to data.csv with rejected status and null OTP
                with open('data.csv', 'a', newline='', encoding='utf-8') as fout:
                    csv_writer = csv.writer(fout)
                    csv_writer.writerow([str(today_date), student_name, admission_number, purpose, mode_of_transport, teacher, 'rejected', None])

                # Remove the rejected request from requests.csv
                with open('requests.csv', 'r', newline='', encoding='utf-8') as fin:
                    requests = list(csv.reader(fin))

                # Filter out the request that has been rejected
                updated_requests = [row for row in requests if not (len(row) >= 3 and row[0] == today_date_str and row[1] == student_name and row[2] == admission_number)]
                
                # Write back the remaining requests to requests.csv, but exclude the header
                with open('requests.csv', 'w', newline='', encoding='utf-8') as fout:
                    csv_writer = csv.writer(fout)
                    csv_writer.writerows(updated_requests)  # Do NOT write the header again

        # Redirect back to the 'vp' route to refresh the page
        return redirect(url_for('vp'))

    return render_template('vp.html', pending_requests=pending_requests)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))


    return render_template('admin.html', final_data=all)



@app.route('/logout', methods=['POST'])
def logout():
    # Clear the session to log the user out
    session.clear()
    return redirect(url_for('login'))



@app.route('/new', methods=['GET', 'POST'])
def new():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        namet = request.form.get('namet')
        role=request.form.get('role')
    try:
        with open('creds.dat','ab') as fappend:
            l=[username,password,namet,role]
            pickle.dump(l,fappend)
    except Exception as e:
        print(f"Error reading creds.dat: {e}")


    return render_template('new.html', final_data=all)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

