import uuid
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponseRedirect
import json
import logging
from django.db import transaction
from Labtoolz import settings
from Labtoolz_app.easydb_utils import execute_sql, fetch_database_data, get_tool_name_id_dict_by_table_name
from foraging_task import Config
from foraging_task.data_manager import update_tool_timestamp
from .models import Task_clicks, Subjects, Task_patches
import pdb
from .forms import Oci_questionnaire_form, Dass_questionnaire_form, Aaq_questionnaire_form
from foraging_task.Config import Config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib

logger = logging.getLogger(__name__)

def is_user_exists(subject_id, table_id):
    try:
        fetch_database_data(f"SELECT subject_id FROM {Config.user_name}_{table_id} WHERE subject_id = '{subject_id}'")[0][0]        
    except IndexError:
        return False
    return True

def welcome_screen(request):
    return render(request, 'welcome_screen.html')

def foraging_task_preview(request):
    return render(request, 'foraging_task_preview.html')

def finish_screen(request):
    return render(request, 'finish_screen.html')

def foraging_task(request):
    return render(request, 'foraging_task.html')

def oci_questionnaire(request):
    form = Oci_questionnaire_form(request.POST) 

    if request.method == 'POST':             
            error_message = "Couldn't insert values to OCI for user " + form['subject_id'].value()

            if form.is_valid():
                try:
                    if not is_user_exists(form['subject_id'].value(), "tool_3"):
                        form.save()                     
                        # Update tables
                        sql = f"UPDATE `{Config.user_name}_tool_1` SET oci_completed = '1' WHERE subject_id = '{form['subject_id'].value()}';" 
                        logger.info("Updating subject data")
                        execute_sql(sql)
                        update_tool_timestamp(Config.user_name, '3') #TODO find way to access Meta      
                except Exception as e:
                    logger.error(error_message)
                    print(e)
                                                           
                return HttpResponseRedirect('/foraging_task/dass_questionnaire')
            else:
                logger.error(error_message +  "Errors:")
                for k in form.errors.keys():
                    logger.error(form.errors[k])                
    else:
        form = Oci_questionnaire_form()

    return render(request, 'questionnaire_form.html', {'form': form,
                                                       'form_name' : 'oci'})

def dass_questionnaire(request):
    form = Dass_questionnaire_form(request.POST)          
      
    if request.method == 'POST':             
            error_message = "Couldn't insert values to DASS for user " + form['subject_id'].value()
            if form.is_valid():
                try:
                    if not is_user_exists(form['subject_id'].value(), "tool_4"):
                        form.save()                     
                        # Update tables
                        sql = f"UPDATE `{Config.user_name}_tool_1` SET dass_completed = '1' WHERE subject_id = '{form['subject_id'].value()}';" 
                        logger.info("Updating subject data")
                        execute_sql(sql)    
                        update_tool_timestamp(Config.user_name, '4')          
                except Exception as e:
                    logger.error(error_message)
                    print(e)  
                                    
                return HttpResponseRedirect('/foraging_task/aaq_questionnaire')
            else:
                logger.error(error_message +  "Errors:")
                for k in form.errors.keys():
                    logger.error(form.errors[k])
    else:
        form = Dass_questionnaire_form()

    return render(request, 'questionnaire_form.html', {'form': form,
                                                       'form_name' : 'dass'})

def aaq_questionnaire(request):
    form = Aaq_questionnaire_form(request.POST)        
    
    if request.method == 'POST':             
            error_message = "Couldn't insert values to AAQ for user " + form['subject_id'].value()            
            if form.is_valid():
                try:
                    if not is_user_exists(form['subject_id'].value(), "tool_5"):
                        form.save()                     
                        # Update tables
                        sql = f"UPDATE `{Config.user_name}_tool_1` SET aaq_completed = '1' WHERE subject_id = '{form['subject_id'].value()}';" 
                        logger.info("Updating subject data")
                        execute_sql(sql)                      
                        update_tool_timestamp(Config.user_name, '5')       
                except Exception as e:
                    logger.error("error_message")
                    print(e)
                                
                return HttpResponseRedirect('https://app.prolific.co/submissions/complete?cc=C1MZ7WQJ')
            else:
                logger.error(error_message +  "Errors:")
                for k in form.errors.keys():
                    logger.error(form.errors[k])
    else:
        form = Aaq_questionnaire_form()

    return render(request, 'questionnaire_form.html', {'form': form,
                                                       'form_name' : 'aaq'})

