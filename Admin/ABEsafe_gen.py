import os
import shutil
import sqlite3

import threading
import Queue

from ctypes.util import find_library
from ctypes import *


class ABEsafe_generator:
	SHARED_FOLDER_PATH = ""
	ABEsafe_PATH = SHARED_FOLDER_PATH+"ABEsafe/"
	KEYS_PATH = ".keys/"+SHARED_FOLDER_PATH+"/"
	CONFIG_PATH = ABEsafe_PATH+".configs/"
	IMG_PATH = ABEsafe_PATH+"userImages/"
	KEYGEN_PATH = ""
	DATABASE_file = "test.db"
	DATABASE = CONFIG_PATH+DATABASE_file
	PRIV_NAME = ""
	libc = CDLL(find_library('libabe.so'))
	@staticmethod
	def generateKey(staffId,username,department,position,seclv):
	    try:
	        staff_id = int(staffId)
	        if staff_id <= 0:
	            raise Exception("Non-positive staff id")
	    except Exception as e:
	        staff_id = None
	    try:
	        sec_lv = int(seclv)
	        if sec_lv <= 0:
	            raise Exception("Non-positive security level")
	    except Exception as e:
	        sec_lv = None
	    if username is None:
	        return False
	    staffId_prop = "" if staff_id is None else "staffId = %d"%staff_id
	    privkey_filename = username+"_"+str(staff_id)
	    username = "name_%s"%username
	    department = "department_%s"%str(department)
	    position = "position_%s"%str(position)
	    sec_prop = "" if sec_lv is None else "seclv = %d"%sec_lv
	    ABEsafe_generator.PRIV_NAME = "%s%s_priv_key"%(ABEsafe_generator.KEYS_PATH,privkey_filename)
	    s = "%s"%("" if staffId_prop=="" else "'%s'"%staffId_prop)+" '"+username+"' '"+department+"' '"+position+"' "+"%s"%("" if sec_prop=="" else "'%s'"%sec_prop)
	    status = ABEsafe_generator.libc.abe_generatekey(str("%s%s_priv_key"%(ABEsafe_generator.KEYS_PATH,privkey_filename)), str(ABEsafe_generator.CONFIG_PATH+".pub_key"), str(ABEsafe_generator.CONFIG_PATH+".master_key"), str(s))
	    with open('%s.%s'%(ABEsafe_generator.CONFIG_PATH,privkey_filename),'w+') as f:
	    	f.write("OK")
	    
	    ABEsafe_generator.libc.abe_encrypt(str("%s.%s_test"%(ABEsafe_generator.CONFIG_PATH,privkey_filename)), str(ABEsafe_generator.CONFIG_PATH+".pub_key"), str("%s.%s"%(ABEsafe_generator.CONFIG_PATH,privkey_filename)), str("%s"%(staffId_prop+" & "+username+" & "+department+" & "+position+"%s"%("" if sec_prop=="" else " & %s"%sec_prop))))
	    return status==0	     

	@staticmethod
	def ABEsafe_gensystem(log,shared_dir,needSample=True):
		ABEsafe_generator.SHARED_FOLDER_PATH = shared_dir
		ABEsafe_generator.ABEsafe_PATH = ABEsafe_generator.SHARED_FOLDER_PATH+"ABEsafe/"
		ABEsafe_generator.KEYS_PATH = ".keys/"+ABEsafe_generator.SHARED_FOLDER_PATH+"/"
		ABEsafe_generator.CONFIG_PATH = ABEsafe_generator.ABEsafe_PATH+".configs/"
		ABEsafe_generator.DATABASE = ABEsafe_generator.CONFIG_PATH+"test.db"
		try:
			if os.path.exists(ABEsafe_generator.ABEsafe_PATH):
				shutil.rmtree(ABEsafe_generator.ABEsafe_PATH)
		except Exception as e:
			log.error(e)
		if not os.path.exists(ABEsafe_generator.ABEsafe_PATH):
			os.makedirs(ABEsafe_generator.ABEsafe_PATH)
			os.chmod(ABEsafe_generator.ABEsafe_PATH,0o777)
		if not os.path.exists(ABEsafe_generator.KEYS_PATH):
			os.makedirs(ABEsafe_generator.KEYS_PATH)
			os.chmod(ABEsafe_generator.KEYS_PATH,0o744)
		if not os.path.exists(ABEsafe_generator.CONFIG_PATH):
			os.makedirs(ABEsafe_generator.CONFIG_PATH)
			os.chmod(ABEsafe_generator.CONFIG_PATH,0o755)
		if not os.path.exists(ABEsafe_generator.IMG_PATH):
			os.makedirs(ABEsafe_generator.IMG_PATH)
			os.chmod(ABEsafe_generator.IMG_PATH,0o766)

		pub_key_path = ABEsafe_generator.CONFIG_PATH+".pub_key"
		status = ABEsafe_generator.libc.abe_setup(str(".master_key"), str(pub_key_path))
		if status==0:
			log.info("Master Key generated successfully")
		else:
			log.warning("Failed to generate master key, %s"%status)
		"""encrypt master_key"""
		shutil.move(".master_key","%s.master_key"%ABEsafe_generator.CONFIG_PATH)

		departments = (
			(None,'HumanResources'),
			(None,'IT'),
			(None,'Accounting')
			)
		positions = (
			(None,'admin'),
			(None,'advisor'),
			(None,'director'),
			(None,'staff')
			)
		users = (
			(None,1,'alice','Accounting','advisor',3),
			(None,2,'bob','HumanResources','staff',3),
			(None,3,'charlie','Accounting','director',1),
			(None,4,'david','HumanResources','director',1),
			(None,5,'eve','IT','admin',2),
			(None,6,'frank','Accounting','director',3),
			(None,7,'gibson','HumanResources','director',1),
			(None,8,'henry','HumanResources','advisor',3),
			(None,9,'ivan','HumanResources','advisor',3),
			(None,10,'john','Accounting','advisor',3),
			(None,11,'kevin','HumanResources','staff',4),
			(None,12,'larry','Accounting','advisor',3),
			(None,13,'mallet','Accounting','staff',2),
			(None,14,'nick','Accounting','admin',2),
			(None,15,'oscar','Accounting','staff',3),
			(None,16,'peter','Accounting','advisor',3)
			)
		department = None
		position = None
		try:
			connection = sqlite3.connect(ABEsafe_generator.DATABASE)
			with connection:
				cursor = connection.cursor()
				try:
					cursor.execute("DROP TABLE department")
				except:
					pass
				cursor.execute("CREATE TABLE IF NOT EXISTS department(Department_Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, DepartmentName VARCHAR(40))")
				if needSample:
					cursor.executemany("INSERT INTO department VALUES(?, ?)",departments)
				try:
					cursor.execute("DROP TABLE position")
				except:
					pass
				cursor.execute("CREATE TABLE IF NOT EXISTS position(Position_Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, PositionName VARCHAR(40))")
				if needSample:
					cursor.executemany("INSERT INTO position VALUES(?,?)",positions)
				try:
					cursor.execute("DROP TABLE Users")
				except:
					pass
				cursor.execute("SELECT * FROM department")
				department = cursor.fetchall()
				cursor.execute("SELECT * FROM position")
				position = cursor.fetchall()
				mapped_users = []
				cursor.execute("CREATE TABLE IF NOT EXISTS Users(Id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, Staff_Id INTEGER UNIQUE, Name VARCHAR(40) NOT NULL, Department INTEGER, Position INTEGER, SecurityLevel INT, FOREIGN KEY(Department) REFERENCES department(Department_Id), FOREIGN KEY(Position) REFERENCES position(Position_Id))")
				if needSample:
					
					genKeyQueue = Queue.Queue()
					def genf(s_id,name,d_id,pos_id,sec):
						if not ABEsafe_generator.generateKey(s_id,name,d_id,pos_id,sec):
							log.warning("Cannot generate key for "+str((a_id,a_staff_id,a_name,a_department,a_position,sec)))
						genKeyQueue.task_done()
					
					for (a_id,a_staff_id,a_name,a_department,a_position,sec) in users:
						try:
							cursor.execute('SELECT Department_Id FROM department WHERE DepartmentName="%s"'%a_department)
							data = cursor.fetchall()
							if data:
								depart_id = data[0][0]
							else:
								log.info("Invalid department name, "+str((a_id,a_staff_id,a_name,a_department,a_position,sec))+" is not added")
								continue
						except Exception, e:
							log.error(e)
						try:
							cursor.execute('SELECT Position_Id FROM position WHERE PositionName="%s"'%a_position)
						except Exception, e:
							log.error(e)
						data = cursor.fetchall()
						if data:
							pos_id = data[0][0]
						else:
							log.warning("Invalid position name, "+str((a_id,a_staff_id,a_name,a_department,a_position,sec))+" is not added")
							continue
						try:
							cursor.execute("INSERT INTO Users VALUES(NULL,%d,'%s','%s','%s',%d)"%(a_staff_id,a_name,depart_id,pos_id,sec))
							t1=threading.Thread(target=genf,args=(a_staff_id,a_name,depart_id,pos_id,sec))
							genKeyQueue.put(t1)
							t1.start()
							shutil.copyfile("userImages/"+a_name+"_"+str(a_staff_id)+".jpg",ABEsafe_generator.IMG_PATH+a_name+"_"+str(a_staff_id)+".jpg")
						except Exception, e:
							log.error(e)
					genKeyQueue.join() 
				cursor.execute("SELECT * FROM department")
				department = cursor.fetchall()
				cursor.execute("SELECT * FROM position")
				position = cursor.fetchall()
				cursor.execute("SELECT * FROM Users")
				rows = cursor.fetchall()
		except sqlite3.Error, e:
			if connection:
				connection.rollback()
			log.error("ABEsafe System Creation Error: %s"%e.args[0])
		finally:
			if connection:
				connection.close()