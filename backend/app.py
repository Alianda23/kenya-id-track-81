from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Your MySQL username
    'password': '',  # Your MySQL password
    'database': 'digital_id_system'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Officer Authentication Routes
@app.route('/api/officer/signup', methods=['POST'])
def officer_signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['idNumber', 'email', 'phoneNumber', 'fullName', 'station', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if officer already exists
        cursor.execute("SELECT id FROM officers WHERE id_number = %s OR email = %s", 
                      (data['idNumber'], data['email']))
        if cursor.fetchone():
            return jsonify({'error': 'Officer with this ID number or email already exists'}), 400
        
        # Hash password
        hashed_password = generate_password_hash(data['password'])
        
        # Insert new officer (pending approval)
        cursor.execute("""
            INSERT INTO officers (id_number, email, phone_number, full_name, station, password_hash, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)
        """, (data['idNumber'], data['email'], data['phoneNumber'], 
              data['fullName'], data['station'], hashed_password, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Application submitted successfully. Awaiting admin approval.'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/officer/login', methods=['POST'])
def officer_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get officer details
        cursor.execute("""
            SELECT id, email, full_name, station, password_hash, status 
            FROM officers WHERE email = %s
        """, (email,))
        officer = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not officer:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if officer['status'] != 'approved':
            return jsonify({'error': 'Account not approved by admin'}), 403
        
        if not check_password_hash(officer['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'officer_id': officer['id'],
            'email': officer['email'],
            'role': 'officer',
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'officer': {
                'id': officer['id'],
                'email': officer['email'],
                'fullName': officer['full_name'],
                'station': officer['station']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Authentication
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get admin details
        cursor.execute("""
            SELECT id, username, full_name, password_hash 
            FROM admins WHERE username = %s
        """, (username,))
        admin = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not admin:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not check_password_hash(admin['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'admin_id': admin['id'],
            'username': admin['username'],
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'admin': {
                'id': admin['id'],
                'username': admin['username'],
                'fullName': admin['full_name']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin Routes
@app.route('/api/admin/officers/pending', methods=['GET'])
def get_pending_officers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, id_number, email, phone_number, full_name, station, created_at
            FROM officers WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
        officers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'officers': officers}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/officers/<int:officer_id>/approve', methods=['PUT'])
def approve_officer(officer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE officers SET status = 'approved' WHERE id = %s", (officer_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Officer approved successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/officers/<int:officer_id>/reject', methods=['PUT'])
def reject_officer(officer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE officers SET status = 'rejected' WHERE id = %s", (officer_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Officer rejected'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Application Routes
@app.route('/api/applications', methods=['POST'])
def submit_application():
    try:
        print("Received request:", request.method, request.content_type)
        
        # Check content type
        if request.content_type and 'application/json' in request.content_type:
            # Handle JSON data
            data = request.get_json()
            files = {}
            print("Processing JSON data:", list(data.keys()) if data else "No data")
        else:
            # Handle form data with files
            data = request.form.to_dict()
            files = request.files
            print("Processing form data:", list(data.keys()) if data else "No data")
        
        # Validate required fields
        required_fields = ['fullNames', 'dateOfBirth', 'gender', 'fatherName', 'motherName', 
                          'districtOfBirth', 'tribe', 'homeDistrict', 'division', 
                          'constituency', 'location', 'subLocation', 'villageEstate', 'occupation']
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            print("Missing required fields:", missing_fields)
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Get officer ID from token (you'd normally verify JWT here)
        officer_id = 1  # Temporary - should get from JWT token
        
        # Generate application number
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current count for application number
        cursor.execute("SELECT COUNT(*) FROM applications")
        count = cursor.fetchone()[0]
        application_number = f"APP{datetime.now().year}{count + 1:06d}"
        
        print(f"Generated application number: {application_number}")
        
        # Insert application
        cursor.execute("""
            INSERT INTO applications (
                application_number, officer_id, application_type,
                full_names, date_of_birth, gender, father_name, mother_name,
                marital_status, husband_name, husband_id_no,
                district_of_birth, tribe, clan, family, home_district,
                division, constituency, location, sub_location, village_estate,
                home_address, occupation, supporting_documents, status, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            application_number, officer_id, 'new',
            data['fullNames'], data['dateOfBirth'], data['gender'],
            data['fatherName'], data['motherName'], data.get('maritalStatus'),
            data.get('husbandName'), data.get('husbandIdNo'),
            data['districtOfBirth'], data['tribe'], data.get('clan'),
            data.get('family'), data['homeDistrict'], data['division'],
            data['constituency'], data['location'], data['subLocation'],
            data['villageEstate'], data.get('homeAddress'), data['occupation'],
            json.dumps(data.get('supportingDocuments', {})), 'submitted', datetime.now()
        ))
        
        application_id = cursor.lastrowid
        
        # Handle file uploads (only if files were sent)
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        for file_key, file in files.items():
            if file and file.filename:
                # Create safe filename
                filename = f"{application_number}_{file_key}_{file.filename}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # Map file types
                doc_type_mapping = {
                    'passportPhoto': 'passport_photo',
                    'birthCertificate': 'birth_certificate', 
                    'parentsId': 'parent_id_front'
                }
                
                doc_type = doc_type_mapping.get(file_key, file_key)
                
                # Insert document record
                cursor.execute("""
                    INSERT INTO documents (application_id, document_type, file_path)
                    VALUES (%s, %s, %s)
                """, (application_id, doc_type, file_path))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Application submitted successfully',
            'applicationNumber': application_number
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/track/<application_number>', methods=['GET'])
def track_application(application_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # First, try to find in regular applications
        cursor.execute("""
            SELECT application_number, full_names, status, created_at, updated_at
            FROM applications WHERE application_number = %s
        """, (application_number,))
        
        application = cursor.fetchone()
        
        # If not found in regular applications, check lost_id_applications using waiting card number
        if not application:
            cursor.execute("""
                SELECT l.waiting_card_number as application_number, c.full_names, 
                       l.status, l.created_at, l.updated_at
                FROM lost_id_applications l
                LEFT JOIN citizens c ON l.citizen_id_number = c.id_number
                WHERE l.waiting_card_number = %s
            """, (application_number,))
            
            application = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
            
        return jsonify({'application': application}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications', methods=['GET'])
def get_all_applications():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get regular applications
        cursor.execute("""
            SELECT a.id, a.application_number, a.full_names, a.status, 
                   a.application_type, a.created_at, a.updated_at,
                   o.full_name as officer_name, 'regular' as source_type
            FROM applications a 
            LEFT JOIN officers o ON a.officer_id = o.id
            ORDER BY a.created_at DESC
        """)
        
        regular_applications = cursor.fetchall()
        
        # Get lost ID applications (renewal applications)
        cursor.execute("""
            SELECT l.id, l.waiting_card_number as application_number, 
                   c.full_names, l.status, 'renewal' as application_type, 
                   l.created_at, l.updated_at, o.full_name as officer_name,
                   'lost_id' as source_type
            FROM lost_id_applications l
            LEFT JOIN officers o ON l.officer_id = o.id
            LEFT JOIN citizens c ON l.citizen_id_number = c.id_number
            ORDER BY l.created_at DESC
        """)
        
        lost_id_applications = cursor.fetchall()
        
        # Combine both types of applications
        all_applications = regular_applications + lost_id_applications
        
        # Sort by created_at desc
        all_applications.sort(key=lambda x: x['created_at'], reverse=True)
        
        cursor.close()
        conn.close()
        
        return jsonify({'applications': all_applications}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/<int:application_id>', methods=['GET'])
def get_application_details(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get application details
        cursor.execute("""
            SELECT a.*, o.full_name as officer_name
            FROM applications a 
            LEFT JOIN officers o ON a.officer_id = o.id
            WHERE a.id = %s
        """, (application_id,))
        
        application = cursor.fetchone()
        
        if not application:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found'}), 404
        
        # Get supporting documents
        cursor.execute("""
            SELECT document_type, file_path
            FROM documents WHERE application_id = %s
        """, (application_id,))
        
        documents = cursor.fetchall()
        application['documents'] = documents
        
        cursor.close()
        conn.close()
        
        return jsonify({'application': application}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/<int:application_id>/approve', methods=['PUT'])
def approve_application(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Generate ID number
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'approved'")
        count = cursor.fetchone()['count']
        id_number = f"ID{datetime.now().year}{count + 1:08d}"
        
        # Update application status and assign ID number
        cursor.execute("""
            UPDATE applications 
            SET status = 'approved', generated_id_number = %s, updated_at = %s
            WHERE id = %s
        """, (id_number, datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Application approved successfully',
            'id_number': id_number
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/<int:application_id>/reject', methods=['PUT'])
def reject_application(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update application status
        cursor.execute("""
            UPDATE applications 
            SET status = 'rejected', updated_at = %s
            WHERE id = %s
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Application rejected successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/approved', methods=['GET'])
def get_approved_applications():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT a.id, a.application_number, a.full_names, a.application_type, 
                   a.generated_id_number, a.created_at, a.updated_at, o.full_name as officer_name
            FROM applications a
            LEFT JOIN officers o ON a.officer_id = o.id
            WHERE a.status = 'approved'
            ORDER BY a.updated_at DESC
        """
        
        cursor.execute(query)
        applications = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'applications': applications}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/applications/<int:application_id>/dispatch', methods=['PUT'])
def dispatch_application(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update application status to dispatched
        cursor.execute("""
            UPDATE applications 
            SET status = 'dispatched', updated_at = %s
            WHERE id = %s AND status = 'approved'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or not approved'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Application dispatched successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/officer/lost-id-applications/<int:application_id>/card-arrived', methods=['PUT'])
def mark_lost_id_card_arrived(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE lost_id_applications 
            SET status = 'ready_for_collection', updated_at = %s 
            WHERE id = %s AND status = 'dispatched'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or not in dispatched status'}), 404
            
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Lost ID card arrival confirmed'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/officer/lost-id-applications/<int:application_id>/card-collected', methods=['PUT'])
def mark_lost_id_card_collected(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE lost_id_applications 
            SET status = 'collected', updated_at = %s 
            WHERE id = %s AND status = 'ready_for_collection'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or not ready for collection'}), 404
            
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Lost ID card collection confirmed'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Officer Application Management Routes
@app.route('/api/officer/applications', methods=['GET'])
def get_officer_applications():
    try:
        # In a real app, get officer_id from JWT token
        officer_id = request.args.get('officer_id', 1)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get regular applications
        cursor.execute("""
            SELECT id, application_number, full_names, status, created_at, 
                   updated_at, generated_id_number, 'regular' as application_type
            FROM applications 
            WHERE officer_id = %s 
            ORDER BY created_at DESC
        """, (officer_id,))
        
        regular_applications = []
        for row in cursor.fetchall():
            app = {
                'id': row[0],
                'application_number': row[1],
                'full_names': row[2],
                'status': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'updated_at': row[5].isoformat() if row[5] else None,
                'generated_id_number': row[6],
                'application_type': row[7],
                'source_type': 'regular'
            }
            regular_applications.append(app)
        
        # Get lost ID applications (renewal applications)
        cursor.execute("""
            SELECT lia.id, lia.waiting_card_number, c.full_names, lia.status, lia.created_at,
                   lia.updated_at, lia.citizen_id_number, 'renewal' as application_type
            FROM lost_id_applications lia
            LEFT JOIN citizens c ON lia.citizen_id_number = c.id_number
            WHERE lia.officer_id = %s
            ORDER BY lia.created_at DESC
        """, (officer_id,))
        
        lost_id_applications = []
        for row in cursor.fetchall():
            app = {
                'id': row[0],
                'application_number': row[1],  # waiting_card_number
                'full_names': row[2],
                'status': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'updated_at': row[5].isoformat() if row[5] else None,
                'generated_id_number': row[6],  # citizen_id_number
                'application_type': row[7],
                'source_type': 'lost_id'
            }
            lost_id_applications.append(app)
        
        # Combine both types of applications
        all_applications = regular_applications + lost_id_applications
        
        # Sort by created_at desc
        all_applications.sort(key=lambda x: x['created_at'] if x['created_at'] else '', reverse=True)
        
        cursor.close()
        conn.close()
        
        return jsonify(all_applications), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/officer/applications/<int:application_id>/card-arrived', methods=['PUT'])
def mark_card_arrived(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE applications 
            SET status = 'ready_for_collection', updated_at = %s 
            WHERE id = %s AND status = 'dispatched'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Application not found or not in dispatched status'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Card arrival confirmed'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/officer/applications/<int:application_id>/card-collected', methods=['PUT'])
def mark_card_collected(application_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE applications 
            SET status = 'collected', updated_at = %s 
            WHERE id = %s AND (status = 'ready_for_collection' OR (status IN ('', 'dispatched') AND generated_id_number IS NOT NULL))
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Application not found or card not arrived yet'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Card collection confirmed'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Lost ID Replacement Routes
@app.route('/api/citizen/<id_number>', methods=['GET'])
def get_citizen_details(id_number):
    """Get citizen details by ID number for lost ID replacement"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if citizen exists in approved applications
        cursor.execute("""
            SELECT generated_id_number as id_number, full_names, date_of_birth, 
                   district_of_birth as place_of_birth, gender,
                   'Kenyan' as nationality
            FROM applications 
            WHERE generated_id_number = %s AND status IN ('approved', 'dispatched', 'ready_for_collection', 'collected')
            LIMIT 1
        """, (id_number,))
        
        citizen = cursor.fetchone()
        
        if not citizen:
            # Also check in citizens table if it exists
            cursor.execute("""
                SELECT id_number, full_names, date_of_birth, place_of_birth, gender, nationality
                FROM citizens WHERE id_number = %s
            """, (id_number,))
            citizen = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not citizen:
            return jsonify({'error': 'Citizen not found'}), 404
            
        return jsonify(citizen), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lost-id-applications', methods=['POST'])
def submit_lost_id_application():
    """Submit a lost ID replacement application"""
    try:
        print(f"Received lost ID application request: {request.method}")
        print(f"Form data: {dict(request.form)}")
        print(f"Files: {list(request.files.keys())}")
        
        # Handle form data with files
        data = request.form.to_dict()
        files = request.files
        
        # Validate required fields
        required_fields = ['id_number', 'ob_number', 'ob_description', 'payment_method']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            print(f"Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Validate required files
        required_files = ['ob_photo', 'passport_photo', 'birth_certificate']
        missing_files = [file for file in required_files if file not in files or not files[file].filename]
        if missing_files:
            print(f"Missing required files: {missing_files}")
            return jsonify({'error': f'Missing required files: {", ".join(missing_files)}'}), 400
        
        # Get officer ID (in production, extract from JWT)
        officer_id = data.get('officer_id', 1)
        
        print("Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ensure citizen exists in citizens table first
        print("Checking if citizen exists in citizens table...")
        cursor.execute("SELECT id_number FROM citizens WHERE id_number = %s", (data['id_number'],))
        citizen_exists = cursor.fetchone()
        
        if not citizen_exists:
            print("Citizen not found in citizens table, searching in applications...")
            # Get citizen data from applications table
            cursor.execute("""
                SELECT generated_id_number, full_names, date_of_birth, 
                       district_of_birth, gender
                FROM applications 
                WHERE generated_id_number = %s AND status IN ('approved', 'dispatched', 'ready_for_collection', 'collected')
                LIMIT 1
            """, (data['id_number'],))
            
            citizen_data = cursor.fetchone()
            if citizen_data:
                print("Found citizen in applications table, inserting into citizens table...")
                # Insert into citizens table
                cursor.execute("""
                    INSERT INTO citizens (id_number, full_names, date_of_birth, place_of_birth, gender, nationality)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    citizen_data[0], citizen_data[1], citizen_data[2], 
                    citizen_data[3], citizen_data[4], 'Kenyan'
                ))
                print("Citizen inserted into citizens table successfully")
            else:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Citizen not found in system'}), 404
        
        # Generate waiting card number
        print("Generating waiting card number...")
        cursor.execute("SELECT COUNT(*) FROM lost_id_applications")
        count = cursor.fetchone()[0]
        waiting_card_number = f"WAIT{datetime.now().year}{count + 1:06d}"
        print(f"Generated waiting card number: {waiting_card_number}")
        
        # Insert lost ID application
        print("Inserting lost ID application...")
        cursor.execute("""
            INSERT INTO lost_id_applications (
                waiting_card_number, citizen_id_number, officer_id, 
                ob_number, ob_description, payment_method, 
                payment_amount, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            waiting_card_number, data['id_number'], officer_id,
            data['ob_number'], data['ob_description'], data['payment_method'],
            1000.00, 'submitted', datetime.now()
        ))
        
        application_id = cursor.lastrowid
        print(f"Created application with ID: {application_id}")
        
        # Handle file uploads
        upload_dir = 'uploads/lost_id'
        os.makedirs(upload_dir, exist_ok=True)
        print(f"Upload directory created: {upload_dir}")
        
        # Map file types for lost ID applications
        file_type_mapping = {
            'ob_photo': 'ob_photo',
            'passport_photo': 'new_passport_photo',
            'birth_certificate': 'birth_cert_photo'
        }
        
        for file_key, file in files.items():
            if file and file.filename and file_key in file_type_mapping:
                print(f"Processing file: {file_key} - {file.filename}")
                # Create safe filename
                secure_name = secure_filename(file.filename)
                filename = f"{waiting_card_number}_{file_key}_{secure_name}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                print(f"Saved file to: {file_path}")
                
                doc_type = file_type_mapping[file_key]
                
                # Insert document record
                cursor.execute("""
                    INSERT INTO documents (lost_id_application_id, document_type, file_path)
                    VALUES (%s, %s, %s)
                """, (application_id, doc_type, file_path))
                print(f"Inserted document record: {doc_type}")
        
        # Record payment
        print("Recording payment...")
        cursor.execute("""
            INSERT INTO payments (lost_id_application_id, amount, payment_method, status)
            VALUES (%s, %s, %s, %s)
        """, (application_id, 1000.00, data['payment_method'], 'pending'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Lost ID application submitted successfully")
        return jsonify({
            'message': 'Lost ID application submitted successfully',
            'waiting_card_number': waiting_card_number
        }), 201
        
    except Exception as e:
        print(f"Error in submit_lost_id_application: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/lost-id-applications', methods=['GET'])
def get_lost_id_applications():
    """Get all lost ID applications for admin"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT lia.id, lia.waiting_card_number, lia.citizen_id_number,
                   lia.ob_number, lia.payment_method, lia.status, lia.created_at,
                   o.full_name as officer_name,
                   c.full_names as citizen_name
            FROM lost_id_applications lia
            LEFT JOIN officers o ON lia.officer_id = o.id
            LEFT JOIN applications a ON lia.citizen_id_number = a.generated_id_number
            LEFT JOIN citizens c ON lia.citizen_id_number = c.id_number
            ORDER BY lia.created_at DESC
        """)
        
        applications = cursor.fetchall()
        
        # Get citizen names from applications table if not in citizens table
        for app in applications:
            if not app['citizen_name']:
                cursor.execute("""
                    SELECT full_names FROM applications 
                    WHERE generated_id_number = %s
                    LIMIT 1
                """, (app['citizen_id_number'],))
                result = cursor.fetchone()
                if result:
                    app['citizen_name'] = result['full_names']
        
        cursor.close()
        conn.close()
        
        return jsonify({'applications': applications}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/lost-id-applications/<int:application_id>/approve', methods=['PUT'])
def approve_lost_id_application(application_id):
    """Approve a lost ID replacement application"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update application status to approved
        cursor.execute("""
            UPDATE lost_id_applications 
            SET status = 'approved', updated_at = %s
            WHERE id = %s AND status = 'submitted'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or already processed'}), 404
        
        # Update payment status
        cursor.execute("""
            UPDATE payments 
            SET status = 'completed'
            WHERE lost_id_application_id = %s
        """, (application_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Lost ID application approved successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/lost-id-applications/<int:application_id>/reject', methods=['PUT'])
def reject_lost_id_application(application_id):
    """Reject a lost ID replacement application"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update application status to rejected
        cursor.execute("""
            UPDATE lost_id_applications 
            SET status = 'rejected', updated_at = %s
            WHERE id = %s AND status = 'submitted'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or already processed'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Lost ID application rejected'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/lost-id-applications/<int:application_id>/dispatch', methods=['PUT'])
def dispatch_lost_id_application(application_id):
    """Dispatch an approved lost ID replacement"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update application status to dispatched
        cursor.execute("""
            UPDATE lost_id_applications 
            SET status = 'dispatched', updated_at = %s
            WHERE id = %s AND status = 'approved'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or not approved'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Lost ID replacement dispatched successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/officer/lost-id-applications', methods=['GET'])
def get_officer_lost_id_applications():
    """Get lost ID applications for a specific officer"""
    try:
        # In a real app, get officer_id from JWT token
        officer_id = request.args.get('officer_id', 1)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT lia.id, lia.waiting_card_number, lia.citizen_id_number,
                   lia.ob_number, lia.payment_method, lia.status, lia.created_at,
                   a.full_names as citizen_name
            FROM lost_id_applications lia
            LEFT JOIN applications a ON lia.citizen_id_number = a.generated_id_number
            WHERE lia.officer_id = %s
            ORDER BY lia.created_at DESC
        """, (officer_id,))
        
        applications = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(applications), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/officer/lost-id-applications/<int:application_id>/card-arrived', methods=['PUT'])
def mark_lost_id_card_arrived(application_id):
    """Mark lost ID replacement card as arrived"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE lost_id_applications 
            SET status = 'ready_for_collection', updated_at = %s 
            WHERE id = %s AND status = 'dispatched'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or not in dispatched status'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Lost ID replacement card arrival confirmed'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/officer/lost-id-applications/<int:application_id>/card-collected', methods=['PUT'])
def mark_lost_id_card_collected(application_id):
    """Mark lost ID replacement card as collected"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE lost_id_applications 
            SET status = 'collected', updated_at = %s 
            WHERE id = %s AND status = 'ready_for_collection'
        """, (datetime.now(), application_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Application not found or card not ready for collection'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Lost ID replacement card collection confirmed'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/track-lost/<waiting_card_number>', methods=['GET'])
def track_lost_id_application(waiting_card_number):
    """Track lost ID application by waiting card number"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT lia.waiting_card_number, lia.citizen_id_number, lia.status, 
                   lia.created_at, lia.updated_at,
                   a.full_names as citizen_name
            FROM lost_id_applications lia
            LEFT JOIN applications a ON lia.citizen_id_number = a.generated_id_number
            WHERE lia.waiting_card_number = %s
        """, (waiting_card_number,))
        
        application = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
            
        return jsonify({'application': application}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)