@csrf_exempt
@transaction.atomic
def report_task_data(request):  
    logger.info("*** Request raw data: ")
    logger.info(request.body)
    
    file_path = "raw_data.txt"
    text_file = open(file_path, "w")
    text_file.write(str(request.body))
    text_file.close()
        
    try:          
        data = json.loads(request.body)                
    except json.JSONDecodeError as e:
        logger.error("Didn't manage to parse data Json, trying to replace")        
        logger.error(e)        
        try:
            data = json.loads(request.body.replace("\\", ""))
        except json.JSONDecodeError as e1:
            logger.error(f"Didn't manage to parse data Json, also after replacing. Data: {str(request.body)}; Error: {str(e1)}")                    
            sendMail(request.body, e1, file_path)
        except Exception as e2:            
            logger.error(f"Didn't manage to parse data Json, also after replacing. Data: {str(request.body)}; Error: {str(e2)}")
            sendMail(request.body, e2, file_path)
    except Exception as e3:
        logger.error(f"Didn't manage to parse data Json. Data: {str(request.body)}; Error: {str(e3)}")
        sendMail(request.body, e3, file_path)
        
    subject_id = ""
    try:
        subject_id = data["subject_id"]
    except KeyError:    
        subject_id = data["subject_data"]["subject_id"]
    
    logger.info("Got data for subject " + str(subject_id) + "; data: " + str(data))
    
    report_subject_data = False
    report_click_data = False
    report_patch_data = False
    data_for_insertion = None
    
    try:
        data_for_insertion = data["subject_data"]
        report_subject_data = True
    except KeyError:
        pass
    
    try:
        data_for_insertion = data["click_data"]
        report_click_data = True
    except KeyError:
        pass
    
    try:
        data_for_insertion = data["patch_data"]
        report_patch_data = True
    except KeyError:
        pass
    
    if report_subject_data:
        subject_id = ""
        try:        
            data_for_insertion = data["subject_data"]
            fields_string = ",".join(["`" + str(field) + "`" for field in data_for_insertion.keys()])
            values_string = ",".join(["'" + str(value) + "'" for value in data_for_insertion.values()])
            
            # Check if the user already exists
            try:
                subject_id = fetch_database_data(f"SELECT subject_id FROM {Config.user_name}_tool_1 WHERE subject_id = '{data_for_insertion['subject_id']}'")[0][0]
            except IndexError:
                pass        
            
            if subject_id == "":  
                subject_id = data_for_insertion['subject_id']                                                  
                sql = f"INSERT INTO `{Config.user_name}_tool_1`({fields_string}) VALUES({values_string});" 
                logger.info("Inserting task subjects: " + sql)
                execute_sql(sql)
                
                # add data to tb_subjects    
                sql = f"INSERT INTO `{Config.user_name}_tb_subjects`(`subject_uuid`,`subject_local_id`,`experiment_id`,`user_identifier`) VALUES('{data_for_insertion['subject_uuid']}','{data_for_insertion['subject_id']}','{'1'}','{'NA'}');" 
                logger.info("Inserting data to tb_subjects: " + sql)
                execute_sql(sql)
            else:
                for key in data_for_insertion.keys():
                    sql = f"UPDATE `{Config.user_name}_tool_1` SET {key} = '{data_for_insertion[key]}' WHERE subject_id = '{subject_id}';" 
                    logger.info("updating task subjects: " + sql)
                    execute_sql(sql)
            
            update_tool_timestamp(Config.user_name, '1') 
            logger.info("Updated subject data for subject id " + subject_id)               
        except Exception as e:
            logger.error("Didn't manage to insert subject data for subject " + str(data["subject_data"]["subject_id"]))
            print(e)
    
    if report_click_data:
        try:    
            data_for_insertion = data["click_data"]
                                    
            clicks = []
            for click in data_for_insertion:
                tc = Task_clicks(subject_id=click["subjectId"],
                                subject_uuid=click["subjectUuid"], 
                                click_time=click["clickTime"],
                                is_ripe=click["isRipe"],
                                x=click["x"],
                                y=click["y"],
                                is_green=click["isGreen"],
                                color=click["color"],
                                patch_number=click["patchNumber"])
                clicks.append(tc)
                
            Task_clicks.objects.bulk_create(clicks)   
                
            update_tool_timestamp(Config.user_name, '2')
            logger.info("Updated clicks data for subject id " + str(subject_id))               
        except Exception as e:
            logger.error("Didn't manage to insert clicks data for subject " + str(subject_id))
            print(e)
    
    if report_patch_data:
        try:    
            data_for_insertion = data["patch_data"]
            
            patches = []
            for patch in data_for_insertion:
                tp = Task_patches(subject_id=patch["subjectId"],
                                subject_uuid=patch["subjectUuid"], 
                                patch_start_time=patch["patchStartTime"],                        
                                patch_end_time=patch["patchEndTime"],                        
                                patch_length=patch["patchLength"],                        
                                patch_number=patch["patchNumber"])
                patches.append(tp)
                
            Task_patches.objects.bulk_create(patches)    
                
            update_tool_timestamp(Config.user_name, '6')
            logger.info("Updated patchs data for subject id " + str(subject_id))               
        except Exception as e:
            logger.error("Didn't manage to insert patch data for " + str(subject_id))   
            print(e)                     
    
    return JsonResponse({})

@csrf_exempt
def sendMail(data, exception, file_path):    
    if data:        
        # msg = MIMEText(f"Data = {data} \n Exception={exception}")
        msg = MIMEMultipart()
        msg['Subject'] = "Foraging task - subject failed"
        msg['From']    = f"labtoolz@{settings.MAILGUN_DOMAIN}"
        msg['To']      = "meshed72@gmail.com"
        
        body = f"Raw data attached. Got this exception: \n {exception}"
        msg.attach(MIMEText(body, "plain"))
        
        with open(file_path, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email    
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {file_path}",
        )

        # Add attachment to message and convert message to string
        msg.attach(part)
        
        s = smtplib.SMTP('smtp.mailgun.org', 587)

        s.login(f'postmaster@{settings.MAILGUN_DOMAIN}', settings.MAILGUN_SMTP_PASSWORD)
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()
            
        logger.info(f"Sent failure mail")
    
    return JsonResponse({'': ''})
    