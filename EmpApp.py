from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

application = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@application.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@application.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')

@application.route("/getemp", methods=['GET'])
def GetEmp():
    return render_template('GetEmp.html')

@application.route("/fetchdata", methods=['POST'])
def GetEmpOne():
    employee_id = request.form['emp_id']
    read_sql = "SELECT * FROM `employee` WHERE emp_id=%s"
    cursor = db_conn.cursor()

    try:

        cursor.execute(read_sql, (employee_id))        
        result = cursor.fetchone()

        emp_id,first_name,last_name,pri_skill,location = result        

        # Load image file from S3 #        
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"        
        
        try:                       
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)
        
    except Exception as e:        
        return render_template('GetEmp.html',err=e,id=employee_id)        
    finally:
        cursor.close()

    print("all modification done...")    
    return render_template('GetEmpOutput.html',id=emp_id,fname=first_name,lname=last_name,priskill=pri_skill,location=location,image_url=object_url)

@application.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)
    except Exception as err:        
        return render_template('AddEmp.html', err=err.args, cache={
            "emp_id":emp_id,
            "first_name":first_name,
            "last_name":last_name,
            "pri_skill":pri_skill,
            "location":location,
            "emp_image_file":emp_image_file
        })
    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=80, debug=True)
